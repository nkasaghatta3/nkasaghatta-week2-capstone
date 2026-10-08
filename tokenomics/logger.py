import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_PATH = BASE_DIR / "tokenomics_log.jsonl"

# These are the assignment's illustrative rates. Confirm the rate required by your instructor.
COST_PER_1K_INPUT = 0.003
COST_PER_1K_OUTPUT = 0.015


def log(
    query: str,
    agent: str,
    input_tokens: int,
    output_tokens: int,
) -> dict:
    """Calculate and persist token usage for one model interaction."""
    input_cost = (input_tokens / 1000) * COST_PER_1K_INPUT
    output_cost = (output_tokens / 1000) * COST_PER_1K_OUTPUT
    total_cost = input_cost + output_cost

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "agent": agent,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(total_cost, 6),
        "cost_per_1000_queries": round(total_cost * 1000, 2),
    }

    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")

    print(
        f"[TOKENOMICS] Agent: {agent} | "
        f"Input: {input_tokens} | Output: {output_tokens} | "
        f"Cost: ${total_cost:.6f}"
    )

    return entry
