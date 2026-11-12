# BuildmindsGPT

A beginner-friendly Streamlit chat app using OpenRouter's Chat Completions API
with `openai/gpt-4o-mini`.

## What it includes

- Chat messages kept in `st.session_state` while active and saved as one JSON
  file per conversation in `chats/`.
- A ChatGPT-inspired, left-aligned sidebar labeled **Recents** for starting,
  switching, and deleting chats, with message avatars hidden for a cleaner
  transcript. The center-pane content is left-aligned too.
- A polished, vibrant layout with **Inference Settings** for the system prompt,
  temperature, output-token limit, context length, and streaming. Click **Save**
  to apply system-prompt edits for the current session.
- A **Transaction Logs** inspector showing the latest Chat Completions request JSON and
  response JSON (including raw stream chunks when streaming is enabled).
- OpenRouter credentials read from Streamlit secrets or a local environment
  variable.
- Light and dark appearance using Streamlit's built-in theme menu.

Chat history is restored after a page refresh from local JSON files. There is
no database, upload feature, or account system in this starter version.
Conversation files are excluded from Git by `.gitignore`.
The JSON inspector is session-only and excludes API credentials. It displays
the system prompt and messages included in the request; do not enter secrets
into chat or prompt text.

**Demo and deployment limitations:** all visitors to the same deployment use
the same chat files, so they can see and delete one another's saved chats. The
files are on the app server, not tied to an individual account. Streamlit
Community Cloud's local filesystem is not durable, so chats can be lost when
the app restarts or is redeployed. Do not use this storage design for private
or important conversations.

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

If the deployed app is public, visitors can use its LLM connection and may
consume your OpenRouter credits. They can also see and delete saved chats.
Only share a deployed app with people you trust, or have each learner deploy
their own app with their own key.

## Student guides

- [Student Guide QA](./STUDENT_QA_GUIDE.md): simplified instructions for
  non-coders, with coding-agent prompts for setup and publishing.
- [Student Dev Guide](./STUDENT_DEV_GUIDE.md): the detailed, hands-on guide for
  developers, with staged prompts and explanations.
