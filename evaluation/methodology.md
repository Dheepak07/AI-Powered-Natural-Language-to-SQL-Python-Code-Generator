# Evaluation Methodology

## Implemented Evaluation

**Unit/regression tests exist and pass** — this is real, verified testing of the deterministic parts of the pipeline (no live API or database needed):

- `tests/test_validator.py` — SQL safety validation (blocklist, SELECT-only enforcement, CTE support, schema-table checks, SQL cleaning)
- `tests/test_chain.py` — AI response parsing (valid JSON, markdown-fenced JSON, unknown chart types, malformed/empty responses)
- `tests/test_executor.py` — Pandas code execution (aggregation, filtering, syntax/runtime error handling)

Run with:
```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```
28 tests, all passing, as of this documentation pass.

**What this does *not* cover:** none of these tests measure whether the AI actually generates *correct* SQL for a given natural-language question — that requires live calls to Claude and is not implemented in this repository. No NL2SQL accuracy numbers (SQL validity rate, execution success rate, exact-match rate, etc.) currently exist for this project. Do not quote any until they are actually produced by the methodology below.

## Recommended Evaluation Methodology (NL2SQL Accuracy)

### Objective
Measure how often the natural-language-to-SQL pipeline produces a query that is both syntactically valid and semantically correct for the intended business question, using the existing `ecommerce_db` schema.

### Evaluation Dataset
Build a labeled set of (question, ground-truth SQL, expected result) triples against `data/schema.sql` + `data/seed_data.sql`. The 10 sample questions already surfaced in `frontend/app.py`'s sidebar are a natural starting point — write the ground-truth SQL and expected result for each, then extend with edge cases:
- Simple aggregation ("Show top 10 customers by total revenue")
- Multi-table joins ("Which sales reps closed the most orders?")
- Date filtering ("Customers who haven't ordered in 90 days")
- Ambiguous/underspecified questions, to check how the model handles them
- Out-of-schema questions (asking about data the schema doesn't have), to check the model doesn't hallucinate a plausible-looking but wrong query

### Test Cases
At minimum, the 10 existing sample questions plus 10-15 additional questions spanning the categories above (~20-25 total).

### Ground Truth
A hand-written, verified-correct SQL query and its expected result set (row count and/or key aggregate values) for each test question.

### Evaluation Process
1. For each test question, call `NL2SQLChain.run(question)` to get the generated SQL.
2. Run the generated SQL through `SQLValidator.validate()` (already implemented) — record pass/fail.
3. If valid, execute it via `execute_query()` and compare the result against ground truth.
4. Record outcomes per question: valid/invalid, executed/failed, result match/mismatch.

### Metrics (NL2SQL-appropriate)
- **SQL Validity Rate** — % of generated queries that pass `SQLValidator` (parseable, SELECT-only, no blocked keywords)
- **Execution Success Rate** — % of valid queries that execute against MySQL without error
- **Exact SQL Match** — % of generated queries that exactly match ground-truth SQL (a strict, usually low-value metric on its own, since equivalent queries can be phrased differently)
- **Result Correctness** — % of executed queries whose *returned data* matches the expected result (the most meaningful correctness metric for this use case)
- **Error Rate** — % of questions that fail at any stage (generation, validation, or execution), broken down by stage

### Baseline
No baseline currently exists. A reasonable baseline to compare against is a fixed-template query generator (e.g. keyword-matching common patterns like "top N by X") to quantify the lift the LLM-based approach provides over simple heuristics.

### Results
Not available — this methodology has not been executed yet. Run it and record results here (or in a linked results file) before citing any numbers.

### Error Analysis
Once results exist, categorize failures by root cause: schema misunderstanding, wrong aggregation/grouping, wrong join, ambiguous question misinterpreted, or validator false-positive/negative — and note common patterns to guide prompt or validator improvements.

### Limitations
- Evaluating "Result Correctness" requires a running MySQL instance with the seed data loaded and a live `ANTHROPIC_API_KEY`, neither of which is bundled with the repository (by design, since API keys must never be committed).
- LLM outputs are non-deterministic even at `TEMPERATURE=0.0` in edge cases; repeated runs may be needed to assess consistency.
- This methodology does not evaluate the generated Pandas code's correctness — only the SQL path. A similar process could be applied to `pandas_code` output if that becomes a priority.
