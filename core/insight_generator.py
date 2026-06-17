from groq import Groq
from dotenv import load_dotenv
import os
import re
import pandas as pd

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