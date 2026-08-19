"""Gradio UI for the Finance Ops Intelligence Network."""
import gradio as gr

from core.memory import Memory
from core.router import run_pipeline

_memory = Memory()


def run_pipeline_ui(csv_file, question):
    result = run_pipeline(question, filepath=csv_file, memory=_memory)
    return result.agent, result.answer, result.chart_path, result.trajectory.summary()


with gr.Blocks(title="Finance Ops AI") as demo:
    gr.Markdown("# Finance Ops Intelligence Network")

    with gr.Row():
        with gr.Column():
            csv_input = gr.File(label="Upload CSV", file_types=[".csv"], type="filepath")
            question = gr.Textbox(label="Ask a question")
            submit = gr.Button("Analyze")

        with gr.Column():
            agent_used = gr.Textbox(label="Agent Routed To")
            answer = gr.Textbox(label="Analysis", lines=10)
            chart = gr.Image(label="Chart")

    with gr.Accordion("Trajectory Audit", open=False):
        trajectory_log = gr.Textbox(label="Step-by-step audit log", lines=10)

    submit.click(
        fn=run_pipeline_ui,
        inputs=[csv_input, question],
        outputs=[agent_used, answer, chart, trajectory_log],
    )


if __name__ == "__main__":
    demo.launch()
