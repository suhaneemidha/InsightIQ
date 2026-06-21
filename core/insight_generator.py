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
You are a data analyst.

Based on the query result below, generate 3-5 concise business insights.

Rules:
- Every number mentioned MUST exist in the data.
- Do NOT invent values.
- Do NOT round numbers.
- Return ONLY bullet points.
- Each bullet must start with "•"

Question:
{question}

Data:
{data_preview}
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

    raw_text = response.choices[0].message.content

    insights = [
        line.strip()
        for line in raw_text.split("\n")
        if line.strip().startswith("•")
    ]

    # -------- Grounding Validation --------

    valid_insights = []

    all_values = set()

    for col in df.columns:
        for val in df[col].dropna():
            all_values.add(str(val))
            try:
                all_values.add(str(round(float(val), 2)))
            except:
                pass

    for insight in insights:
        numbers = re.findall(r"\d+\.?\d*", insight)

        valid = True

        for num in numbers:
            if num not in all_values:
                valid = False
                break

        if valid:
            valid_insights.append(insight)
        else:
            print(f"[Grounding failed] {insight}")

    return valid_insights if valid_insights else insights

def generate_followup_questions(
    question: str,
    df_preview: str
) -> list[str]:
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