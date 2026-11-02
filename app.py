"""Streamlit chat UI. Run: streamlit run app.py  (API must be running)"""
import uuid
import requests
import pandas as pd
import streamlit as st

API_URL = "http://localhost:8000/ask"

st.title("AI SQL Agent")
if "sid" not in st.session_state:
    st.session_state.sid = str(uuid.uuid4())  # one memory thread per browser session
    st.session_state.chat = []

# replay chat
for m in st.session_state.chat:
    with st.chat_message(m["role"]):
        st.write(m["text"])
        if m.get("sql"):
            st.code(m["sql"], language="sql")
        if m.get("rows"):
            st.dataframe(pd.DataFrame(m["rows"], columns=m["columns"]))

if q := st.chat_input("Ask about your data..."):
    st.session_state.chat.append({"role": "user", "text": q})
    resp = requests.post(API_URL, json={"question": q, "session_id": st.session_state.sid})
    if resp.status_code != 200:  # show backend error instead of crashing
        st.error(f"Backend error: {resp.text}")
        st.stop()
    r = resp.json()
    st.session_state.chat.append({"role": "assistant", "text": r["answer"],
                                  "sql": r["sql"], "rows": r["rows"], "columns": r["columns"]})
    st.rerun()
