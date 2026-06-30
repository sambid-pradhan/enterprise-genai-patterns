from research_summarizer_ai_agent.citations import format_citation
from research_summarizer_ai_agent.fetcher import extract_main_text


def test_extract_main_text_returns_readable_article_text():
    html = """
    <html>
      <body>
        <article>
          <h1>Title</h1>
          <p>First paragraph.</p>
          <p>Second paragraph.</p>
        </article>
      </body>
    </html>
    """
    text = extract_main_text(html)
    assert "First paragraph" in text
    assert "Second paragraph" in text


def test_format_citation_creates_markdown_link():
    citation = format_citation(
        {"title": "Example Paper", "url": "https://example.com/paper", "source_type": "paper"}
    )
    assert "[Example Paper](https://example.com/paper)" in citation

