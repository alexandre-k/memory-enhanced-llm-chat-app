<details><summary>Thinking</summary>

The user wants me to create a "get started" guide reusing the commands and script they've provided. They want me to use the commands.md and notes.md content as a starting point.

This is a creative/organizational task - I need to synthesize the provided material into a clean, well-structured getting started guide. I don't need to do web research since all the information is provided in the prompt.

I should:
1. Structure it as a proper getting started guide
2. Reuse the commands and script content
3. Make it clear and easy to follow
4. Include the context about the backend, frontend, authentication, etc.

Let me organize this into sections like:
- Prerequisites
- Installation/Setup
- Running the CLI
- Understanding the user ID
- How to use / test it

I'll format it nicely with markdown.

</details>

Here's a clean **Getting Started** guide based on your demo script and notes:

---

# Getting Started with Memory-Enhanced LLM Chat App

A command-line chat interface with persistent memory, powered by a backend LLM service.

## Prerequisites

- **Git** (to clone the repository)
- **Python** and **uv** (Python package installer)
- (Optional) **Toolbox** if you're on Fedora Atomic or prefer containerized development

## 1. Clone the Repository

```bash
git clone git@github.com:alexandre-k/memory-enhanced-llm-chat-app.git
cd memory-enhanced-llm-chat-app
```

## 2. Set Up Your Environment

### Option A: Using Toolbox (Fedora Atomic / Silverblue)

```bash
toolbox create python
toolbox enter python
sudo dnf install python uv
```

### Option B: Direct System Install

Ensure Python and `uv` are available on your system, then proceed.

## 3. Install Dependencies

```bash
python -m ensurepip --upgrade
uv run python -m pip install -e .
```

Verify the files are in place:

```bash
ls -l
```

## 4. Configure Environment Variables

Copy the example environment file:

```bash
mv .env.example .env
```

> Edit `.env` if needed to match your backend endpoint or API keys. If you just
> run the `memory-cli` app, you don't need to do anything else as the access is
> not restricted. Only if you run `llm-server` locally you will need to edit
> `.env` with a set of API keys and URLs (like `localhost:8000` for the app to
> communicate to your local instance).

## 5. Run the CLI

```bash
uv run memory-cli
```

You will see:

```
LLM CLI ready. Type '/quit' or press Ctrl-D to exit.
>>>
```

### Try It Out

Ask a question to test memory retrieval:

```bash
>>> Remind me what kind of guitar I like.
```

Expected response:

> You like playing acoustic guitar—it’s your favorite instrument, and you’ve been practicing it daily around night time. 🎸

Use `/quit` or press **Ctrl+D** to exit.

---

## How It Works

### Architecture
- **Frontend:** `memory-cli` — the command-line interface you just ran
- **Backend:** Deployed on Alibaba Cloud (ECS), containerized and ready for Kubernetes or any container runtime

### User Identity & Memory
When you first run the CLI, a unique user ID is generated in `ip_users.json`:

```bash
cat ip_users.json
# "8a13f1f5-9df0-4d31-a137-cb067ae0f855"
```

To reuse pre-existing test memories (e.g., the guitar preference), restore the included test ID:

```bash
rm ip_users.json
mv tests/ip_users.json .
cat ip_users.json
```

> **Note:** Changing the UUID means you start with a fresh memory context. All previous memories remain in the database but won't be associated with your new ID.

### Memory in Action
1. Start a conversation and tell the bot your preferences
2. End the session (`/quit`)
3. Start a new session later
4. Ask about something related — the LLM will recall your stored preferences and include them in the response

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `uv run memory-cli` | Start the chat interface |
| `/quit` | Exit the CLI |
| `cat ip_users.json` | View your current user ID |
| `mv tests/ip_users.json .` | Restore the test user ID with demo memories |

---

## Next Steps

- Customize `.env` to point to your own backend deployment
- Explore the codebase to modify memory retrieval logic or add new CLI commands
- Deploy the backend container to your own infrastructure (Kubernetes, Docker, etc.)
