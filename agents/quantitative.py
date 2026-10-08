import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from validation.validator import validate_sql

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_PATH = BASE_DIR / "data" / "database.sqlite"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

SCHEMA_CONTEXT = """
Available SQLite tables:

sales(id, region, product, revenue, date, units_sold)
customers(id, name, industry, churn_date, satisfaction_score)
employees(id, department, satisfaction_score, tenure_years)
""".strip()


def token_counts(response) -> tuple[int, int]:
    usage = response.usage
    if not usage:
        return 0, 0
    return usage.prompt_tokens, usage.completion_tokens


def clean_sql(sql: str) -> str:
    """Extract the first complete SELECT statement from model output."""
    match = re.search(r"\bSELECT\b", sql, flags=re.IGNORECASE)
    if not match:
        return ""

    cleaned = sql[match.start():]
    cleaned = cleaned.split("```", 1)[0].strip()

    if ";" in cleaned:
        cleaned = cleaned.split(";", 1)[0].strip() + ";"

    return cleaned



def generate_sql(query: str) -> dict:
    """Generate SQL, retrying malformed or incomplete model responses."""
    prompt = f"""
Translate the user's business question into one SQLite query.

Use only this schema:
{SCHEMA_CONTEXT}

Return exactly one complete read-only SELECT statement.
The statement must include FROM and must fully answer the question.
Do not return Markdown, backticks, commentary, or multiple statements.

User question:
{query}
""".strip()

    total_input_tokens = 0
    total_output_tokens = 0

    for _ in range(3):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=512,
        )

        input_tokens, output_tokens = token_counts(response)
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens

        sql = clean_sql(response.choices[0].message.content or "")

        if sql.upper().startswith("SELECT ") and " FROM " in sql.upper():
            return {
                "sql": sql,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
            }

    return {
        "sql": "",
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
    }




def execute_sql(sql: str) -> tuple[list[str], list[tuple]]:
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(sql)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchmany(100)

    return columns, rows


def interpret_results(
    query: str,
    sql: str,
    columns: list[str],
    rows: list[tuple],
) -> dict:
    prompt = f"""
Interpret these read-only SQLite results.

Original question:
{query}

SQL used:
{sql}

Columns:
{columns}

Rows:
{rows}

Provide a concise answer using only these results.
Do not invent figures or conclusions.
If there are no rows, say that no matching records were found.
""".strip()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512,
    )

    input_tokens, output_tokens = token_counts(response)

    return {
        "answer": response.choices[0].message.content or "",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def run(query: str) -> dict:
    sql_result = generate_sql(query)
    sql = sql_result["sql"]
    validation_status = validate_sql(sql)

    if validation_status != "PASSED":
        return {
            "answer": "Query blocked because the generated SQL was not approved.",
            "sql": sql,
            "rows": [],
            "validation": validation_status,
            "input_tokens": sql_result["input_tokens"],
            "output_tokens": sql_result["output_tokens"],
            "interpretation_input_tokens": 0,
            "interpretation_output_tokens": 0,
        }

    try:
        columns, rows = execute_sql(sql)
    except sqlite3.Error as error:
        return {
            "answer": "The approved SQL could not be executed.",
            "sql": sql,
            "rows": [],
            "validation": "ERROR",
            "error": str(error),
            "input_tokens": sql_result["input_tokens"],
            "output_tokens": sql_result["output_tokens"],
            "interpretation_input_tokens": 0,
            "interpretation_output_tokens": 0,
        }

    interpretation = interpret_results(query, sql, columns, rows)

    return {
        "answer": interpretation["answer"],
        "sql": sql,
        "rows": rows,
        "validation": validation_status,
        "input_tokens": sql_result["input_tokens"],
        "output_tokens": sql_result["output_tokens"],
        "interpretation_input_tokens": interpretation["input_tokens"],
        "interpretation_output_tokens": interpretation["output_tokens"],
    }
