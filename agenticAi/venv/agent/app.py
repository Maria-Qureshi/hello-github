"""
app.py
------
Streamlit UI for the Pathfinder career assistant.
Run with: streamlit run app.py
"""

from click import style
import streamlit as st
from agent import (
    init_model,
    load_memory,
    save_memory,
    clear_memory,
    start_chat_session,
    send_message,
)

# ── Page Config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Pathfinder",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────


st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&family=Nunito:wght@400;700&display=swap');

  /* ── Base ── */
  html, body, [class*="css"] {
    font-family: 'Quicksand', sans-serif;
    background-color: #FAFAFA; /* Very light clean grey/white */
    color: #4A4A4A;
  }

  /* ── Hide default Streamlit chrome ── */
  #MainMenu, footer, header { visibility: hidden; }

  /* ── Main container ── */
  .block-container {
    padding: 2rem 2rem 6rem 2rem;
    max-width: 700px;
  }

  /* ── App header ── */
  .app-header {
    text-align: center;
    margin-bottom: 2.5rem;
    padding: 1.5rem;
    background: #FFFFFF;
    border-radius: 24px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.03);
  }
  .app-header h1 {
    font-family: 'Quicksand', sans-serif;
    font-weight: 700;
    font-size: 2.2rem;
    color: #FF8A8A; /* Soft Coral */
    margin: 0;
  }
  .app-header p {
    font-size: 0.9rem;
    color: #A0A0A0;
    margin-top: 5px;
    font-weight: 500;
    letter-spacing: 0.5px;
  }

  /* ── Chat bubbles ── */
  .chat-row {
    display: flex;
    margin-bottom: 1.5rem;
    gap: 12px;
    animation: fadeIn 0.4s ease-out;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .chat-row.user { flex-direction: row-reverse; }

  .avatar {
    width: 38px;
    height: 38px;
    border-radius: 14px; /* Squircle */
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    flex-shrink: 0;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
  }
  .avatar.user-av  { background: #FFE5E5; color: #FF8A8A; } /* Soft Pink */
  .avatar.bot-av   { background: #E5F9F6; color: #5BC0BE; } /* Soft Mint */

  .bubble {
    max-width: 75%;
    padding: 1rem 1.2rem;
    border-radius: 20px;
    font-size: 0.95rem;
    line-height: 1.5;
    font-family: 'Nunito', sans-serif;
    box-shadow: 0 4px 15px rgba(0,0,0,0.02);
  }
  .bubble.user-bubble {
    background: #FF8A8A;
    color: #FFFFFF;
    border-bottom-right-radius: 4px;
  }
  .bubble.bot-bubble {
    background: #FFFFFF;
    color: #4A4A4A;
    border: 1px solid #F0F0F0;
    border-bottom-left-radius: 4px;
  }

  /* ── Empty state ── */
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 30px;
    border: 2px dashed #FFE5E5;
  }
  .empty-state .icon { font-size: 3.5rem; margin-bottom: 1rem; }
  .empty-state h3 {
    font-size: 1.5rem;
    color: #4A4A4A;
    margin-bottom: 0.5rem;
  }

  /* ── Prompt chips ── */
  .chips { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-top: 1.5rem; }
  .chip {
    background: #FDF2F2;
    border: 1px solid #FFE5E5;
    border-radius: 12px;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    color: #FF8A8A;
    font-weight: 600;
    transition: all 0.2s;
  }
  .chip:hover {
    background: #FF8A8A;
    color: white;
    transform: translateY(-2px);
  }

  /* ── Chat input override ── */
  .stChatInput > div {
    border-radius: 20px !important;
    border: 2px solid #F0F0F0 !important;
    background: #fff !important;
    padding: 5px !important;
  }
  
  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #F0F0F0;
  }
  
  /* Make buttons look pill-shaped and cute */
  button[kind="secondary"] {
    border-radius: 20px !important;
    border: 1px solid #FFE5E5 !important;
    color: #FF8A8A !important;
    background: white !important;
  }
  button[kind="secondary"]:hover {
    background: #FF8A8A !important;
    color: white !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Session State Init ─────────────────────────────────────────────────────────

def init_session():
    """Initialize all session state variables on first load."""
    if "initialized" not in st.session_state:
        model = init_model()
        if model is None:
            st.session_state.error = "⚠️ Could not initialize model. Check your API_KEY in .env"
            st.session_state.initialized = False
            return

        history = load_memory()
        chat    = start_chat_session(model, history)

        st.session_state.model          = model
        st.session_state.chat           = chat
        st.session_state.display_msgs   = _history_to_display(history)
        st.session_state.error          = None
        st.session_state.initialized    = True


def _history_to_display(history: list[dict]) -> list[dict]:
    """Convert raw memory format to display-friendly dicts."""
    display = []
    for entry in history:
        role    = "user" if entry.get("role") == "user" else "assistant"
        parts   = entry.get("parts", [])
        content = " ".join(parts) if isinstance(parts, list) else str(parts)
        if content.strip():
            display.append({"role": role, "content": content})
    return display


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("### 🧭 Pathfinder")
        st.markdown("<p style='font-size:0.78rem;color:#888;'>Your career strategy assistant</p>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        st.markdown("**Session**")
        msg_count = len(st.session_state.get("display_msgs", []))
        st.markdown(f"<p style='font-size:0.82rem;color:#666;'>💬 {msg_count} message{'s' if msg_count != 1 else ''} in memory</p>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🗑️ Clear Memory"):
            if clear_memory():
                model = st.session_state.model
                st.session_state.chat         = start_chat_session(model, [])
                st.session_state.display_msgs = []
                st.toast("Memory cleared.", icon="✅")
                st.rerun()
            else:
                st.toast("Failed to clear memory.", icon="❌")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
        <p style='font-size:0.75rem;color:#aaa;line-height:1.6;'>
        Pathfinder helps you build deliberate career paths,
        identify skill gaps, and make high-leverage decisions.
        </p>
        """, unsafe_allow_html=True)


# ── Chat UI ────────────────────────────────────────────────────────────────────

STARTER_PROMPTS = [
    "What skills should I focus on this year?",
    "I want to transition into cybersecurity",
    "How do I stand out as a fresh grad?",
    "Review my career plan",
]

def render_chat():
    """Render the main chat area."""
    st.markdown("""
    <div class="app-header">
      <div>
        <h1>🧭 Pathfinder</h1>
        <p>Career Strategy Assistant</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    messages = st.session_state.get("display_msgs", [])

    # ── Empty state ──
    if not messages:
        chips_html = "".join(f'<div class="chip">{p}</div>' for p in STARTER_PROMPTS)
        st.markdown(f"""
        <div class="empty-state">
          <div class="icon">🗺️</div>
          <h3>Where do you want to go?</h3>
          <p>Ask me anything about your career path, skills, or next move.</p>
          <div class="chips">{chips_html}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── Render chat history ──
        for msg in messages:
            is_user = msg["role"] == "user"
            row_cls    = "user"         if is_user else "bot"
            bubble_cls = "user-bubble"  if is_user else "bot-bubble"
            av_cls     = "user-av"      if is_user else "bot-av"
            av_icon    = "👤"           if is_user else "🧭"
            content    = msg["content"].replace("\n", "<br>")

            st.markdown(f"""
            <div class="chat-row {row_cls}">
              <div class="avatar {av_cls}">{av_icon}</div>
              <div class="bubble {bubble_cls}">{content}</div>
            </div>
            """, unsafe_allow_html=True)


# ── Input Handling ─────────────────────────────────────────────────────────────

def handle_input():
    """Render the chat input and process user messages."""
    user_input = st.chat_input("Ask Pathfinder anything about your career…")
    if not user_input or not user_input.strip():
        return

    # Append user message immediately
    st.session_state.display_msgs.append({"role": "user", "content": user_input.strip()})

    # Get model response
    with st.spinner("Thinking…"):
        reply = send_message(st.session_state.chat, user_input)

    if reply:
        st.session_state.display_msgs.append({"role": "assistant", "content": reply})
        save_memory(st.session_state.chat.history)
    else:
        st.session_state.display_msgs.append({
            "role": "assistant",
            "content": "⚠️ Something went wrong. Check your connection or API quota and try again."
        })

    st.rerun()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    init_session()

    if not st.session_state.get("initialized"):
        st.error(st.session_state.get("error", "Initialization failed."))
        st.stop()

    render_sidebar()
    render_chat()
    handle_input()


if __name__ == "__main__":
    main()