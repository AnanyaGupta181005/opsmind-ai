# OpsMind AI — project vision

## The problem
Operational knowledge in a company is split between a database nobody queries directly
and a handbook nobody reads. Answering "can this intern carry leave over?" or "who joined
last month?" means a person stitching those two together by hand.

## The thesis
A manager agent should do both: query structured records **and** retrieve unstructured
policy, then act. Two things make that trustworthy rather than impressive-looking:

1. **Grounding.** Policy answers must come from retrieved passages and cite them, and must
   refuse when the evidence is not there.
2. **Legibility.** Every tool call is shown — name, arguments, result summary, duration.
   A reviewer can see exactly what the agent did, not just what it said.

## Non-goals
- Not a general chatbot. If a question is not answerable by a tool or the indexed corpus,
  the correct output is a refusal and a routing suggestion.
- Not autonomous by default. Write tools are withheld unless the session arms them.

## Design principles
- **Degrade, never crash.** Each subsystem has a mock path and `/health` says which is live.
- **One contract.** Pydantic schemas are shared by API, agent and UI.
- **Boring infrastructure.** Multi-stage Docker, one compose file, no bespoke glue.
