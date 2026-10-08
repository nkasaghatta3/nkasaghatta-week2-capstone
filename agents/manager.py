import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents import qualitative, quantitative
from tokenomics.logger import log
from validation.validator import validate_qualitative, validate_quantitative

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


def token_counts(response) -> tuple[int, int]:
    usage = response.usage
    if not usage:
        return 0, 0
    return usage.prompt_tokens, usage.completion_tokens


def classify(query: str) -> str:
    """Classify a query, retrying empty model responses safely."""
    prompt = f"""
Classify this query as exactly one lowercase word:
qualitative, quantitative, or both.

qualitative: policies, processes, procedures, explanations, or documentation.
quantitative: numbers, metrics, trends, comparisons, or SQL-queryable data.
both: requires document search and data analysis.

Return exactly one word and nothing else.

Query:
{query}
""".strip()

    for attempt in range(2):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=128,
        )

        route = (response.choices[0].message.content or "").strip().lower()
        route = route.strip(" .,:;")
        input_tokens, output_tokens = token_counts(response)

        log(
            query=query,
            agent=f"manager-classifier-{attempt + 1}",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        if route in {"qualitative", "quantitative", "both"}:
            print(f"[CLASSIFIER RAW OUTPUT] {route!r}")
            return route

    lowered = query.lower()
    quantitative_terms = (
        "revenue", "sales", "churn", "satisfaction", "metric",
        "trend", "compare", "total", "average", "count", "data",
    )
    qualitative_terms = (
        "policy", "process", "procedure", "explain", "requirements",
        "security", "complaint", "documentation",
    )

    has_quantitative = any(term in lowered for term in quantitative_terms)
    has_qualitative = any(term in lowered for term in qualitative_terms)

    if has_quantitative and has_qualitative:
        return "both"
    if has_quantitative:
        return "quantitative"
    return "qualitative"




def print_qualitative_result(query: str) -> None:
    result = qualitative.run(query)
    validation = validate_qualitative(result["answer"], result["chunks"])

    log(
        query=query,
        agent="qualitative",
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
    )

    print("\n[Qualitative]")
    if validation["flag"]:
        print(f"VALIDATION WARNING: {validation['warning']}")
    print(result["answer"])


def print_quantitative_result(query: str) -> None:
    result = quantitative.run(query)
    validation = validate_quantitative(
        result["answer"],
        result["sql"],
        result["validation"],
    )

    log(
        query=query,
        agent="quantitative-sql",
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
    )

    if result["interpretation_input_tokens"] or result["interpretation_output_tokens"]:
        log(
            query=query,
            agent="quantitative-interpretation",
            input_tokens=result["interpretation_input_tokens"],
            output_tokens=result["interpretation_output_tokens"],
        )

    print("\n[Quantitative]")
    if validation["flag"]:
        print(f"VALIDATION WARNING: {validation['warning']}")
    print(result["answer"])
    print(f"SQL used: {result['sql']}")


def run(query: str) -> str:
    route = classify(query)

    print(f"\nQuery: {query}")
    print(f"Route: {route}")

    if route in {"qualitative", "both"}:
        print_qualitative_result(query)

    if route in {"quantitative", "both"}:
        print_quantitative_result(query)

    return route
