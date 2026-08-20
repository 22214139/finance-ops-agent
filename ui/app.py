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


with gr.Blocks(title="Finance Ops AI") as demo:
    gr.Markdown("# Finance Ops Intelligence Network")

    with gr.Row():
        with gr.Column():
            csv_input = gr.File(label="Upload CSV", file_types=[".csv"], type="filepath")
            upload_alert = gr.Textbox(label="Auto Anomaly Alert (on upload)", lines=3)
            question = gr.Textbox(label="Ask a question")
            submit = gr.Button("Analyze")

        with gr.Column():
            agent_used = gr.Textbox(label="Agent Routed To")
            answer = gr.Textbox(label="Analysis", lines=10)
            chart = gr.Image(label="Chart")

    with gr.Row():
        summary_btn = gr.Button("Session Summary")
        new_session_btn = gr.Button("New Session")

    session_panel = gr.Textbox(label="Session", lines=6)

    with gr.Accordion("Trajectory Audit", open=False):
        trajectory_log = gr.Textbox(label="Step-by-step audit log", lines=10)

    csv_input.upload(fn=check_on_upload_ui, inputs=[csv_input], outputs=[upload_alert])

    submit.click(
        fn=run_pipeline_ui,
        inputs=[csv_input, question],
        outputs=[agent_used, answer, chart, trajectory_log],
    )

    summary_btn.click(fn=session_summary_ui, outputs=[session_panel])
    new_session_btn.click(fn=new_session_ui, outputs=[session_panel])


if __name__ == "__main__":
    demo.launch()
