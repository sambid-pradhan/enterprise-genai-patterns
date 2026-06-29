import os
from typing import List

import streamlit as st
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from scrapegraphai.graphs import SmartScraperGraph


load_dotenv()


class NewsScrapeResult(BaseModel):
    page_title: str = Field(description="The title of the page")
    top_headline: str = Field(description="The main headline on the page")
    summary: str = Field(description="A short summary of the page content")
    key_facts: List[str] = Field(description="A short list of important facts")


st.title("Web Scraping AI Agent")
st.caption("Scrape a news page with ScrapeGraphAI using DeepSeek via OpenRouter.")

openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

if not openrouter_api_key:
    st.warning("Set OPENROUTER_API_KEY in your environment or .env file before running this app.")
    st.stop()

llm_model = init_chat_model(
    model="deepseek/deepseek-v4-flash",
    model_provider="openai",
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key,
    temperature=0,
    model_kwargs={"response_format": {"type": "json_object"}},
)

graph_config = {
    "llm": {
        "model_instance": llm_model,
        "model_tokens": 128000,
    },
    "verbose": True,
}

url = st.text_input(
    "Enter the news page URL",
    value="https://www.bbc.com/news",
)
user_prompt = st.text_input(
    "What do you want the AI agent to scrape from the page?",
    value=(
        "Extract the page title, the top headline, a short summary, and 3 to 5 key facts. "
        "If a field is not available, use NA. Return only values that fit the schema."
    ),
)

if st.button("Scrape"):
    if not url.strip():
        st.warning("Please enter a news page URL.")
    elif not user_prompt.strip():
        st.warning("Please enter a scraping prompt.")
    else:
        try:
            smart_scraper_graph = SmartScraperGraph(
                prompt=user_prompt,
                source=url,
                config=graph_config,
                schema=NewsScrapeResult,
            )
            result = smart_scraper_graph.run()
            st.write(result)
        except Exception as exc:
            st.error(f"Scrape failed: {exc}")
