import os
import json
import duckdb
import numpy as np

from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

SYSTEM_PROMPT = """
You are an expert SQL analyst.

You will be given:
1. A database schema (table names, columns, descriptions)
2. A natural language question

Your job is to write a DuckDB-compatible SQL query that answers the question.

IMPORTANT RULES:
- Use ONLY tables and columns present in the schema context.
- Do NOT invent table names.
- SQL must be compatible with DuckDB.
- If multiple tables are needed, use appropriate JOINs.
- Keep reasoning brief.

Respond ONLY in valid JSON.

Format:
{
  "sql": "<your SQL here>",
  "tables_used": ["table1", "table2"],
  "reasoning": "brief explanation",
  "llm_confidence": 85
}

llm_confidence is a number from 0 to 100 representing how confident you are
that your SQL correctly answers the question given the schema provided.
100 = completely certain. 0 = completely guessing.

Do not surround the JSON with markdown code blocks.
Do not write any extra explanation before or after the JSON.

ONLY use tables explicitly listed in schema context.

Never invent tables.

INVALID examples:
sales
deliveries
revenue_table
transactions

VALID examples:
orders
customers
products
order_items
payments
reviews
sellers

If a required table is not present,
do not create one.
"""

def load_few_shot_examples(path="data/golden_queries.json"):
    with open(path) as f:
        examples = json.load(f)  # list of {"nl_query": "...", "sql": "..."}
    return examples

def get_top_k_examples(query: str, examples: list, k: int = 3) -> list:
    query_emb = embedder.encode(query)
    example_embs = embedder.encode([e["nl_query"] for e in examples])
        
    # Cosine similarity
    sims = np.dot(example_embs, query_emb) / (
        np.linalg.norm(example_embs, axis=1) * np.linalg.norm(query_emb)
    )
    top_indices = np.argsort(sims)[::-1][:k]
    return [examples[i] for i in top_indices]

def format_few_shot(examples: list) -> str:
    shots = []
    for ex in examples:
        shots.append(f"Question: {ex['nl_query']}\nSQL: {ex['sql']}")
    return "\n\n".join(shots)


def generate_sql(nl_query: str, schema_context: list[str]) -> dict:

    schema_text = "\n\n".join(schema_context)

    examples = load_few_shot_examples()

    top_examples = get_top_k_examples(
        nl_query,
        examples,
        k=3
    )
    
    few_shot_text = format_few_shot(top_examples)

    prompt = f"""
    {SYSTEM_PROMPT}

    ### Similar Examples:
    {few_shot_text}
    
    ### Schema Context:
    {schema_text}
   
    ### Question:
    {nl_query}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    raw = response.choices[0].message.content.strip()

    # Remove markdown code fences if present
    if raw.startswith("```"):

        raw = raw.replace("```json", "")
        raw = raw.replace("```", "")
        raw = raw.strip()

    return json.loads(raw)

# Optional test
if __name__ == "__main__":

    schema_context = [
        """
        Table: customers
        Columns:
        customer_id INTEGER
        customer_name VARCHAR
        city VARCHAR
        """,

        """
        Table: orders
        Columns:
        order_id INTEGER
        customer_id INTEGER
        amount DOUBLE
        order_date DATE
        """
    ]

    query = "Show total amount spent by each customer."

    result = generate_sql(query, schema_context)

    print(json.dumps(result, indent=4))
    

def validate_sql(sql: str):
    try:
        conn = duckdb.connect("olist.db", read_only=True)
        conn.execute(f"EXPLAIN {sql}")
        return True, ""
    except Exception as e:
        return False, str(e)


def generate_sql_with_retry(nl_query, schema_context, max_retries=2):
    result = generate_sql(nl_query, schema_context)

    for i in range(max_retries):
        ok, error = validate_sql(result["sql"])

        if ok:
            result["attempts"] = i + 1
            return result

        fix_prompt = f"""
            Fix this SQL query.

            Schema:
            {chr(10).join(schema_context)}

            Question:
            {nl_query}

            Faulty SQL:
            {result['sql']}

            Error:
            {error}

            Return ONLY JSON:
            {{
            "sql": "...",
            "reasoning": "..."
            }}
            """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": fix_prompt}
            ]
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("{"):
            result = json.loads(raw)

    result["attempts"] = max_retries + 1
    return result