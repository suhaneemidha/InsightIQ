import os
import json
import numpy as np

from core.query_history import get_few_shot_pool
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from groq import Groq
from dotenv import load_dotenv
from core.data_store import get_connection


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
embedder = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

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

DuckDB Rules:
- DuckDB DATEDIFF always requires 3 arguments.

IMPORTANT DATE RULES:
The Olist dataset stores date columns as VARCHAR in DD-MM-YYYY HH:MM format.
Do NOT use CAST(column AS TIMESTAMP).
Always convert dates using:
STRPTIME(column, '%d-%m-%Y %H:%M')

before using:
- DATEDIFF
- DATE_TRUNC
- EXTRACT
- any date arithmetic

Examples:

Wrong:
DATEDIFF(
CAST(order_delivered_customer_date AS TIMESTAMP),
CAST(order_estimated_delivery_date AS TIMESTAMP)
)

Correct:
DATEDIFF(
'day',
STRPTIME(
order_estimated_delivery_date,
'%d-%m-%Y %H:%M'
),
STRPTIME(
order_delivered_customer_date,
'%d-%m-%Y %H:%M'
)
)

Respond ONLY in valid JSON.

Format:
{
  "sql": "<your SQL here>",
  "tables_used": ["table1", "table2"],
  "reasoning": "brief explanation",
  "llm_confidence": 70
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

IMPORTANT OLIST RELATIONSHIPS:
orders.customer_id = customers.customer_id
customers.customer_zip_code_prefix = geolocation.geolocation_zip_code_prefix
orders.order_id = order_items.order_id
order_items.product_id = products.product_id
order_items.seller_id = sellers.seller_id
reviews.order_id = orders.order_id
Never use CAST(customer_id AS INTEGER).
Never use SUBSTR(customer_id).

IMPORTANT:
customer_id is a UUID string.
customer_zip_code_prefix is a BIGINT zip code.
Never CAST customer_id to INTEGER.
Never use SUBSTR(customer_id).
Never join orders directly to geolocation.


If a required table is not present,
do not create one.
"""

def load_few_shot_examples(path="data/golden_queries.json"):
    with open(path) as f:
        examples = json.load(f)  # list of {"nl_query": "...", "sql": "..."}
    return examples

def get_top_k_examples(query: str, examples: list, k: int = 3) -> list:
    query_emb = embedder.get_query_embedding(query)
    if not examples:
        return []
    example_embs = [embedder.get_query_embedding(e["nl_query"]) for e in examples]

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

    golden_examples = load_few_shot_examples()
    history_examples = get_few_shot_pool(limit=50)
    examples = golden_examples + history_examples

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

    try:
        result= json.loads(raw)

    except Exception as e:

        print(
            f"[SQL Generator] Failed to parse JSON: {e}"
        )

        result= {
            "sql": "",
            "tables_used": [],
            "reasoning": "JSON parse failed",
            "llm_confidence": 0
        }
    return result
    
    
def validate_sql(sql: str):
    conn = None
    try:
        conn = get_connection(read_only=True)
        conn.execute(f"EXPLAIN {sql}")
        return True, ""
    except Exception as e:
        return False, str(e)
    finally:
        if conn:
            conn.close()


def generate_sql_with_retry(nl_query, schema_context, max_retries=2):
    result = generate_sql(nl_query, schema_context)

    for i in range(max_retries):
        sql = result.get("sql", "")

        if not sql:
            result["attempts"] = i + 1
            return result
        else:
            ok, error = validate_sql(sql)

            if ok:
                result["attempts"] = i + 1
                return result

        
        fix_prompt = f"""
            {SYSTEM_PROMPT}

            Fix this SQL query.

            Question:
            {nl_query}

            Schema:
            {chr(10).join(schema_context)}

            Faulty SQL:
            {result['sql']}

            DuckDB Error:
            {error}

            Correct the SQL.

            Return ONLY JSON:

            {{
            "sql": "...",
            "tables_used": [],
            "reasoning": "...",
            "llm_confidence":70
            }}
            """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": fix_prompt}
            ]
        )
        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.replace("```json", "")
            raw = raw.replace("```", "")
            raw = raw.strip()

        try:
            result= json.loads(raw)

        except Exception as e:

            print(
                f"[SQL Generator] Failed to parse JSON: {e}"
            )

            result= {
                "sql": "",
                "tables_used": [],
                "reasoning": "JSON parse failed",
                "llm_confidence": 0
            }
    

    result["attempts"] = max_retries + 1
    return result