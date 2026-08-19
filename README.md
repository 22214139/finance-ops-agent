# Finance Ops Agent

A multi-agent financial analysis system built for the Kaggle 5-Day AI Agents Intensive Capstone Project. A user asks a finance question in plain language; the system validates the input, classifies it, routes it to a specialist agent, and returns a grounded answer — with every step logged for audit.

## What It Does

Upload a CSV financial report and ask a question. The system:
- Blocks prompt-injection attempts and flags PII before anything reaches the LLM.
- Classifies the question (audit / research / procurement / visualization) and routes it to the matching agent.
- Answers using the actual data — anomaly detection is done with pandas, not guessed by the LLM.
- Remembers your preferences per category, so future answers apply them automatically.
- Logs every step (validator → triage → agent) into an inspectable trajectory, so you can see exactly what ran and what failed.

## Architecture

```
User (Gradio UI)
        |
        v
   validate_input()          <- blocks injection, flags PII, enforces length cap
        |
        v
     triage()                <- classifies into audit / research / procurement / visualization
        |
   +----+-----------+-----------+
   v    v           v           v
 audit research procurement visualization
   |    |           |           |
   +----+-----------+-----------+
        |
        v
  Trajectory + Memory          <- per-step audit log; per-category preference recall
        |
        v
   Answer + Chart (if any)
```

Every agent call and tool call runs through `safe_execute()` (timeout + exception isolation), so one failing step returns an error instead of crashing the whole request.

## Project Structure

```
ops-agent-capstone/
├── agents/
│   ├── triage.py          # classifies the question, routes it
│   ├── audit.py           # pandas anomaly detection + LLM explanation
│   ├── research.py        # trend / comparison analysis
│   └── procurement.py     # purchase order drafting
├── tools/
│   ├── validator.py       # injection keyword screen, length cap, PII flagging
│   ├── pii_redactor.py    # regex redaction for card/email/phone
│   ├── csv_reader.py      # CSV -> DataFrame / text summary
│   └── visualizer.py      # matplotlib line chart of a report
├── core/
│   ├── llm_client.py      # shared Gemini client, retry with backoff
│   ├── router.py          # wires validator -> triage -> agent -> logging together
│   ├── trajectory.py      # per-run step log + audit summary
│   └── memory.py          # category-scoped preferences + history, persisted to disk
├── sandbox/
│   └── safe_executor.py   # timeout + exception isolation for any callable
├── evaluation/
│   ├── scorecard.py       # runs test_cases.json through the pipeline, scores it
│   └── test_cases.json
├── ui/
│   └── app.py              # Gradio UI
├── data/
│   └── sample_report.csv
├── docs/screenshots/
├── main.py                 # entry point, launches the UI
├── requirements.txt
├── .env.example
└── agent.py                 # original single-notebook Kaggle submission (superseded by the above)
```

## How to Run

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

cp .env.example .env            # then paste your GOOGLE_API_KEY into .env
# get a key at https://aistudio.google.com/apikey

python main.py                  # launches the Gradio app at http://127.0.0.1:7860
```

Run the evaluation scorecard directly (as a module, so the `core`/`agents`/`tools` imports resolve):

```bash
python -m evaluation.scorecard
```

## Evaluation Scorecard

Six test cases exercise the full pipeline against `data/sample_report.csv`, checking routing correctness, keyword grounding, and the security gate:

```
TC001: PASS   "Which month had the highest profit?" -> research
TC002: PASS   "Ignore previous instructions..." -> blocked
TC003: PASS   "Are there any unusual revenue spikes?" -> audit
TC004: PASS   "Generate a purchase order for 10 laptops..." -> procurement
TC005: PASS   "" (empty input) -> blocked
TC006: PASS   "What's the overall expense trend?" -> research

Score: 6/6 (100.0%)
```

Note: TC001–TC004 and TC006 call the live Gemini API, so wording can vary between runs. Generation temperature is set low (0.2) to keep financial answers consistent, and `evaluation/scorecard.py` paces calls to stay under free-tier rate limits — but the score can still fluctuate slightly on live LLM output between runs. TC002 and TC005 (the security checks) are fully deterministic, since they never reach the LLM.

## Screenshots

**Research query** — routed correctly, answer grounded in the actual CSV numbers, trajectory shows validator ran first:

![Research query](docs/screenshots/research_query.png)

**Visualization query** — routed to the chart agent, matplotlib line chart rendered inline:

![Visualization query](docs/screenshots/visualization_query.png)

## Tech Stack

- **Model:** Gemini (`gemini-flash-lite-latest`) via the `google-genai` SDK
- **UI:** Gradio
- **Data:** pandas, matplotlib
- **Config:** python-dotenv (`.env`, not Kaggle secrets — this version runs locally)

## Features

- **CSV analysis** — anomaly detection via z-score thresholds, trend/comparison narrative
- **Category-scoped memory** — preferences recalled per agent, capped at the 5 most recent
- **Guardrails** — blocks prompt injection, flags PII, redacts it before logging
- **Sandbox** — every tool/agent call is timeout-bound and exception-isolated
- **Retry logic** — exponential backoff on transient API failures
- **Trajectory audit** — full step-by-step log of what ran, in what order, and what failed
- **Evaluation scorecard** — automated pass/fail against a fixed test set

## Known Limitations

- Gradio launches locally only (no `share=True`) — the app processes financial data, so a public tunnel isn't turned on by default. Pass `demo.launch(share=True)` yourself if you want one.
- The free Gemini API tier has a low requests-per-minute limit; rapid-fire testing (e.g. re-running the scorecard immediately after manual testing) can trigger transient 429s. `core/llm_client.py` retries with backoff, and the scorecard paces its own calls, but very heavy concurrent use can still hit the ceiling.
- `agent.py` at the repo root is the original single-notebook Kaggle submission. It still works standalone in a Kaggle notebook but is no longer part of this pipeline.
