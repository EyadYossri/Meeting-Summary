import streamlit as st
import os

st.title("🎥 Meeting Summarizer AI")

uploaded_file = st.file_uploader("Upload Video", type=["mp4"])
sender_email = st.text_input("Sender Email")
sender_password = st.text_input("Password", type="password")
receiver_email = st.text_input("Receiver Email")

if st.button("Start"):
    st.info("Pipeline coming next")