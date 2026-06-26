from groq import Groq
from dotenv import load_dotenv
import os
import re
import pandas as pd
import json

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_insights(df: pd.DataFrame, question: str) -> list[str]:
    # Preview only first few rows
    data_preview = df.head(10).to_string(index=False)

    prompt = f"""
        Question:
        {question}

        Query Result:
        {data_preview}
        Return ONLY valid JSON.

        Format:
        [
        {{
            "insight": "Some insight",
            "evidence": ["123", "456"]
        }}
        ]

        Rules:
        - evidence must contain the exact values from the table that support the insight.
        - Do not invent evidence.
        - Return 3-5 insights.
        - Generate BUSINESS insights only.
        - Do NOT describe dataframe structure.
        - Do NOT mention rows, columns, tables, dataframes, datasets, records.
        - Do NOT explain what fields exist.
        - Focus on trends, rankings, comparisons, distributions, totals and anomalies.
        - Each insight must be unique.
        - Do not restate the same finding in different words.
        - If only one row is returned, generate at most 2 insights.
        If the result contains only 1 row:
        - Summarize the row.
        - Do not generate comparisons.
        
        """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # or your preferred Groq model
        messages=[
            {
                "role": "system",
                "content": "You are an expert data analyst."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    raw_text = response.choices[0].message.content.strip()

    if raw_text.startswith("```"):
        raw_text = (
            raw_text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )
    try:
        insights = json.loads(raw_text)
    except Exception as e:
        print(f"[Insight Parse Error] {e}")
        print("Raw response:", repr(raw_text))
        return []
    
    # -------- Grounding Validation --------

    valid_insights = []

    all_values = set()

    for col in df.columns:
        for val in df[col].dropna():
            all_values.add(str(val))

            try:
                all_values.add(str(float(val)))
                all_values.add(f"{float(val):.2f}")
            except:
                pass

    for item in insights:

        evidence = item.get("evidence", [])

        grounded = all(
            str(ev) in all_values
            for ev in evidence
        )

        if grounded:
            valid_insights.append(
                item["insight"]
            )
        else:
            print(
                f"[Grounding failed] {item['insight']}"
            )
    return valid_insights
    
def generate_followup_questions(question: str,df_preview: str,conversation_history:str) -> list[str]:
    """
    Given the user's question and the data returned,
    generates 2 follow-up questions they might want to ask next.
    
    Returns a list of exactly 2 strings.
    """
    prompt = f"""You are a data analyst assistant.

The user just asked: "{question}"

The data returned looks like:
{df_preview}

Suggest exactly 2 short follow-up questions the user might want to ask next.
These should be natural and directly related to the data shown.

Return ONLY a JSON array of 2 strings. No explanation. No markdown.
Example format: ["Question 1?", "Question 2?"]"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()

        questions = json.loads(raw)

        # Make sure we got exactly a list of strings
        if isinstance(questions, list) and len(questions) >= 2:
            return [str(q) for q in questions[:2]]
        else:
            return []

    except Exception as e:
        print(f"[Follow-up] Failed to generate: {e}")
        return []