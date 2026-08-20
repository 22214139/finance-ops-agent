"""Gradio UI for the Finance Ops Intelligence Network."""
import gradio as gr

from agents.summary import generate_session_summary
from core.memory import Memory
from core.router import run_pipeline
from core.session import Session
from tools.anomaly_alert import check_on_upload

_memory = Memory()
_session = Session()


def run_pipeline_ui(csv_file, question):
    result = run_pipeline(question, filepath=csv_file, memory=_memory, session=_session)
    return result.agent, result.answer, result.chart_path, result.trajectory.summary()


def check_on_upload_ui(csv_file):
    alert = check_on_upload(csv_file)
    _session.log(question="[CSV upload]", agent="anomaly_alert", answer=alert)
    return alert


def new_session_ui():
    _session.reset()
    return "New session started. Contradiction checks and the summary now start fresh."


def session_summary_ui():
    return generate_session_summary(_session)


NAVY = "#0f2d52"
TEAL = "#0e7c7b"
PURPLE = "#6d4aa8"

THEME = gr.themes.Soft(
    primary_hue="teal",
    secondary_hue="slate",
    font=gr.themes.GoogleFont("Inter"),
)

CUSTOM_CSS = f"""
.gradio-container {{
    max-width: 1080px !important;
    margin: auto !important;
    background: linear-gradient(180deg, #f4f7fb 0%, #eef2f8 100%);
}}

#header-block {{
    background: linear-gradient(120deg, {NAVY} 0%, #1b4d6b 55%, {TEAL} 100%);
    border-radius: 18px;
    padding: 2rem 1.75rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 28px rgba(15, 45, 82, 0.22);
    text-align: center;
}}
#header-block h1 {{
    color: #ffffff !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    margin-bottom: 0.35rem !important;
}}
#header-block p {{ color: rgba(255,255,255,0.82) !important; margin: 0 !important; }}

.section-card {{
    background: #ffffff;
    border-radius: 14px;
    padding: 1.1rem 1.5rem 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 2px 12px rgba(15, 23, 42, 0.07);
    border-left: 4px solid {NAVY};
}}
.section-card-result {{ border-left-color: {TEAL}; }}
.section-card-session {{ border-left-color: {PURPLE}; }}

.section-title {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1.05rem;
    font-weight: 700;
    color: {NAVY};
    margin-bottom: 0.85rem;
}}
.section-title .badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.7rem;
    height: 1.7rem;
    border-radius: 50%;
    background: {NAVY};
    color: #fff;
    font-size: 0.85rem;
    font-weight: 700;
    flex-shrink: 0;
}}
.section-card-result .section-title .badge {{ background: {TEAL}; }}
.section-card-session .section-title .badge {{ background: {PURPLE}; }}

.analyze-btn, .analyze-btn > button {{
    background: linear-gradient(120deg, {NAVY}, {TEAL}) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 14px rgba(14, 124, 123, 0.35) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}}
.analyze-btn:hover, .analyze-btn > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(14, 124, 123, 0.45) !important;
}}

.gr-group, .section-card {{ border: 1px solid rgba(15, 23, 42, 0.06); }}
"""


def section_title(number: str, text: str) -> str:
    return f'<div class="section-title"><span class="badge">{number}</span>{text}</div>'


with gr.Blocks(title="Finance Ops AI") as demo:
    with gr.Column(elem_id="header-block"):
        gr.Markdown("# Finance Ops Intelligence Network")
        gr.Markdown("Upload a financial report, ask a question in plain language, get a grounded and audited answer.")

    with gr.Group(elem_classes="section-card section-card-input"):
        gr.Markdown(section_title("1", "Upload &amp; Ask"))
        with gr.Row(equal_height=True):
            with gr.Column():
                csv_input = gr.File(label="Financial report (CSV)", file_types=[".csv"], type="filepath")
                upload_alert = gr.Textbox(label="Auto anomaly alert (on upload)", lines=3, interactive=False)
            with gr.Column():
                question = gr.Textbox(
                    label="Your question",
                    placeholder="e.g. Which month had the highest profit?",
                    lines=4,
                )
                submit = gr.Button("Analyze", variant="primary", size="lg", elem_classes="analyze-btn")

    with gr.Group(elem_classes="section-card section-card-result"):
        gr.Markdown(section_title("2", "Result"))
        with gr.Row(equal_height=True):
            with gr.Column():
                agent_used = gr.Textbox(label="Agent routed to", interactive=False)
                answer = gr.Textbox(label="Analysis", lines=10, interactive=False)
            with gr.Column():
                chart = gr.Image(label="Chart")

    with gr.Group(elem_classes="section-card section-card-session"):
        gr.Markdown(section_title("3", "Session"))
        with gr.Row():
            summary_btn = gr.Button("Session Summary")
            new_session_btn = gr.Button("New Session", variant="stop")
        session_panel = gr.Textbox(label="Session", lines=6, interactive=False, show_label=False)

    with gr.Accordion("Trajectory audit (step-by-step log)", open=False):
        trajectory_log = gr.Textbox(label="Steps", lines=10, interactive=False, show_label=False)

    csv_input.upload(fn=check_on_upload_ui, inputs=[csv_input], outputs=[upload_alert])

    submit.click(
        fn=run_pipeline_ui,
        inputs=[csv_input, question],
        outputs=[agent_used, answer, chart, trajectory_log],
    )

    summary_btn.click(fn=session_summary_ui, outputs=[session_panel])
    new_session_btn.click(fn=new_session_ui, outputs=[session_panel])


if __name__ == "__main__":
    import os

    from tools.visualizer import CHART_DIR

    demo.launch(allowed_paths=[os.path.abspath(CHART_DIR)], theme=THEME, css=CUSTOM_CSS)
