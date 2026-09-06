"""
app.py
------
Main Streamlit application — the entry point for the AI Automation Assistant.

Responsibilities:
  - Render the browser UI (input area, buttons, results panels)
  - Orchestrate the flow: user input → AI response → code execution → display
  - Maintain conversation history in Streamlit session state for multi-turn context

Fix note (button bug):
  The previous version used a `processing` boolean in session state to disable
  buttons, and called st.rerun() inside the Clear handler before resetting that
  flag. This caused the buttons to stay permanently disabled after one Clear.

  The fix:
    1. Remove the `processing` flag entirely. st.spinner() provides the "busy"
       visual feedback without needing to touch button state.
    2. Use a `input_key_counter` integer in session state. Incrementing it changes
       the `key=` argument of st.text_area, which forces Streamlit to mount a fresh
       widget — effectively clearing the input without needing st.rerun().
    3. All state mutations (clear, save results) happen BEFORE any st.rerun() call
       so there is no window where a flag can be left in an inconsistent state.
"""

import streamlit as st
from ai_handler import get_ai_response, parse_response
from code_executor import execute_code

# ---------------------------------------------------------------------------
# Page configuration — must be the first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Automation Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main { background-color: #0f1117; }

    .section-panel {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 16px;
        border-left: 4px solid #4f8ef7;
    }
    .section-panel.code-panel   { border-left-color: #f7c948; }
    .section-panel.output-panel { border-left-color: #4caf82; }
    .section-panel.error-panel  { border-left-color: #e05c5c; }
    .section-panel.blocked-panel{ border-left-color: #e09c30; }

    .section-title {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 8px;
        opacity: 0.75;
    }

    .user-bubble {
        background-color: #2a2d3e;
        border-radius: 12px 12px 2px 12px;
        padding: 10px 14px;
        margin: 6px 0 6px 40px;
        font-size: 0.95rem;
    }
    .assistant-bubble {
        background-color: #1a1d2e;
        border-radius: 12px 12px 12px 2px;
        padding: 10px 14px;
        margin: 6px 40px 6px 0;
        font-size: 0.95rem;
        border-left: 3px solid #4f8ef7;
    }

    footer { visibility: hidden; }
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "results" not in st.session_state:
    st.session_state.results = None

# Integer counter used as the text_area key.
# Incrementing it forces Streamlit to mount a brand-new widget (empty input)
# without needing st.rerun() and without touching button disabled state.
if "input_key_counter" not in st.session_state:
    st.session_state.input_key_counter = 0


# ---------------------------------------------------------------------------
# Helper: render result panels
# ---------------------------------------------------------------------------
def render_results(results: dict):
    """Render the four result panels: explanation, code, expected output, actual output."""

    parsed    = results["parsed"]
    execution = results["execution"]

    # --- Explanation panel ---
    if parsed["explanation"]:
        st.markdown(
            f'<div class="section-panel">'
            f'<div class="section-title">🧠 AI Explanation</div>'
            f'{parsed["explanation"]}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # --- Code panel ---
    if parsed["code"]:
        st.markdown(
            '<div class="section-panel code-panel">'
            '<div class="section-title">💻 Generated Code</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.code(parsed["code"], language="python")

    # --- Expected output panel ---
    if parsed["expected_output"]:
        st.markdown(
            f'<div class="section-panel">'
            f'<div class="section-title">📋 Expected Output (from AI)</div>'
            f'<pre style="margin:0;white-space:pre-wrap;">{parsed["expected_output"]}</pre>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # --- Execution result panel ---
    if parsed["code"] and execution:
        if execution["blocked"]:
            st.markdown(
                f'<div class="section-panel blocked-panel">'
                f'<div class="section-title">🚫 Execution Blocked</div>'
                f'{execution["message"]}'
                f'</div>',
                unsafe_allow_html=True,
            )
        elif execution["success"]:
            output_text = execution["stdout"] if execution["stdout"] else "(No output produced)"
            st.markdown(
                f'<div class="section-panel output-panel">'
                f'<div class="section-title">✅ Actual Execution Output</div>'
                f'<pre style="margin:0;white-space:pre-wrap;">{output_text}</pre>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            error_text  = execution["stderr"] if execution["stderr"] else execution["message"]
            stdout_text = execution["stdout"]

            if stdout_text:
                st.markdown(
                    f'<div class="section-panel output-panel">'
                    f'<div class="section-title">📤 Partial Output (before error)</div>'
                    f'<pre style="margin:0;white-space:pre-wrap;">{stdout_text}</pre>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<div class="section-panel error-panel">'
                f'<div class="section-title">❌ Execution Error</div>'
                f'<pre style="margin:0;white-space:pre-wrap;color:#ff8a80;">{error_text}</pre>'
                f'</div>',
                unsafe_allow_html=True,
            )

    elif parsed["code"] and not execution:
        st.info("Code generated but not yet executed.")


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
col1, col2 = st.columns([0.08, 0.92])
with col1:
    st.markdown("## 🤖")
with col2:
    st.markdown("## AI Automation Assistant")
    st.caption("Enter a coding task or paste code to analyze. The assistant will explain, generate, and run Python code.")

st.divider()

# ---------------------------------------------------------------------------
# Conversation history display
# ---------------------------------------------------------------------------
if st.session_state.conversation_history:
    st.markdown("### Conversation")
    for msg in st.session_state.conversation_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="user-bubble">👤 <strong>You:</strong> {msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            preview = msg["content"][:120].replace("\n", " ")
            st.markdown(
                f'<div class="assistant-bubble">🤖 <strong>Assistant:</strong> {preview}…</div>',
                unsafe_allow_html=True,
            )
    st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Current results display
# ---------------------------------------------------------------------------
if st.session_state.results:
    st.markdown("### Latest Response")
    render_results(st.session_state.results)
    st.divider()

# ---------------------------------------------------------------------------
# Input area
# ---------------------------------------------------------------------------
st.markdown("### Your Request")

# The key is a string built from the counter. When the counter increments,
# Streamlit treats this as a completely new widget and renders it empty.
# This is the correct Streamlit pattern for programmatic input clearing.
user_input = st.text_area(
    label="Type your task or paste your code here:",
    placeholder=(
        "Examples:\n"
        "  • Write a Python function that reverses a string\n"
        "  • What does this code do: [paste code]\n"
        "  • Generate a Fibonacci sequence up to 100\n"
        "  • Find the bug in this code: [paste buggy code]"
    ),
    height=160,
    key=f"user_input_area_{st.session_state.input_key_counter}",
    label_visibility="collapsed",
)

col_btn, col_clear, col_spacer = st.columns([0.15, 0.15, 0.70])

with col_btn:
    # Never set disabled= here. The spinner communicates "busy" state instead.
    run_clicked = st.button("▶ Run", type="primary", use_container_width=True)

with col_clear:
    clear_clicked = st.button("🗑 Clear", use_container_width=True)

# ---------------------------------------------------------------------------
# Clear handler
# ---------------------------------------------------------------------------
if clear_clicked:
    # 1. Wipe all display state
    st.session_state.conversation_history = []
    st.session_state.results = None
    # 2. Increment the counter — next render mounts a fresh, empty text_area
    st.session_state.input_key_counter += 1
    # 3. Rerun so the cleared state is reflected immediately.
    #    Buttons are NOT disabled, so this rerun is safe.
    st.rerun()

# ---------------------------------------------------------------------------
# Run handler
# ---------------------------------------------------------------------------
if run_clicked:
    if not user_input.strip():
        st.warning("Please enter a task or some code before clicking Run.")
    else:
        # Step 1: Call the Gemini API (spinner gives "busy" feedback)
        with st.spinner("Thinking…"):
            raw_response, error = get_ai_response(
                user_input.strip(),
                st.session_state.conversation_history,
            )

        if error:
            # Show error inline; no state mutation needed — buttons stay live
            st.error(f"**API Error:** {error}")
        else:
            # Step 2: Parse structured response
            parsed = parse_response(raw_response)

            # Step 3: Execute code if present
            execution_result = None
            if parsed["code"]:
                with st.spinner("Executing code…"):
                    execution_result = execute_code(parsed["code"])

            # Step 4: Commit all results to session state in one block
            #         before calling rerun, so nothing is lost mid-flight
            st.session_state.results = {
                "user_input": user_input.strip(),
                "parsed":     parsed,
                "execution":  execution_result,
            }

            # Step 5: Append to conversation history
            st.session_state.conversation_history.append(
                {"role": "user",      "content": user_input.strip()}
            )
            st.session_state.conversation_history.append(
                {"role": "assistant", "content": raw_response}
            )

            # Keep last 10 exchanges (20 messages) to stay within token limits
            if len(st.session_state.conversation_history) > 20:
                st.session_state.conversation_history = \
                    st.session_state.conversation_history[-20:]

            # Step 6: Rerun to render results at the top of the page.
            #         All state is already saved above, so rerun is safe.
            st.rerun()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("AI Automation Assistant · Powered by Gemini · Built with Streamlit")
