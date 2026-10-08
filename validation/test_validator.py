from validation.validator import (
    validate_qualitative,
    validate_quantitative,
    validate_sql,
)


chunks = [
    {"source": "security_policy.txt"},
    {"source": "code_review_process.txt"},
]

grounded = validate_qualitative(
    "Source 2 explains that production changes require review.",
    chunks,
)
assert grounded["is_grounded"] is True
assert grounded["flag"] is False

irrelevant = validate_qualitative(
    "The company should open offices in three new cities.",
    chunks,
)
assert irrelevant["is_grounded"] is False
assert irrelevant["flag"] is True

assert validate_sql("SELECT COUNT(*) FROM sales;") == "PASSED"
assert validate_sql("DELETE FROM sales;") == "FAILED"
assert validate_sql("SELECT * FROM sales; DROP TABLE sales;") == "FAILED"

quantitative = validate_quantitative(
    "Revenue is increasing.",
    "DELETE FROM sales;",
    "FAILED",
)
assert quantitative["sql_blocked"] is True
assert quantitative["flag"] is True

print("All validator tests passed.")
