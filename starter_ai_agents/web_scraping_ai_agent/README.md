# Web Scraping AI Agent

A Streamlit starter for extracting structured information from a web page.

## What It Is

This app uses ScrapeGraphAI with a DeepSeek model through OpenRouter. You provide a page URL and a scraping prompt, and the app returns structured fields like title, headline, summary, and key facts.

## Diagram

```text
URL + scraping prompt
        |
        v
ai_scrapper.py
        |
        v
ScrapeGraphAI
        |
        v
DeepSeek via OpenRouter
        |
        v
Structured result
```

## How To Run

Install dependencies:

```powershell
pip install -r starter_ai_agents/web_scraping_ai_agent/requirements.txt
playwright install
```

Set environment variables in `.env` or your shell:

```env
OPENROUTER_API_KEY=your_key_here
```

Start the app:

```powershell
streamlit run starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py
```
