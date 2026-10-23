import streamlit as st
import uuid
from config import MAX_HISTORY_MESSAGES
from retrivel import search_query
from llm import generate_answer,rewrite_query
from insert import insert

from db import (
    create_session,
    save_message,
    get_chat_history,
    get_all_sessions,
    update_session_name,
    get_recent_chat_context
)
# PAGE CONFIG
st.set_page_config(page_title="RAG Chat", layout="wide")

st.title("💬 Document RAG Assistant")

# INIT SESSION (FIXED)
if "session_id" not in st.session_state:
    sessions = get_all_sessions()

    if sessions:
        st.session_state.session_id = sessions[0]["id"]
    else:
        st.session_state.session_id = None

# SIDEBAR
st.sidebar.title("🗂️ Chat Sessions")

#  New Chat
if st.sidebar.button("➕ New Chat"):
    new_id = str(uuid.uuid4())
    st.session_state.session_id = new_id
    create_session(new_id, "New Chat")
    st.rerun()

#  Refresh Documents
if st.sidebar.button("🔄 Refresh Documents"):
    with st.spinner("📄 Re-indexing documents..."):
        insert()
    st.sidebar.success("✅ Documents refreshed!")

# Load sessions
sessions = get_all_sessions()

for s in sessions:
    session_id = s["id"]
    session_name = s["name"]

    if st.sidebar.button(
        session_name,
        key=session_id,
        type="primary" if session_id == st.session_state.session_id else "secondary"
    ):
        st.session_state.session_id = session_id
        st.rerun()

# NO SESSION HANDLING
if not st.session_state.session_id:
    st.info("👉 Click 'New Chat' to start a conversation")
    st.stop()

# LOAD CHAT HISTORY (UI)
history = get_chat_history(st.session_state.session_id, limit=50)

for role, msg in history:
    with st.chat_message(role):
        st.markdown(msg)

# CHAT INPUT
user_input = st.chat_input("Ask something about your documents...")

if user_input:

    # Show user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Save user message
    save_message(st.session_state.session_id, "user", user_input)

    #  Rename session on first message
    if len(history) == 0:
        update_session_name(
            st.session_state.session_id,
            user_input[:50]
        )

    #  GET CHAT CONTEXT FIRST
    chat_context = get_recent_chat_context(
        st.session_state.session_id,
        limit=MAX_HISTORY_MESSAGES
    )

    # REWRITE QUERY
    rewritten_query = rewrite_query(user_input, chat_context)

    # RETRIEVAL (FIXED)
    results = search_query(rewritten_query)

    # LLM RESPONSE
    answer = generate_answer(rewritten_query, results)    
    # Show assistant message
    with st.chat_message("assistant"):
        st.markdown(answer)

        with st.expander("📚 Sources"):
            for i, r in enumerate(results, 1):
                st.markdown(f"**{i}. {r['source_file']} (chunk {r['chunk_id']})**")
                st.write(r["content"][:300])
                st.markdown("---")

    # Save assistant message
    save_message(st.session_state.session_id, "assistant", answer)

    # Refresh UI
    st.rerun()