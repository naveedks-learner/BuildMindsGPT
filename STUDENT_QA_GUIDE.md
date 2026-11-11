# Student Guide QA: build and share a chat app

Build a small Streamlit chatbot with an AI coding assistant, run it, and deploy
it. Chat history is saved in JSON files in the app's `chats/` folder, so it
usually survives a browser refresh. Everyone using the same deployed demo can
see and delete the same chats. Streamlit Cloud may clear those files when the
app restarts. This beginner version has no database, accounts, or file uploads.

## 1. Create your accounts and API key

1. Create a GitHub account at [github.com](https://github.com/) and verify your
   email.
2. Create an OpenRouter account at [openrouter.ai](https://openrouter.ai/),
   then create an API key from its **Keys** page. Keep the key private.
3. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with
   GitHub and grant access to the repository you will create.
4. Check OpenRouter's model pricing and usage requirements. Each student should
   use their own key.

Never paste your API key into an AI prompt, source file, GitHub repository, or
cohort chat. Do not share your GitHub password, recovery codes, or tokens.

## 2. Create the project with your coding assistant

1. Install Python 3.11 or newer and open a new, empty project folder in VS Code.
2. Open the coding assistant and ask it to build the app:

   > I am a beginner. In this project folder, create a simple Streamlit chat app
   > in `app.py` using OpenRouter's Chat Completions API with model
   > `openai/gpt-4o-mini`. Use `st.session_state` for active conversations and
   > save each conversation as a JSON file in a `chats/` folder so history
   > survives refreshes. Add a sidebar to create, switch, and delete chats. Add
   > settings for temperature, maximum output tokens, recent context length,
   > and streaming on/off. Add a system prompt editor with a nearby Save button;
   > apply prompt edits only after Save is clicked. Read
   > `OPENROUTER_API_KEY` from Streamlit secrets, never hard-code it. Keep this
   > beginner-friendly and do not add a database, accounts, file uploads, or
   > extra packages. Make `.gitignore` exclude chat JSON files,
   > `.streamlit/secrets.toml`, `.env`, virtual environments, and Python cache
   > files. Explain that all visitors to one deployment can see/delete chats
   > and Streamlit Cloud may clear local files after a restart.

3. Read the assistant's explanation. If it asks to install the listed
   requirements, approve that step.

If you prefer to type the app yourself, ask the assistant to teach you one
feature at a time instead of generating the files.

## 3. Add your key and test the app

1. Ask your coding assistant to create `.streamlit/secrets.toml` with this
   placeholder setting, but **do not send it your actual key**:

   ```toml
   OPENROUTER_API_KEY = "paste-your-key-here"
   ```

2. Open that file yourself and replace the placeholder with your own key. Do not
   show the key in screenshots or paste it into chat.
3. In the VS Code terminal, run:

   ```powershell
   python -m pip install -r requirements.txt
   python -m streamlit run app.py
   ```

   If `python` is not recognized on Windows, use `py` in its place. If Python
   isn't installed, install it from
   [python.org/downloads](https://www.python.org/downloads/), reopen VS Code,
   then retry.
4. In the browser, send a message, create a second chat, switch between chats,
   and try the settings. Edit the system prompt and click **Save** before testing
   it. Refresh the browser and confirm the saved chats return.
5. To ask for help with an error, paste the error into the coding assistant
   **after removing API keys and other secrets**. You do not need a separate
   error-help prompt.

## 4. Create a GitHub repository and push your project

1. On GitHub, choose **+ > New repository**. Name it `my-chat-app`. Choose
   **Public** if your cohort needs to see the source; choose **Private** if
   access can be granted to the instructor and Streamlit. Create it without
   adding starter files.
2. Copy the new repository's HTTPS URL, such as
   `https://github.com/YOUR-USERNAME/my-chat-app`.
3. Give this prompt to your coding assistant, replacing the example URL:

   > Push this project to my GitHub repository:
   > `https://github.com/YOUR-USERNAME/my-chat-app`. First verify that
   > `.streamlit/secrets.toml`, `.env`, `chats/*.json`, virtual environments,
   > and Python cache files are ignored and are not staged. Do not read, print,
   > or upload secrets or saved chats. If GitHub sign-in is needed, tell me to
   > complete the browser sign-in; never ask me to paste a password or access
   > token. Then push the project and show me the repository link.

4. If the assistant cannot push, ask it to explain the sign-in or Git steps, or
   upload `app.py`, `requirements.txt`, `.gitignore`, and `README.md` using
   GitHub's **Add file > Upload files**. Do not upload `.streamlit/secrets.toml`
   or any `chats/*.json` files.
5. Open the repository in your browser. Make sure the files are there and
   `.streamlit/secrets.toml` is **not** there. Copy the repository link for the
   cohort.

If you accidentally upload your key, revoke it in OpenRouter and create a new
one immediately. Deleting a leaked key file later does not remove it from Git
history.

## 5. Deploy and share

1. In Streamlit Community Cloud, choose **Create app** and select your GitHub
   repository, its `main` branch, and `app.py`.
2. In the app's **Settings > Secrets** (or **Advanced settings**), add your key:

   ```toml
   OPENROUTER_API_KEY = "your-own-openrouter-key"
   ```

3. Save/deploy, open the app, and send a test message.
4. Share your **GitHub repository link** and **deployed app link** in the
   instructor's requested channel.

Visitors to the same deployed app can see and delete its saved chats. They may
also make requests using your configured key and consume your OpenRouter
credits. Streamlit Cloud may clear chat files when the app restarts. Follow the
instructor's sharing instructions and only share the demo with people you trust.

## Optional next features

Once the starter works, ask your coding assistant to help add one feature at a
time, such as file uploads, downloadable chats, or account-specific storage.
Discuss privacy and cost before making a multi-user app.
