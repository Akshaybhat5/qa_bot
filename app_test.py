

import streamlit as st
from openai import OpenAI
import os
from azure.storage.blob import BlobServiceClient
import json
import uuid
from datetime import datetime
import ast 
from dotenv import load_dotenv
load_dotenv()

# ---- Azure Blob Config ----
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_BLOB_CONTAINER = os.getenv("AZURE_BLOB_CONTAINER")

for key, default in {
    "consent_given": False,
    "conversation": [],
    "question_step": 1,
    "questions_asked_count": 0,
    "session_complete": False,
    "saved_to_blob": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def save_session_to_blob(session_state):
    chat_data = {
        "session_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "consent_given": session_state.consent_given,
        "questions_asked_count": session_state.questions_asked_count,
        "conversation": session_state.conversation,
    }
    filename = f"roleclarity_{chat_data['session_id']}.json"
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=AZURE_BLOB_CONTAINER, blob=filename)
    blob_client.upload_blob(json.dumps(chat_data, indent=2), overwrite=True)
    return filename

# ---- OpenAI Config ----
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
ROLE_CLARITY_QUESTION_BANK = [
    "Can you describe your primary responsibilities in your current role?",
    "How well do you feel your role aligns with your job description?",
    "Are there tasks you perform regularly that are not clearly outlined in your role description?",
    "Have you ever felt unclear about your specific job responsibilities?",
    "What could your direct leader or organisation do to improve your role clarity?",
    # ...add more as needed!
]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_llm_followup_question(conversation_history, user_response):
    question_step = st.session_state.get("question_step", 1)
    conversation = "\n".join([f"{who}: {msg}" for who, msg in conversation_history])

    prompt = f"""
You are a workplace psychologist conducting a structured AI-led interview on **role clarity**.

Follow this strict 7-step flow:

1️⃣ Ask how the employee experiences role clarity or lack of it.  
2️⃣ Ask a follow-up. If vague (<10 words or includes “not sure”, “maybe”, etc.), gently ask for clarification or an example. If detailed, ask what helped or made it harder.  
3️⃣ Ask what they believe are the *main reasons* for their level of role clarity.  
4️⃣ Ask what *specific actions* (by manager, team, org) could improve their role clarity.  
5️⃣ Ask if they have *any other suggestions* to improve role clarity for themselves or others.  
6️⃣ Ask how improved role clarity would help them in their work or wellbeing.
7️⃣ Ask before we finish, is there anything else you’d like to add about your experience of role clarity or how it could be improved?

You are on **Step {question_step}**.

Conversation so far:
{conversation}

Their last response:
"{user_response}"

Return exactly two lines:
1. A short, empathetic sentence that acknowledges the response.
2. The next appropriate question for Step {question_step}.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=100,
        temperature=0.7,
    )

    reply = response.choices[0].message.content.strip()
    st.session_state.question_step += 1
    return reply

# ---- App Title and Consent ----
st.title("Role Clarity AI Agent Chatbot")
st.markdown("Talk to a virtual workplace psychologist about your experience of role clarity.")

if not st.session_state.consent_given:
    st.info("""
    **Consent Required**  
    This interview helps us understand your experience of role clarity. It's confidential and anonymous.  
    Do you agree to proceed?
    """)
    with st.form("consent_form", clear_on_submit=True):
        consent_input = st.text_input("Type 'yes' to provide consent and begin.")
        submitted = st.form_submit_button("Submit")
        if submitted and consent_input.strip().lower() == "yes":
            st.session_state.consent_given = True
            st.session_state.conversation = []
            st.session_state.questions_asked_count = 0
            st.session_state.session_complete = False
            st.session_state.saved_to_blob = False
            st.session_state.question_step = 1
            st.session_state.conversation.append(("Mibo", "Hi, I’m your virtual workplace psychologist. Let’s begin."))
            with st.spinner("Loading your first question..."):
                first_q = get_llm_followup_question(st.session_state.conversation, "")
                st.session_state.conversation.append(("Mibo", first_q))
            st.session_state.questions_asked_count = 1
            st.success("Thank you for your consent.")
            st.rerun()
        elif submitted:
            st.warning("You need to type 'yes' to begin.")
    st.stop()

# ---- Chat Display ----
for speaker, text in st.session_state.conversation:
    with st.chat_message("user" if speaker == "Employee" else "assistant"):
        st.markdown(f"**{speaker}:** {text}")

# ---- Chat Input ----
def proceed_conversation(user_input):
    if st.session_state.session_complete:
        return
    st.session_state.conversation.append(("Employee", user_input))

    if st.session_state.questions_asked_count >= 7:
        st.session_state.conversation.append(("Mibo", "Thank you for your responses. The interview is now complete."))
        st.session_state.session_complete = True
        return

    next_q = get_llm_followup_question(st.session_state.conversation, user_input)
    st.session_state.conversation.append(("Mibo", next_q))
    st.session_state.questions_asked_count += 1

with st.form("chat_input_form", clear_on_submit=True):
    if not st.session_state.session_complete:
        user_input = st.text_input("Your response:")
        submitted = st.form_submit_button("Send")
        if submitted and user_input.strip():
            proceed_conversation(user_input)
            st.rerun()
    else:
        st.info("Session complete. Thank you for participating!")
        submit_and_restart = st.form_submit_button("Submit & Start New Session")
        if submit_and_restart:
            if not st.session_state.saved_to_blob:
                try:
                    filename = save_session_to_blob(st.session_state)
                    st.success(f"Session saved as `{filename}`.")
                    st.session_state.saved_to_blob = True
                except Exception as e:
                    st.error(f"Error saving session: {e}")
            for key in [
                "consent_given", "conversation", "question_step",
                "questions_asked_count", "session_complete", "saved_to_blob"
            ]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()