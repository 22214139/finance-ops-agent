"""Entry point: launches the Finance Ops Gradio app."""
import os

from tools.visualizer import CHART_DIR
from ui.app import CUSTOM_CSS, THEME, demo

if __name__ == "__main__":
    # Gradio only serves files it created itself unless the directory is allow-listed;
    # chart PNGs are written directly by matplotlib, so without this the <Image> output
    # silently fails to load.
    demo.launch(allowed_paths=[os.path.abspath(CHART_DIR)], theme=THEME, css=CUSTOM_CSS)
