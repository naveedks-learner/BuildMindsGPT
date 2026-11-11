# BuildmindsGPT

A beginner-friendly Streamlit chat app using OpenRouter's Chat Completions API
with `openai/gpt-4o-mini`.

## What it includes

- Chat messages and multiple chat threads stored in `st.session_state`.
- A sidebar for starting, switching, and deleting chats.
- A system prompt, temperature, output-token limit, context-length limit, and
  streaming setting.
- OpenRouter credentials read from Streamlit secrets or a local environment
  variable.
- Light and dark appearance using Streamlit's built-in theme menu.

**History is temporary.** It remains available during the current Streamlit
browser session, but can disappear when the session ends or the page is
refreshed. There is no database, upload feature, or account system in this
starter version. Add those later as separate learning exercises.

## Quick local setup

1. Install Python 3.11 or newer.
2. Open a terminal in this project folder and install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml` with your own OpenRouter key:

   ```toml
   OPENROUTER_API_KEY = "your-openrouter-key"
   ```

4. Run the app:

   ```powershell
   python -m streamlit run app.py
   ```

Never put an API key in `app.py` or a GitHub commit. The local secrets file is
excluded from Git by `.gitignore`.

## Deploy on Streamlit Community Cloud

1. Push the project to a GitHub repository.
2. Create an app on Streamlit Community Cloud from that repository and choose
   `app.py` as the entry point.
3. Add `OPENROUTER_API_KEY = "your-openrouter-key"` in the app's Streamlit
   **Settings > Secrets**.
4. Restart/redeploy the app, then send a test message.

The app and chat history are per visitor session. If the deployed app is public,
visitors can use its LLM connection and may consume your OpenRouter credits.
Only share a deployed app with people you trust, or have each learner deploy
their own app with their own key.

## Student build guide

See [STUDENT_GUIDE.md](./STUDENT_GUIDE.md) for a step-by-step lesson, copyable
prompts for building the app, GitHub account/repository setup, deployment, and
how to share repository and app links with the cohort.
