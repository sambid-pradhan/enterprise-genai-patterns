# Starter AI Agents

Small Streamlit starter apps for building and testing AI agent patterns.

## What It Is

This folder groups standalone agent examples. Each subfolder has its own app, dependencies, and run command.

## Diagram

```text
starter_ai_agents/
|-- research_summarizer_ai_agent/
|   |-- app.py
|   |-- agents.py
|   `-- requirements.txt
`-- web_scraping_ai_agent/
    |-- ai_scrapper.py
    `-- requirements.txt
```

## How To Run

Pick a starter folder, install its dependencies, then run the Streamlit app.

```powershell
pip install -r starter_ai_agents/research_summarizer_ai_agent/requirements.txt
streamlit run starter_ai_agents/research_summarizer_ai_agent/app.py
```

```powershell
pip install -r starter_ai_agents/web_scraping_ai_agent/requirements.txt
streamlit run starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py
```
