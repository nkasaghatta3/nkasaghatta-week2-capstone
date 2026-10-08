import re


REFUSAL_PHRASES = (
    "cannot find",
    "not found",
    "insufficient information",
    "not enough information",
    "unable to answer",
)


def validate_qualitative(answer: str, chunks: list[dict]) -> dict:
    """Check whether an answer cites at least one retrieved source."""
    sources_cited = []

    for index, chunk in enumerate(chunks, start=1):
        if f"Source {index}" in answer:
            sources_cited.append(chunk["source"])

    refused = any(phrase in answer.lower() for phrase in REFUSAL_PHRASES)
    grounded = bool(sources_cited)

    return {
        "is_grounded": grounded,
        "refused_to_answer": refused,
        "sources_cited": sources_cited,
        "flag": not grounded and not refused,
        "warning": (
            "Response may not be grounded in source documents."
            if not grounded and not refused
            else None
        ),
    }


def validate_sql(sql: str) -> str:
    """Allow one read-only SELECT statement only."""
    normalized = re.sub(r"/\*.*?\*/|--[^\n]*", "", sql, flags=re.DOTALL)
    normalized = normalized.strip()

    if not normalized:
        return "FAILED"

    if normalized.endswith(";"):
        normalized = normalized[:-1].strip()

    if ";" in normalized:
        return "FAILED"

    if not re.match(r"^SELECT\b", normalized, flags=re.IGNORECASE):
        return "FAILED"

    return "PASSED"


def validate_quantitative(
    answer: str,
    sql: str,
    validation_status: str,
) -> dict:
    """Record whether SQL validation succeeded before execution."""
    sql_validated = validation_status == "PASSED"
    sql_blocked = validation_status == "FAILED"
    execution_error = validation_status == "ERROR"

    return {
        "sql_validated": sql_validated,
        "sql_blocked": sql_blocked,
        "execution_error": execution_error,
        "flag": not sql_validated,
        "warning": (
            f"SQL validation status: {validation_status}"
            if not sql_validated
            else None
        ),
    }
