import streamlit as st
import requests
import json
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("🎥 Meeting Summarizer AI")

uploaded_file = st.file_uploader("Upload Meeting Video", type=["mp4", "mov", "avi"])

receiver_email = st.text_input("Enter receiver email:")

if st.button("Start Summarization"):

    if uploaded_file is None:
        st.error("Please upload a video file.")
    elif not receiver_email:
        st.error("Please fill in all email fields.")
    else:
        progress = st.progress(0)
        status = st.empty()
        summary_box = st.empty()
        summary_text = ""

        try:
            with requests.post(
                f"{BACKEND_URL}/summarize",
                files={"video": (uploaded_file.name, uploaded_file, uploaded_file.type)},
                data={
                    "receiver_email": receiver_email,
                },
                stream=True,
                timeout=600,
            ) as response:
                response.raise_for_status()

                for raw_line in response.iter_lines():
                    if not raw_line:
                        continue

                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                    if not line.startswith("data:"):
                        continue

                    event = json.loads(line[len("data:"):].strip())

                    if event["type"] == "progress":
                        progress.progress(event["value"])
                        status.text(event["status"])

                    elif event["type"] == "token":
                        summary_text += event["value"]
                        summary_box.markdown(
                            f"<div dir='rtl' style='text-align: right;'>\n\n{summary_text}\n\n</div>", 
                            unsafe_allow_html=True
                        )

                    elif event["type"] == "done":
                        st.success("تم الانتهاء بنجاح!")
                        st.markdown(
                            "<h3 style='text-align: right; direction: rtl;'>📋 الملخص النهائي</h3>", 
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f"<div dir='rtl' style='text-align: right;'>\n\n{event['summary']}\n\n</div>", 
                            unsafe_allow_html=True
                        )

                    elif event["type"] == "error":
                        st.error(f"Error: {event['message']}")
                        break

        except requests.exceptions.ConnectionError:
            st.error(
                f"Cannot connect to the backend at `{BACKEND_URL}`.\n\n"
                "Make sure the FastAPI service is running and `BACKEND_URL` is set correctly."
            )
        except Exception as e:
            st.error(f"Unexpected error: {e}")
