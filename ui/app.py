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


THEME = gr.themes.Soft(primary_hue="blue", secondary_hue="slate")

CUSTOM_CSS = """
.gradio-container { max-width: 1080px !important; margin: auto !important; }
#header-block { text-align: center; }
#header-block h1 { margin-bottom: 0.25rem; }
"""

with gr.Blocks(title="Finance Ops AI") as demo:
    with gr.Column(elem_id="header-block"):
        gr.Markdown("# Finance Ops Intelligence Network")
        gr.Markdown("Upload a financial report, ask a question in plain language, get a grounded and audited answer.")

    with gr.Group():
        gr.Markdown("### 1 · Upload & Ask")
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
                submit = gr.Button("Analyze", variant="primary", size="lg")

    with gr.Group():
        gr.Markdown("### 2 · Result")
        with gr.Row(equal_height=True):
            with gr.Column():
                agent_used = gr.Textbox(label="Agent routed to", interactive=False)
                answer = gr.Textbox(label="Analysis", lines=10, interactive=False)
            with gr.Column():
                chart = gr.Image(label="Chart")

    with gr.Group():
        gr.Markdown("### 3 · Session")
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
