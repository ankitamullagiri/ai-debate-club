import html
from pathlib import Path

import gradio as gr

from arcade.debate import debater_turn, judge_debate

MODELS = [
    "google/gemma-3-27b-it",
    "mistralai/mistral-small-3.2-24b-instruct",
    "anthropic/claude-haiku-5.5",
    "openai/gpt-4o-mini",
]
ROUNDS = 3

CSS_PATH = Path(__file__).parent / "app.css"


# ---------- Text shown in the UI ----------

HEADER_HTML = """
<div id="hero">
  <h1>AI Debate <span>Club</span></h1>
  <p>Two AIs argue. A third one judges.</p>
</div>
"""

EMPTY_STATE_HTML = """
<div class="empty-state">
  <div class="empty-icon">🎙️</div>
  <h3>The floor is open</h3>
  <p>Pick a topic and your three models, then press <b>Start debate</b>.
  Arguments stream in here, round by round.</p>
  <div class="legend"><span class="pro">● PRO</span><span class="con">● CON</span></div>
</div>
"""

VERDICT_WAITING_HTML = (
    '<div class="verdict-waiting">⚖️ The judge\'s decision will appear here '
    "once the debate ends.</div>"
)


def status_html(text: str) -> str:
    return f'<div class="status"><span class="pulse"></span>{text}</div>'


def bubble_content(side: str, round_num: int, argument: str) -> str:
    tag = f'<span class="speaker {side.lower()}">{side} <span class="round">· Round {round_num}</span></span>'
    return f"{tag}\n\n{argument}"


def verdict_html(verdict: dict) -> str:
    winner = str(verdict["winner"]).upper()
    pro_class = "score pro winner" if winner == "PRO" else "score pro"
    con_class = "score con winner" if winner == "CON" else "score con"
    reason = html.escape(str(verdict["reason"]))
    return f"""
<div class="kicker">Judge's verdict</div>
<h2>🏆 {html.escape(winner)} wins</h2>
<div class="scores">
  <div class="{pro_class}">
    <span class="side">PRO</span>
    <span class="value">{html.escape(str(verdict["pro_score"]))}</span><span class="out-of"> / 10</span>
  </div>
  <div class="{con_class}">
    <span class="side">CON</span>
    <span class="value">{html.escape(str(verdict["con_score"]))}</span><span class="out-of"> / 10</span>
  </div>
</div>
<p class="reason">{reason}</p>
"""


# ---------- Debate logic (unchanged flow: stream each turn, then judge) ----------

def debate(topic: str, pro_model: str, con_model: str, judge_model: str):
    transcript = []
    chat = []
    for round_num in range(1, ROUNDS + 1):
        for side, model in [("PRO", pro_model), ("CON", con_model)]:
            argument = debater_turn(side, topic, transcript, model)
            transcript.append(f"{side} (round {round_num}): {argument}")

            role = "user" if side == "PRO" else "assistant"
            chat.append({"role": role, "content": bubble_content(side, round_num, argument)})
            yield chat, status_html("⏳ Debate in progress...")

    yield chat, status_html("⚖️ The judge is deliberating...")
    verdict = judge_debate(topic, transcript, judge_model)
    yield chat, verdict_html(verdict)


# ---------- Theme ----------

BG = "#0d0d17"
CARD = "#191927"
INPUT = "#12121e"
BORDER = "#2c2942"
TEXT = "#eceaf4"
MUTED = "#9995b0"
ACCENT = "#e9b77e"
ACCENT_HOVER = "#f2c894"


def both_modes(**colors: str) -> dict:
    """Use the same colour in light and dark mode, so the app always looks dark."""
    result = {}
    for name, value in colors.items():
        result[name] = value
        result[f"{name}_dark"] = value
    return result


theme = gr.themes.Base(
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
    radius_size="lg",
).set(
    **both_modes(
        body_background_fill=BG,
        body_text_color=TEXT,
        body_text_color_subdued=MUTED,
        background_fill_primary=CARD,
        background_fill_secondary=INPUT,
        block_background_fill=CARD,
        block_border_color=BORDER,
        block_label_background_fill=CARD,
        block_label_text_color=MUTED,
        block_title_text_color=MUTED,
        border_color_primary=BORDER,
        input_background_fill=INPUT,
        input_border_color=BORDER,
        input_border_color_focus=ACCENT,
        input_placeholder_color="#6b6785",
        color_accent_soft="rgba(233, 183, 126, 0.12)",
        button_primary_background_fill=ACCENT,
        button_primary_background_fill_hover=ACCENT_HOVER,
        button_primary_border_color=ACCENT,
        button_primary_text_color="#1a1408",
        block_shadow="none",
    ),
    color_accent=ACCENT,
    block_radius="18px",
    input_radius="12px",
    button_large_radius="14px",
)


# ---------- Layout ----------

with gr.Blocks(title="AI Debate Club") as demo:
    gr.HTML(HEADER_HTML)

    with gr.Column(elem_id="setup-card", elem_classes="adc-card"):
        topic = gr.Textbox(
            label="Debate topic",
            placeholder="e.g. Pineapple belongs on pizza",
            elem_id="topic",
        )
        with gr.Row(elem_id="model-row"):
            pro_model = gr.Dropdown(
                MODELS, value=MODELS[0], label="PRO model",
                allow_custom_value=True, min_width=200, elem_classes="model-pro",
            )
            con_model = gr.Dropdown(
                MODELS, value=MODELS[1], label="CON model",
                allow_custom_value=True, min_width=200, elem_classes="model-con",
            )
            judge_model = gr.Dropdown(
                MODELS, value=MODELS[2], label="Judge model",
                allow_custom_value=True, min_width=200, elem_classes="model-judge",
            )
        start = gr.Button("Start debate", variant="primary", size="lg", elem_id="start-btn")

    gr.HTML('<div class="section-title">Debate arena</div>')
    chat = gr.Chatbot(
        show_label=False,
        height=520,
        placeholder=EMPTY_STATE_HTML,
        elem_id="arena",
    )

    gr.HTML('<div class="section-title">Verdict</div>')
    with gr.Column(elem_classes="adc-card"):
        verdict = gr.Markdown(VERDICT_WAITING_HTML, elem_id="verdict")

    start.click(
        debate,
        inputs=[topic, pro_model, con_model, judge_model],
        outputs=[chat, verdict],
    )

if __name__ == "__main__":
    demo.launch(theme=theme, css_paths=CSS_PATH)
