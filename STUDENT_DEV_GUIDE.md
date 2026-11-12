# Student Dev Guide: build a chat app

This workshop builds a small ChatGPT-style app with Streamlit and OpenRouter.
You will create the code yourself with an AI coding assistant, run it locally,
put the project on GitHub, and deploy it to Streamlit Community Cloud.

## What you will build

- A chat screen with multiple chats and a **Recents** list in a ChatGPT-style
  sidebar; the sidebar and center-pane content are left-aligned, and messages
  display without user/assistant avatars.
- `st.session_state` for active chats and one JSON file per conversation in a
  local `chats/` folder.
- OpenRouter's Chat Completions API using `openai/gpt-4o-mini`.
- A system prompt, temperature, maximum output tokens, recent-message context
  limit, and a streaming on/off switch.
- A vibrant interface with **Inference Settings** and a **Settings** inspector
  for request and response JSON.
- A GitHub repository and a deployed Streamlit app.

Chat history is restored from JSON files after a browser refresh. All visitors
to the same deployment share these files and can see or delete the same chats.
Streamlit Community Cloud may clear local files when the app restarts or is
redeployed. There are no accounts, database, or file uploads in this demo.

## Before the workshop

You need:

- A computer with internet access.
- Python 3.11 or newer installed.
- A web browser.
- An AI coding assistant that can generate and explain Python code.
- A personal OpenRouter API key. Keep it private.

## Part 1: Create your accounts

### GitHub

