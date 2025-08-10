# 📌 Role Clarity AI Chatbot

An **ISO 27001–compliant** Streamlit application that conducts structured interviews on *role clarity*, integrates with **Azure OpenAI**, and stores responses securely in **Azure Blob Storage**.

---

## 🚀 Features

- **Structured 7-Step Interview** workflow on role clarity
- Powered by **Azure OpenAI ChatCompletion API**
- Secure storage of anonymized chat sessions in **Azure Blob Storage**
- Modular, ISO-friendly code structure for easy audits
- `.env` configuration (no secrets in code)
- Fully deployable on **Azure App Service**

---

## 📂 Project Structure

```plaintext
role-clarity-chatbot/
│
├── app/                  # Core application modules
│   ├── __init__.py
│   ├── main.py           # Streamlit entrypoint
│   ├── config.py         # Env variables & settings
│   ├── llm.py            # Azure OpenAI interface
│   ├── prompts.py        # All LLM prompts
│   ├── storage.py        # Azure Blob interaction
│
├── requirements.txt      # Python dependencies
├── .env.example          # Example env variables
├── README.md             # Project documentation
