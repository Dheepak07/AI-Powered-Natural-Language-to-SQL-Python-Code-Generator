# Screenshots

No screenshots are included in this repository.

Capturing them requires the app to actually be running end-to-end, which needs:
- A live MySQL instance loaded with `data/schema.sql` and `data/seed_data.sql`
- A valid `ANTHROPIC_API_KEY` so `NL2SQLChain` can call Claude
- A browser to interact with the running Streamlit server

None of these were available in the environment used to prepare this documentation, so no screenshots were captured — and none have been fabricated.

## What to capture once you run the app locally

Run `streamlit run frontend/app.py` after completing the setup in the main [README](../README.md), then capture:

1. **`01_home.png`** — Landing page with the sidebar (DB connection status, sample questions, empty query history) and the empty question input.
2. **`02_generated_sql.png`** — The "SQL Query" tab after asking a question: generated SQL, the ✅ validation badge, the plain-English explanation, and the visualization recommendation.
3. **`03_pandas_code.png`** — The "Python / Pandas" tab showing the generated Pandas snippet.
4. **`04_results.png`** — The "Results" tab after clicking **Execute SQL against MySQL**: the returned DataFrame and the CSV download button.
5. **`05_query_history.png`** — Sidebar query history after a few questions have been asked.

Save them into this `screenshots/` folder using the numbered names above, and reference them from the README's Screenshots section once available.