1. Go to [github.com](https://github.com/) and choose **Sign up**.
2. Enter an email address, create a password, choose a username, and verify your
   email.
3. Save your username. You will need it to create a repository and share its
   link.
4. Do not share your password, recovery codes, or authentication tokens.

### OpenRouter

1. Go to [openrouter.ai](https://openrouter.ai/) and create/sign in to your
   account.
2. Open the **Keys** page and create a key for this project.
3. Copy the key into a password manager or another private place. You will paste
   it into local Streamlit secrets and later into Streamlit Cloud settings.
4. Never paste the key into an AI prompt, source file, screenshot, class chat,
   or GitHub commit. Check OpenRouter's current model pricing and account
   requirements before making requests.

### Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Sign in with the GitHub account you just created.
3. Grant the requested access to the repository you will deploy.

## Part 2: Create your project locally

1. Make a folder named `my-chat-app` on your computer.
2. Open that folder in VS Code.
3. Open VS Code's terminal (**Terminal > New Terminal**).
4. Create `requirements.txt` containing:

   ```text
   streamlit>=1.57,<2
   openai>=1.68,<3
   ```

5. In the terminal, install the packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

   If `python` is not recognized on Windows, try `py -m pip install -r
   requirements.txt`. In the steps below, use `py` instead of `python` too. If
   neither works, install Python from
   [python.org/downloads](https://www.python.org/downloads/) and reopen VS Code.

6. Ask your AI coding assistant to help write `app.py`. Use the prompts in the
   next section one at a time. Review the code and ask the assistant to explain
   it; don't paste your API key into the prompt.

## Part 3: Prompts to build the app

Use these prompts in order. Replace bracketed notes if you like. Give the
assistant any errors you see, but remove API keys and other secrets first.

### Prompt 1 — Plan the beginner app

> I am a beginner learning Python and Streamlit. Help me build a small,
> single-file `app.py` chat application using Streamlit and OpenRouter's
> OpenAI-compatible Chat Completions API with model `openai/gpt-4o-mini`.
> First give me a short implementation plan and explain each piece in plain
> language. Use `st.session_state` for a dictionary of conversations and the
> active conversation ID. Save each conversation as a JSON file in a local
> `chats/` folder and restore those files when a new session starts. Do not add
> a database, user accounts, file uploads, or extra packages. Keep the API key
> out of source code. Explain that everyone using one deployment shares chat
> history and Streamlit Cloud may clear local files on restart. Give the
> interface a polished, vibrant appearance without external font or JavaScript
> dependencies. Name model controls "Inference Settings"; add a separate
> "Transaction Logs" inspector for the latest request JSON and response JSON.
> Label the sidebar chat list "Recents", hide chat-message avatars, and keep
> the sidebar and center-pane content left-aligned while keeping both light and
> dark themes working.

### Prompt 2 — Build chat and history

> Now create `app.py` from that plan. Include a chat input and user/assistant
> message display with `st.chat_message`, but hide the user and assistant
> avatars. Add a sidebar button to start a new chat, buttons under "Recents" to
> switch between chat histories, and a way to delete the
> current chat. Keep active state in `st.session_state`, and load/save each
> conversation as JSON under `chats/` so it returns after a refresh. Initialize
> state safely so Streamlit reruns work. Add the vibrant layout and keep the
> request/response inspector readable. Explain the code after showing it.

### Prompt 3 — Connect OpenRouter safely

> Add a function that reads `OPENROUTER_API_KEY` from the local environment
> when set, otherwise from `st.secrets`. Use
> `OpenAI(api_key=..., base_url="https://openrouter.ai/api/v1")` and call
> `client.chat.completions.create` with model `openai/gpt-4o-mini`. Send a
> configurable system prompt followed by recent conversation messages. Show a
> clear UI error if the key is missing or the API request fails. Do not print,
> log, or display the key.

### Prompt 4 — Add the learning settings

> Add sidebar settings for temperature, maximum output tokens, the number of
> recent chat messages sent as context, and whether responses stream. Use
> `st.write_stream` for streaming and the same Chat Completions API with
> `stream=True`. When streaming is off, make a normal non-streaming request.
> Put a Save button next to the system prompt editor; keep edits as a draft
> until Save is clicked, then use the saved prompt for future requests in this
> session. Label the controls "Inference Settings" and add a separate
> "Transaction Logs" section showing the latest request and response JSON. Do not
> include API credentials. Keep the code beginner-readable and explain how the
> settings affect the request.

### Prompt 5 — Review and test

> Review my `app.py` and `requirements.txt` for beginner-level correctness.
> Check that messages survive Streamlit reruns within one browser session, that
> separate chats do not mix, and that only the configured recent messages are
> sent to the model. Check that system-prompt edits are not applied until Save
> is clicked. Check that the inspector reflects the actual request and response
> and never includes credentials. Check that the API key cannot be committed
> accidentally.
> List any problems first, then suggest the smallest corrections. Do not add a
> database or change the JSON-file persistence design.

### Prompt 6 — Ask for help with an error

> I am learning Streamlit. Here is the error I got:
> [paste the traceback, but remove API keys, passwords, and other secrets].
> Explain the cause in beginner-friendly language, point to the exact line or
> concept, and suggest the smallest fix. Please don't rewrite the whole app
> unless necessary.

## Part 4: Add your API key locally

1. In the project folder, create a folder named `.streamlit`.
2. Inside it, create `secrets.toml` with:

   ```toml
   OPENROUTER_API_KEY = "paste-your-own-key-here"
   ```

3. Create a `.gitignore` file in the project root and add:

   ```gitignore
   .streamlit/secrets.toml
   .env
   __pycache__/
   .venv/
   chats/*.json
   ```

4. Check that `.streamlit/secrets.toml` is not shown among files you intend to
   upload or commit. Never share a screenshot that reveals the key.

## Part 5: Run and test locally

1. In the VS Code terminal, run:

   ```powershell
   python -m streamlit run app.py
   ```

2. Streamlit opens a browser tab. If it prints a local URL instead, Ctrl+click
   that URL.
3. Send a test message and verify you receive a reply.
4. Start another chat, switch back to the first, and confirm the messages remain
   separate.
5. Change a setting and test again.
6. Refresh the browser and confirm saved chats return.
7. Stop the local app with **Ctrl+C** in the terminal.

If you see a missing-key error, check the spelling and location of
`.streamlit/secrets.toml`. If you see an OpenRouter error, check your key,
account/model access, and current usage limits. Do not post the key when asking
for help.

## Part 6: Create your own GitHub repository

### Easy browser method

1. Sign in at [github.com](https://github.com/).
2. Click **+** near the top-right, then **New repository**.
3. Name it `my-chat-app` (or another short name).
4. Choose **Public** if the cohort needs to review the code. Source code is
   public, so it must contain no API keys or personal data. Choose **Private**
   if your instructor and Streamlit account can access private repositories.
5. Optionally select **Add a README file**, then create the repository.
6. In the repository page, choose **Add file > Upload files**.
7. Upload `app.py`, `requirements.txt`, `.gitignore`, and optionally `README.md`.
   Do **not** upload `.streamlit/secrets.toml`, `chats/*.json`, `.venv`, or
   Python cache files.
8. Enter a commit message such as `Create beginner chat app`, then click
   **Commit changes**.
9. Open the **Code** page and copy the repository URL, for example
   `https://github.com/YOUR-USERNAME/my-chat-app`.

If uploading nested files through the browser is awkward, use **GitHub
Desktop**: install it from [desktop.github.com](https://desktop.github.com/),
sign in, add your project folder as a local repository, publish it to your
GitHub account, and confirm `.streamlit/secrets.toml` and `chats/*.json` are
ignored before publishing.

### Verify before sharing

1. Open the repository's **Code** page and check the file list.
2. Confirm `.streamlit/secrets.toml` and any `chats/*.json` files are absent.
3. Search the repository for `sk-or-` or your key; if a key was committed,
   revoke it in OpenRouter immediately and create a replacement. Deleting the
   file in a later commit does not erase it from Git history.
4. Share only the repository URL with the cohort. Never share an API key,
   GitHub password, or access token.

## Part 7: Deploy your app

1. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with
   GitHub.
2. Choose **Create app** (or **New app**) and select your repository,
   `main` branch, and `app.py`.
3. Open the app's **Advanced settings** or **Settings > Secrets** before or
   after deployment.
4. Add this TOML setting, using your own key:

   ```toml
   OPENROUTER_API_KEY = "your-own-openrouter-key"
   ```

5. Save the secret and deploy/reboot the app if prompted.
6. Open the deployed app and send a short test message.
7. Copy your deployed app URL. Check that the URL works before sending it to the
   cohort.

Each student should deploy with their **own** OpenRouter key. Visitors to the
same deployed app can see and delete its saved chats. A publicly accessible app
can also let visitors make model requests using its configured key, which may
consume that student's credits. Streamlit Cloud may clear chat files when the
app restarts. Follow the instructor's sharing/access instructions.

## Part 8: Share your work with the cohort

Post these items in the instructor's requested channel or form:

- Your GitHub repository URL.
- Your deployed Streamlit app URL, if deployment is part of the exercise.
- One sentence describing something you learned or one issue you solved.

Before sharing, open both links in a browser and confirm they work. Never post
your OpenRouter key, GitHub password, recovery code, or a screenshot containing
them.

## If something goes wrong

- **GitHub asks you to sign in:** sign in to the correct account; never send
  credentials to an instructor or assistant.
- **Streamlit cannot find `app.py`:** select the correct repository branch and
  entry-point path in the deployment settings.
- **Packages are missing:** confirm `requirements.txt` is at the repository
  root and contains `streamlit` and `openai`, then redeploy.
- **Secret is missing:** add `OPENROUTER_API_KEY` in Streamlit Cloud's Secrets
  settings; a local secrets file is not uploaded to the cloud.
- **Changes do not appear online:** commit/upload the new code to GitHub and
  wait for Streamlit to redeploy.
- **Local chats do not return:** confirm the `chats/` folder is beside `app.py`
  and that its JSON files have not been deleted.
- **Cloud chats disappear after a restart:** Streamlit Community Cloud's local
  filesystem is temporary; this demo does not use durable storage.

## Optional next lessons

After the basic app works, add one feature at a time: document uploads, a
downloadable transcript, account-specific storage, authentication, or more
careful context-window/token counting. Explain the privacy and cost trade-offs
before sharing a multi-user app.
