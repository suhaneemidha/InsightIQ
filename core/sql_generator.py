from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

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
  "reasoning": "brief explanation"
}

Do not surround the JSON with markdown code blocks.
Do not write any extra explanation before or after the JSON.
"""


def generate_sql(nl_query: str, schema_context: list[str]) -> dict:

    schema_text = "\n\n".join(schema_context)

    prompt = f"""
{SYSTEM_PROMPT}

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
'''if __name__ == "__main__":

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

    print(json.dumps(result, indent=4))'''
    

import duckdb

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
            model="llama3-70b-8192",
            messages=[
                {"role": "user", "content": fix_prompt}
            ]
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("{"):
            result = json.loads(raw)

    result["attempts"] = max_retries + 1
    return result