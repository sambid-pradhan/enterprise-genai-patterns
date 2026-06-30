# Research Summarizer Starter Design

## Goal

Build a new `starter_ai_agents` project: a `Streamlit` app that takes a topic or question, runs multiple web search passes, optionally opens the strongest primary sources, and produces a sectioned research digest with citations.

## User Experience

The app should feel like a lightweight research assistant:

1. User enters a topic or question.
2. The app expands broad topics into 2 to 4 sub-questions.
3. The app runs several web searches per sub-question.
4. The app fetches the full text of the best primary sources when useful.
5. The app writes a structured report, not a search-results dump.

The report should be easy to read in one screen and still detailed enough for personal research.

## Scope

### In scope

- `Streamlit` UI
- single-topic input
- automatic topic decomposition
- multiple web search passes
- optional full-page fetch for top primary sources
- sectioned report with citations
- primary-sources-only evidence policy

### Out of scope

- user accounts
- saved research history
- PDF export
- background jobs
- multi-turn chat
- non-web data sources

## Core Loop

The app should follow this loop:

1. Break a broad topic into 2 to 4 sub-questions.
2. Search each sub-question separately.
3. Fetch the full page for the best 2 to 3 primary sources when the snippets are not enough.
4. Compare the sources and identify agreement, gaps, and weak evidence.
5. Synthesize a report with citations.

This should be implemented as separate passes so the app can reason over more than one search result set instead of depending on a single query.

## Report Format

The final output should have these sections:

- Executive summary
- Sub-questions and findings
- What the sources agree on
- Where evidence is weak or missing
- Citations

The report should be written in concise prose with short bullets where that improves readability.

## Source Policy

Use primary sources only.

Acceptable sources include:

- official documentation
- research papers
- company blog posts that are clearly first-party
- standards or specification pages

If primary sources are thin or conflicting, the app should say so instead of silently filling gaps with weaker material.

## Suggested Components

### `app.py`

Main `Streamlit` entry point. Handles the form, starts the research passes, and renders the final report.

### `research_planner`

Turns the user topic into sub-questions and search queries.

### `search_agent`

Runs multiple web searches and returns ranked candidate sources for each sub-question.

### `source_fetcher`

Fetches full pages for the strongest sources when the snippet is not enough.

### `synthesizer`

Merges the gathered evidence into a sectioned digest with citations.

### `citation_formatter`

Formats source links and basic source metadata for display in the report.

## Data Flow

1. User submits a topic.
2. Planner produces sub-questions and search queries.
3. Search agent gathers candidate sources for each sub-question.
4. Fetcher pulls full text from the best primary sources.
5. Synthesizer produces the report.
6. UI renders the final digest.

## Error Handling

- If a search pass fails, show the error for that pass and continue with the others when possible.
- If too few primary sources are found, return a short report that says evidence is thin.
- If page fetching fails, fall back to the available snippet and note the limitation.
- If the topic is too broad, ask one clarifying question instead of guessing.

## Success Criteria

The starter is good enough when:

- a user can enter a topic and get a structured digest
- the report cites sources clearly
- the app uses more than one search pass
- the app fetches full pages for the best sources when helpful
- the app stays within a simple starter-project shape

## Notes

The existing `starter_ai_agents/web_scraping_ai_agent` project can serve as the template for layout and dependency style, but the implementation should shift from scraping one page to researching several sources and synthesizing them.

