from core.retriever import build_retriever, retrieve_schema
from core.sql_generator import generate_sql_with_retry
from core.query_engine import execute_sql
from core.insight_generator import generate_insights


retriever = build_retriever()

print("Retriever initialized successfully")

def run_pipeline(question: str) -> dict:
    print("Question received:", question)
    # retrieve schema context
    schema_context = retrieve_schema(
        question,
        retriever
    )

    # generate SQL
    sql_result = generate_sql_with_retry(
        question,
        schema_context
    )

    sql = sql_result["sql"]

    # execute SQL
    execution_result = execute_sql(sql)

    # generate insights if query succeeded
    insights = []

    if execution_result["success"]:
        insights = generate_insights(
            execution_result["data"],
            question
        )

    return {
        "question": question,
        "schema_context": schema_context,
        "sql_result": sql_result,
        "execution_result": execution_result,
        "insights": insights
    }

if __name__ == "__main__":
    result = run_pipeline(
        "Top 5 sellers by revenue"
    )

    print(result)   