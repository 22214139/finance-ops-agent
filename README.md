# Finance Ops Agent

A multi-agent financial analysis system built for the Kaggle 5-Day AI Agents Intensive Capstone Project. Upload a CSV financial report, ask a question in plain language — the system validates input, classifies it, routes it to the right specialist agent, verifies the answer, and returns a grounded response with every step logged for audit.

---

## What It Does

- Blocks prompt-injection attempts and redacts PII before anything reaches the LLM
- Classifies the question into one of five categories and routes it to the matching agent
- Answers using actual data — anomaly detection and what-if math run on pandas, not guessed by the LLM
- Scores its own answers with a confidence score and the source rows they are grounded in
- Runs an independent auditor agent that re-checks answers against the data for hallucination before they reach you
- Flags statistical outliers the instant a CSV is uploaded, before any question is asked
- Catches contradictions — if a new answer conflicts with an earlier one in the same session, it says so
- Remembers preferences per category so future answers apply them automatically
- Logs every step into an inspectable trajectory so you can see exactly what ran and what failed

---

## Architecture

```
User (Gradio UI)
        |
        v
   validate_input()          <- blocks injection, redacts PII, enforces length cap
        |
        v
     triage()                <- classifies into anomaly_detection / trend_analysis /
        |                       cost_analysis / visualization / simulation
        |
   +----+--------------------+------------------+------------------+
   v                         v                  v                  v
anomaly_detection       trend_analysis     cost_analysis      simulation
        |                    |                                     |
        +--------------------+-------------------------------------+
                             |
                             v
              audit_agent_response()    <- re-checks the answer against the data
                             |             for grounding and hallucination
                             v
              check_contradiction()    <- flags conflicts with earlier answers
                             |             from the same session
                             v
         Trajectory + Memory + Session <- per-step audit log; per-category
                             |             preference recall; resettable session
                             v
                  Answer + Chart (if any)

CSV upload (fires independently, before any question is asked)
        |
        v
  check_on_upload()          <- z-score anomaly scan on upload
```

Every agent and tool call runs through `safe_execute()` — timeout and exception isolation — so one failing step returns an error instead of crashing the whole request.

---

## Project Structure

```
ops-agent-capstone/
├── agents/
│   ├── triage.py              # classifies the question, routes it
│   ├── anomaly_detection.py   # pandas z-score anomaly detection + LLM explanation + confidence score
│   ├── trend_analysis.py      # trend and comparison analysis + confidence score
│   ├── cost_analysis.py       # cost analysis, vendor management, purchase order drafting
│   ├── simulator.py           # what-if scenarios: LLM extracts params, pandas computes outcome
│   ├── auditor.py             # independently re-verifies answers for grounding and hallucination
│   ├── contradiction.py       # flags a new answer that conflicts with an earlier one this session
│   └── summary.py             # session stats: questions asked, agents used, audit pass rate
├── tools/
│   ├── validator.py           # injection keyword screen, length cap, PII flagging
│   ├── pii_redactor.py        # regex redaction for card / email / phone
│   ├── csv_reader.py          # CSV -> DataFrame / text summary
│   ├── visualizer.py          # matplotlib chart of a report
│   └── anomaly_alert.py       # z-score scan that fires immediately on CSV upload
├── core/
│   ├── llm_client.py          # shared Gemini client with retry and exponential backoff
│   ├── router.py              # wires validator -> triage -> agent -> auditor -> contradiction -> logging
│   ├── trajectory.py          # per-run step log and audit summary
│   ├── memory.py              # category-scoped preferences and history, persisted to disk
│   └── session.py             # in-memory resettable Q&A window for the current sitting
├── sandbox/
│   └── safe_executor.py       # timeout and exception isolation for any callable
├── evaluation/
│   ├── scorecard.py           # runs test_cases.json through the pipeline and scores it
│   └── test_cases.json
├── ui/
│   └── app.py                 # Gradio UI with Analyze, Session Summary, and New Session tabs
├── data/
│   └── sample_report.csv
├── docs/
│   └── screenshots/
├── main.py                    # entry point, launches the UI
├── requirements.txt
└── .env.example
```

