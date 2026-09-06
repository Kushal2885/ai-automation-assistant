import streamlit as st
from ai_handler import get_ai_response, parse_response
from code_executor import execute_code

st.set_page_config(
    page_title="AI Automation Assistant",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "results" not in st.session_state:
    st.session_state.results = None

# Incrementing this counter changes the text_area key, forcing Streamlit to
# mount a fresh empty widget — the correct pattern for programmatic clearing.
if "input_key_counter" not in st.session_state:
    st.session_state.input_key_counter = 0


def render_results(results: dict):
    """Render the explanation, code, expected output, and execution output panels."""
    parsed    = results["parsed"]
    execution = results["execution"]

    if parsed["explanation"]:
        st.markdown(
            f'<div class="section-panel">'
            f'<div class="section-title">AI Explanation</div>'
            f'{parsed["explanation"]}'
            f'</div>',
            unsafe_allow_html=True,
        )

    if parsed["code"]:
        st.markdown(
            '<div class="section-panel code-panel">'
            '<div class="section-title">Generated Code</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.code(parsed["code"], language="python")

    if parsed["expected_output"]:
        st.markdown(
            f'<div class="section-panel">'
            f'<div class="section-title">Expected Output (from AI)</div>'
            f'<pre style="margin:0;white-space:pre-wrap;">{parsed["expected_output"]}</pre>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if parsed["code"] and execution:
        if execution["blocked"]:
            st.markdown(
                f'<div class="section-panel blocked-panel">'
                f'<div class="section-title">Execution Blocked</div>'
                f'{execution["message"]}'
                f'</div>',
                unsafe_allow_html=True,
            )
        elif execution["success"]:
            output_text = execution["stdout"] if execution["stdout"] else "(No output produced)"
            st.markdown(
                f'<div class="section-panel output-panel">'
                f'<div class="section-title">Actual Execution Output</div>'
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
                    f'<div class="section-title">Partial Output (before error)</div>'
                    f'<pre style="margin:0;white-space:pre-wrap;">{stdout_text}</pre>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<div class="section-panel error-panel">'
                f'<div class="section-title">Execution Error</div>'
                f'<pre style="margin:0;white-space:pre-wrap;color:#ff8a80;">{error_text}</pre>'
                f'</div>',
                unsafe_allow_html=True,
            )

    elif parsed["code"] and not execution:
        st.info("Code generated but not yet executed.")


st.markdown("## AI Automation Assistant")
st.caption("Enter a coding task or paste code to analyze. The assistant will explain, generate, and run Python code.")

st.divider()

if st.session_state.conversation_history:
    st.markdown("### Conversation")
    for msg in st.session_state.conversation_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="user-bubble"><strong>You:</strong> {msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            preview = msg["content"][:120].replace("\n", " ")
            st.markdown(
                f'<div class="assistant-bubble"><strong>Assistant:</strong> {preview}…</div>',
                unsafe_allow_html=True,
            )
    st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.results:
    st.markdown("### Latest Response")
    render_results(st.session_state.results)
    st.divider()

st.markdown("### Your Request")

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
    run_clicked = st.button("Run", type="primary", use_container_width=True)

with col_clear:
    clear_clicked = st.button("Clear", use_container_width=True)

if clear_clicked:
    st.session_state.conversation_history = []
    st.session_state.results = None
    st.session_state.input_key_counter += 1
    st.rerun()

if run_clicked:
    if not user_input.strip():
        st.warning("Please enter a task or some code before clicking Run.")
    else:
        with st.spinner("Thinking…"):
            raw_response, error = get_ai_response(
                user_input.strip(),
                st.session_state.conversation_history,
            )

        if error:
            st.error(f"**API Error:** {error}")
        else:
            parsed = parse_response(raw_response)

            execution_result = None
            if parsed["code"]:
                with st.spinner("Executing code…"):
                    execution_result = execute_code(parsed["code"])

            st.session_state.results = {
                "user_input": user_input.strip(),
                "parsed":     parsed,
                "execution":  execution_result,
            }

            st.session_state.conversation_history.append(
                {"role": "user",      "content": user_input.strip()}
            )
            st.session_state.conversation_history.append(
                {"role": "assistant", "content": raw_response}
            )

            # Keep last 10 exchanges to stay within token limits
            if len(st.session_state.conversation_history) > 20:
                st.session_state.conversation_history = \
                    st.session_state.conversation_history[-20:]

            st.rerun()

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("AI Automation Assistant · Powered by Gemini · Built with Streamlit")
