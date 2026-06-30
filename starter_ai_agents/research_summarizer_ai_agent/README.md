# Research Summarizer AI Agent

A simple LangChain research agent with a Streamlit UI.

## What It Is

This starter accepts a user prompt, runs one LangChain agent, and lets the agent use tools for web search and page extraction. It can use OpenRouter/DeepSeek when `OPENROUTER_API_KEY` is configured.

## Diagram

```text
User prompt
    |
    v
app.py
    |
    v
run_simple_agent()
    |
    +-- search_web()
    |
    +-- fetch_page_text()
    |
    v
Agent response
```

## How To Run

Install dependencies:

```powershell
pip install -r starter_ai_agents/research_summarizer_ai_agent/requirements.txt
```

Set environment variables in `.env` or your shell:

```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=deepseek/deepseek-v4-flash
OPENROUTER_HTTP_REFERER=http://localhost:8506
OPENROUTER_APP_TITLE=Research Summarizer AI Agent
```

Start the app:

```powershell
streamlit run starter_ai_agents/research_summarizer_ai_agent/app.py
```