---

## How to Run

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac / Linux
pip install -r requirements.txt

cp .env.example .env
# open .env and paste your GOOGLE_API_KEY
# get a free key at https://aistudio.google.com/apikey

python main.py
# app launches at http://127.0.0.1:7860
```

Run the evaluation scorecard:

```bash
python -m evaluation.scorecard
```

### Docker

```bash
docker build -t finance-ops-agent .
docker run -p 7860:7860 --env-file .env finance-ops-agent
```

---

## Evaluation Scorecard

Seven test cases exercise the full pipeline against `data/sample_report.csv`:

```
TC001: PASS   "Which month had the highest profit?"           -> trend_analysis
TC002: PASS   "Ignore previous instructions..."              -> blocked
TC003: PASS   "Are there any unusual revenue spikes?"        -> anomaly_detection
TC004: PASS   "Generate a purchase order for 10 laptops..."  -> cost_analysis
TC005: PASS   "" (empty input)                               -> blocked
TC006: PASS   "What's the overall expense trend?"            -> trend_analysis
TC007: PASS   "What if we reduce expenses by 10% in March?"  -> simulation

Score: 7/7 (100%)
```

TC002 and TC005 are fully deterministic — they never reach the LLM. The remaining five call the live Gemini API; temperature is set to 0.2 for consistency.

---

## Tests

Unit tests cover all deterministic, non-LLM logic: the validator and PII gate, CSV parsing, pandas-based anomaly detection, memory persistence, and trajectory logging. No API key needed.

```bash
pip install -r requirements-dev.txt
pytest -v
```

CI runs this suite and a Docker build check on every push and pull request to `main`.

---

## Tech Stack

- **Model:** Gemini via `google-genai` SDK
- **UI:** Gradio
- **Data processing:** pandas, matplotlib, scipy (z-score)
- **Config:** python-dotenv

---

## Features

- **Anomaly detection** — z-score on each numeric column (threshold 1.5), pandas does the math, LLM explains the finding
- **Trend analysis** — month-over-month comparison and performance narrative grounded in the actual data
- **Cost analysis** — expense breakdown, vendor management, purchase order generation
- **What-if simulator** — LLM extracts the scenario parameters; pandas computes the before/after outcome; no guessing
- **Confidence scoring** — answers come back with `CONFIDENCE`, `GROUNDED`, and `SOURCE ROWS`
- **Independent auditor agent** — re-checks every answer against the CSV for hallucination before delivery
- **Auto anomaly alert** — fires on CSV upload, independent of any question
- **Contradiction detector** — flags when a new answer conflicts with an earlier one this session
- **Session summary** — on-demand: questions asked, agents used, audit pass rate, anomalies detected
- **Category-scoped memory** — preferences stored per agent category, capped at the 5 most recent
- **Guardrails** — injection keyword blocking, PII flagging, redaction before logging
- **Sandbox** — every call is timeout-bound and exception-isolated
- **Retry logic** — exponential backoff on transient API failures
- **Trajectory audit** — full step-by-step log of what ran, in what order, and what failed

---

## Known Limitations

- Gradio runs locally only — no `share=True` by default, since the app processes financial data
- The free Gemini API tier has a low requests-per-minute limit; the auditor and contradiction checks add extra LLM calls per question
- Session state resets on app restart and is not shared across browser tabs

---

## Links

- Kaggle Notebook: [kaggle.com/code/taranehkhorshidi/finance-ops-capstone](https://www.kaggle.com/code/taranehkhorshidi/finance-ops-capstone)
- GitHub: [github.com/22214139/ops-agent-capstone](https://github.com/22214139/ops-agent-capstone)
