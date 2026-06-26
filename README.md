# Finance Ops Agent 🤖📊

A Spec-Driven Autonomous Financial Analysis Agent built for the Kaggle 5-Day AI Agents Intensive Capstone Project.

## What It Does
This agent analyzes company financial reports (CSV files) using natural language questions. It remembers manager preferences across sessions and protects against prompt injection attacks.

## Features
- 📊 **CSV Analysis** — Reads and analyzes financial reports
- 🧠 **Long-term Memory** — Remembers manager preferences between sessions
- 🛡️ **Guardrails** — Blocks prompt injection attacks
- 🔄 **Retry Logic** — Exponential backoff for API rate limits
- 📋 **Observability** — Logs every action with timestamps

## Tech Stack
- **Model:** Gemini 1.5 Flash (Google AI Studio)
- **SDK:** google-genai (Python)
- **Platform:** Kaggle Notebooks
- **Data:** CSV financial reports

## Project Structure
