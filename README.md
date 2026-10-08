# Spoonful Enterprise RAG System

A Python CLI application that routes enterprise questions to specialized qualitative and quantitative agents. The system combines semantic document retrieval, natural-language-to-SQL generation, SQLite analysis, response validation, and token usage logging.

## Project status

- CLI entry point: `main.py`
- Qualitative agent: semantic retrieval from ChromaDB plus grounded answer generation
- Quantitative agent: SQLite queries generated from natural-language questions
- Manager agent: qualitative, quantitative, or both-agent routing
- Validation layer: SQL guardrails and qualitative grounding checks
- Tokenomics: JSON Lines logging in `tokenomics_log.jsonl`
- Current model integration: Gemini through an OpenAI-compatible API endpoint
- Original assignment model: Claude. Confirm that the Gemini migration is accepted for grading.

The original capstone requires a manager agent, qualitative and quantitative agents, validation before output, token logging, a CLI, and concrete Trust-but-Verify evidence. [f96e132e-6193-4d73-8c28-4d73-8c28-4dce13d924de]

## Architecture

### Manager agent

The manager classifies each query as:

- `qualitative`: documentation, policies, procedures, or explanations
- `quantitative`: metrics, trends, comparisons, or SQL-queryable data
- `both`: requires document retrieval and data analysis

The classifier retries empty model responses and applies a deterministic fallback based on query terms.

### Qualitative agent

The qualitative agent:

1. Embeds the user query.
2. Retrieves relevant document chunks from ChromaDB.
3. Sends the retrieved context to the language model.
4. Produces an answer grounded in the supplied documents.
5. Runs a grounding validation check before displaying the result.

### Quantitative agent

The quantitative agent:

1. Supplies the database schema to the language model.
2. Generates a read-only SQL query.
3. Extracts and cleans the first SQL statement from model output.
4. Validates that the query is a permitted `SELECT` statement.
5. Executes approved SQL against SQLite.
6. Uses the model to interpret the returned results.

Non-`SELECT` statements and blocked SQL keywords are rejected before execution.

## Data sources

The project uses:

- ChromaDB data in `data/chroma`
- SQLite data in `data/database.sqlite`
- Source documents under the project data directory

The quantitative schema includes these tables:

- `sales(id, region, product, revenue, date, units_sold)`
- `customers(id, name, industry, churn_date, satisfaction_score)`
- `employees(id, department, satisfaction_score, tenure_years)`

## Setup

1. Create and activate a Python virtual environment.
2. Install the packages listed in `requirements.txt`.
3. Create a local `.env` file.
4. Set the Gemini API key in `.env` using the variable expected by the agents.
5. Do not commit `.env` or expose its contents.

The repository was checked to confirm that `.env` is ignored and that no likely Google API key was found outside `.env`.

## Running the application

From the project root, run `python main.py`.

Enter a question at the prompt. Type `exit` or `quit` to stop.

Example questions:

- `Explain the code review process.`
- `What is the total revenue by region?`
- `Use employee satisfaction data and explain which documented policies may affect it.`

## Validation and Trust-but-Verify

The system does not automatically trust model output. It validates generated SQL before execution and checks qualitative answers against retrieved context.

### Example 1: Successful quantitative answer

**Query:** `What is the total revenue by region?`

**Generated SQL:**

`SELECT region, SUM(revenue) AS total_revenue FROM sales GROUP BY region;`

**Validation:** `PASSED`

**Returned result:**

- East: 401,000.0
- North: 307,000.0
- South: 321,000.0
- West: 310,000.0

**Decision:** The query was accepted because it was a read-only aggregate over the approved `sales` table and passed validation.

### Example 2: Model output blocked before database execution

**Query:** `How many employees are in each department, and what is the average employee satisfaction score by department?`

**Model output observed:** An incomplete Markdown-wrapped response beginning with `**:` and `SELECT department`.

**Validation:** `FAILED`

**Decision:** The result was not accepted. The guardrail correctly blocked execution because the generated SQL was incomplete and did not contain a complete approved query. The SQL generation path was updated to strip Markdown, extract a complete `SELECT` statement, and retry malformed responses. Live verification remains pending because the Gemini quota was subsequently exhausted.

### Example 3: Grounded qualitative answer

**Query:** `Explain the code review process.`

**Model response:** The answer described pull request submission, two qualified reviewers, required automated tests, review criteria, author responsibilities, and branch protection safeguards.

**Validation:** No validation warning was produced.

**Decision:** The answer was accepted because it was grounded in the retrieved documentation and included source references in the response.

## Testing completed

### Offline tests

The following checks passed:

- Python compilation for the application and supporting modules
- SQL `SELECT` validation
- Blocking of a `DELETE` statement
- Grounded qualitative answer validation
- Flagging of unsupported qualitative content
- Acceptance of an explicit unable-to-find response
- Direct SQLite aggregation query returning four rows
- Confirmation that the database exists
- Confirmation that ChromaDB data exists
- Confirmation that `.env` is ignored
- Scan for likely exposed Google API keys outside `.env`

### Routing tests

The manager successfully classified these routes:

- `Explain the code review process.` → `qualitative`
- `What is the total revenue by region?` → `quantitative`
- `Use employee satisfaction data and explain which documented policies may affect it.` → `both`

The `both` classification required one retry after an initial invalid response.

### Pending live tests

The token log currently contains 16 entries representing 6 distinct queries. The assignment target is at least 10 distinct logged queries, so four additional live queries remain pending after the Gemini quota resets.

Recommended pending queries:

1. `What are total units sold by product?`
2. `How many customers have a recorded churn date?`
3. `What is the average tenure by department?`
4. `What is the average customer satisfaction score by industry?`

Run these individually and verify route, validation status, SQL, answer quality, and the new token log entry.

## Tokenomics

Every model call is logged in `tokenomics_log.jsonl` with:

- Timestamp
- User query
- Agent name
- Input token count
- Output token count
- Estimated cost

The current logger uses inherited illustrative rates. These figures should not be treated as verified Gemini pricing until the applicable Gemini rate card is confirmed.

Retries create additional model calls and therefore additional token usage. Empty-response retries and malformed SQL retries are intentionally recorded.

## Security notes

- API credentials are loaded from `.env`.
- `.env` is excluded by `.gitignore`.
- API keys must never be committed.
- Do not paste credentials into issues, commits, logs, or chat transcripts.
- Verify the repository contents before sharing the GitHub URL.

## Known limitations

- Gemini free-tier quota was exhausted during testing, temporarily preventing further live queries.
- The classifier and SQL generator use retries that may consume additional quota.
- Four additional distinct queries are still needed to reach the 10-query target.
- The Gemini migration requires confirmation against the original Claude-only assignment requirement.
- The README was completed after the initial repository upload, so commit and push this file before submission.

## Submission checklist

- [x] Python application compiles successfully
- [x] Manager agent routes qualitative, quantitative, and both-agent queries
- [x] Qualitative retrieval and grounding validation are implemented
- [x] Quantitative SQLite integration is implemented
- [x] SQL guardrails block unsafe or malformed queries
- [x] Tokenomics logging is implemented
- [x] CLI entry point is implemented
- [x] `.env` is ignored and no likely API key is exposed
- [x] `tokenomics_log.jsonl` is present
- [x] Trust-but-Verify examples are documented
- [ ] At least 10 distinct live queries logged
