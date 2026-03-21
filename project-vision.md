# Project Vision: OpsMind AI

## 1. Overview
OpsMind AI is an intelligent agent designed to bridge the gap between natural language user intent and traditional structured data stores. It empowers non-technical users to query, analyze, and visualize data residing in SQL (PostgreSQL, MySQL) and NoSQL (MongoDB, DynamoDB) environments without writing code.

## 2. Core Architecture
The interaction flow follows a strict "Interpret-Generate-Execute" loop to ensure accuracy and security.

### The Workflow
1.  **Intent Recognition (NLU):** The user provides a natural language query (e.g., "Show me the top 5 users by spend last month"). The LLM parses this to understand the *intent* (ranking/aggregation) and *entities* (users, spend).
2.  **Schema Retrieval:** The agent fetches the relevant database schema (table names, column types, relationships) to understand the data structure. It does *not* fetch actual data at this stage.
3.  **Query Generation (Text-to-Syntax):**
    * **SQL:** Generates ANSI SQL or dialect-specific SQL (e.g., `SELECT * FROM users...`).
    * **NoSQL:** Generates JSON-based aggregation pipelines or specific API calls.
4.  **Safety Layer:** A middleware layer validates the generated query to prevent injection attacks and ensures the query is Read-Only (blocking `DROP`, `DELETE`, or `UPDATE` commands).
5.  **Execution & Synthesis:** The query is executed against the database. The raw JSON/Tabular results are returned to the AI, which summarizes them into a human-readable answer.

## 3. Technical Stack Strategy

| Component | Technology Choices |
| :--- | :--- |
| **LLM Engine** | OpenAI GPT-4o, Claude 3.5 Sonnet, or Llama 3 (Self-hosted) |
| **Orchestration** | LangChain or LlamaIndex |
| **SQL Interface** | SQLAlchemy (Python) for generic SQL adaptation |
| **NoSQL Interface** | PyMongo (MongoDB) or Boto3 (DynamoDB) |
| **Backend** | FastAPI or Node.js |

## 4. Security Principles
* **Principle of Least Privilege:** The agent connects to the database using a restricted user account that has **strictly READ-ONLY** permissions.
* **Human-in-the-Loop (Optional):** For complex queries, the agent presents the generated SQL to the user for confirmation before execution.
* **Sanitization:** All inputs are sanitized to prevent Prompt Injection attacks that might attempt to leak schema details.
