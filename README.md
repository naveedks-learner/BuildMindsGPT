# BuildmindsGPT

A Streamlit chat app using OpenRouter's Chat Completions API and
`openai/gpt-4o-mini`, deployed on Streamlit Community Cloud.

## Features

- Persistent conversation and message history in Supabase Postgres.
- New chats, history selection, and chat deletion in the sidebar.
- Temperature, estimated context-window budget, maximum output tokens,
  streaming, verbosity, and system-prompt settings.
- Text, Markdown, CSV, and text-based PDF uploads for chat context.
- Light and dark themes using Streamlit's native appearance control.

Uploads are limited to 10 MB per file and 50,000 extracted characters per
message; scanned PDFs do not receive OCR. Extracted file text is stored with
the corresponding user message in Supabase Postgres so it remains available
when the conversation is reopened. Original binary files are not stored.

The context window uses the GPT-4o tokenizer plus a small per-message overhead
estimate. Older turns are dropped first to leave room for the system prompt and
requested maximum output. Settings and pending uploads are held in Streamlit
session state; conversation history and extracted upload text are stored in
Supabase Postgres. Uploaded document text is included with each new message
while those files remain selected, and can be removed from the sidebar.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Configure secrets in `.streamlit/secrets.toml`:

   ```toml
   OPENROUTER_API_KEY = "your-key"
   SUPABASE_DB_URL = "your-supabase-postgres-connection-string"
   ```

   Get the Postgres connection string from your Supabase project's **Connect**
   settings. Use the transaction pooler connection string and keep the database
   password private.
4. Start the app:

   ```powershell
   streamlit run app.py
   ```

For local development without Supabase, set an explicit SQLite file path before
launching:

   ```powershell
   $env:CHAT_DB_PATH = ".data\chat_history.sqlite3"
   streamlit run app.py
   ```

SQLite is only intended for local testing; it is not persistent on Streamlit
Community Cloud.

## Deploy to Streamlit Community Cloud

1. Push the project to a GitHub repository. Streamlit Community Cloud deploys
   apps from GitHub; Hugging Face Spaces is not needed.
2. In Streamlit Community Cloud, create an app from the repository and select
   `app.py` as the entry point.
3. In the app's **Settings > Secrets**, add:

   ```toml
   OPENROUTER_API_KEY = "your-openrouter-key"
   SUPABASE_DB_URL = "your-supabase-postgres-connection-string"
   ```

4. Keep the Streamlit app private. This version does not have user accounts or
   per-user history isolation, so users with access share the same conversations.
5. Supabase stores chat history independently of Streamlit app restarts.

The app creates the required tables and index on its first run. Do not commit
`.streamlit/secrets.toml`; it is excluded by `.gitignore`.
