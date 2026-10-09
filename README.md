# Spoonful Enterprise RAG System

A Python CLI application that routes enterprise questions to specialized qualitative and quantitative agents. The system combines semantic document retrieval, natural-language-to-SQL generation, SQLite analysis, response validation, and token usage logging.

## Project status

- CLI entry point: `main.py`
- Qualitative agent: semantic retrieval from ChromaDB and grounded answer generation
- Quantitative agent: natural-language-to-SQL generation and SQLite analysis
- Manager agent: qualitative, quantitative, or combined routing
- Validation layer: SQL guardrails and qualitative grounding checks
- Tokenomics: JSON Lines logging in `tokenomics_log.jsonl`
- Model integration: Gemini through an OpenAI-compatible API endpoint

## Architecture

```text
User question
      |
      v
Manager agent
      |
      +--------------------+
      |                    |
      v                    v
Qualitative agent    Quantitative agent
      |                    |
      v                    v
ChromaDB retrieval   SQLite query generation
      |                    |
      v                    v
Grounded response   SQL validation and execution
      |                    |
      +----------+---------+
                 |
                 v
       Response validation
                 |
                 v
          CLI response
                 |
                 v
       Tokenomics logging

Manager agent
The manager classifies each query as:

qualitative: documentation, policies, procedures, or explanations
quantitative: metrics, trends, comparisons, or SQL-queryable data
both: requires document retrieval and data analysis

The classifier retries empty responses and applies a deterministic fallback when necessary.
Qualitative agent
The qualitative agent:

Embeds the user query.
Retrieves relevant document chunks from ChromaDB.
Sends the retrieved context to Gemini.
Produces an answer grounded in the supplied documents.
Runs grounding validation before displaying the result.

Quantitative agent
The quantitative agent:

Supplies the database schema to Gemini.
Generates a read-only SQL query.
Extracts and cleans the first SQL statement from the model output.
Validates that the query is a permitted SELECT statement.
Executes approved SQL against SQLite.
Uses Gemini to interpret the returned results.

Non-SELECT statements and blocked SQL keywords are rejected before execution.
Data sources
The project uses:

ChromaDB data in data/chroma
SQLite data in data/database.sqlite
Source documents under the project data directory

The quantitative schema includes:

sales(id, region, product, revenue, date, units_sold)
customers(id, name, industry, churn_date, satisfaction_score)
employees(id, department, satisfaction_score, tenure_years)

The document collection includes:

Enterprise Security Policy
Software Code Review Process
Customer Complaints Process

##Setup

Create and activate a Python virtual environment.
Install the packages listed in requirements.txt.
Create a local .env file.
Add the Gemini API credential using the environment variable expected by the agents.
Do not commit .env or expose its contents.

API credentials are loaded locally from .env. The file remains excluded through .gitignore.
Running the application
From the project root, run:
Bashpython main.py

Enter a question at the prompt. Type exit or quit to stop.
Example questions:

Explain the code review process.
What is the total revenue by region?
What are the total units sold by product?
How many customers have a recorded churn date?
What is the average tenure by department?
How do we handle customer complaints?

##Validation and Trust-but-Verify
The system does not automatically trust model output. It validates generated SQL before execution and checks qualitative answers against retrieved context.
Example 1: Average tenure by department
Query: What is the average tenure by department?
Generated SQL:
SELECT department, AVG(tenure_years) FROM employees GROUP BY department
Validation: PASSED
Returned result:

Customer Success: 3.75 years
Engineering: 4.25 years
Operations: 5.0 years
Sales: 3.25 years

Decision: The result was accepted because the query was read-only, used the approved employees table, and returned a valid grouped aggregation.
Example 2: Customer complaints process
Query: How do we handle customer complaints?
Model response: The response stated that complaints must be recorded within one business day, acknowledged within two business days, categorized by issue type and severity, escalated when critical, assigned an action plan within three business days, and resolved or updated within the required timeframes.
Validation: No grounding warning was produced.
Decision: The answer was accepted because its process details were supported by the retrieved Customer Complaints Process document and included source references.
Example 3: Employee count and satisfaction by department
Query: How many employees are in each department, and what is the average employee satisfaction score by department?
Generated SQL:
SELECT department, COUNT(id) AS employee_count, AVG(satisfaction_score) AS average_satisfaction FROM employees GROUP BY department
Validation: PASSED
Returned result:

Customer Success: 2 employees, average satisfaction 4.3
Engineering: 2 employees, average satisfaction 4.35
Operations: 2 employees, average satisfaction 4.15
Sales: 2 employees, average satisfaction approximately 3.95

Decision: The result was accepted after verifying that the SQL used a permitted read-only aggregation and that the returned departments and metrics matched the database schema.
Trust-but-Verify resolution
The quantitative interpretation was not accepted solely because it sounded plausible. The generated SQL was checked for permitted syntax, executed against SQLite, and compared with the returned columns and rows. The final answer was accepted only after the query and results were consistent.
Testing completed
Offline tests
The following checks passed:

Python compilation for the application and supporting modules
SQL SELECT validation
Blocking of a DELETE statement
Grounded qualitative answer validation
Flagging of unsupported qualitative content
Acceptance of an explicit unable-to-find response
Direct SQLite aggregation query returning four rows
Confirmation that the database exists
Confirmation that ChromaDB data exists
Confirmation that .env is ignored
Scan for likely exposed API keys outside .env

Routing tests
The manager successfully classified:

Explain the code review process. → qualitative
What is the total revenue by region? → quantitative
Use employee satisfaction data and explain which documented policies may affect it. → both

Successful live queries logged
The token log contains successful records for at least 10 distinct questions:

Explain the code review process.
What are the requirements for production code changes?
What are the total units sold by product?
How many customers have a recorded churn date?
What is the average tenure by department?
What is the average customer satisfaction score by industry?
What is the total revenue by region?
How do we handle customer complaints?
How many employees are in each department, and what is the average employee satisfaction score by department?
What are the provided documents?

Each completed run was routed to an appropriate agent, produced tokenomics records, and returned a validated answer.
##Tokenomics
Every model call is logged in tokenomics_log.jsonl with:

Timestamp
User query
Agent name
Input token count
Output token count
Estimated cost
Estimated cost per 1,000 queries

A single user query may produce multiple log entries because classification, retrieval, SQL generation, and interpretation can each involve separate model calls.
Security notes

API credentials are loaded from .env.
.env is excluded by .gitignore.
API keys must never be committed.
Do not paste credentials into issues, commits, logs, or chat transcripts.
Verify repository contents before sharing the GitHub URL.

Known limitations

Model calls depend on Gemini service availability and quota.
Classifier and SQL-generation retries can increase token usage.
Token costs are estimates based on the rates configured in the project logger.
The system does not retain conversation history between separate CLI questions.

Submission checklist

[x] Python application compiles successfully
[x] Manager agent routes qualitative, quantitative, and both-agent queries
[x] Qualitative retrieval and grounding validation are implemented
[x] Quantitative SQLite integration is implemented
[x] SQL guardrails block unsafe or malformed queries
[x] Tokenomics logging is implemented
[x] CLI entry point is implemented
[x] .env is ignored and no likely API key is exposed
[x] tokenomics_log.jsonl is present
[x] Trust-but-Verify examples are documented
[x] At least 10 distinct successful live queries logged