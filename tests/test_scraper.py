import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from scraper import clean_markdown_urls, scrape_site_to_dict


class TestCleanMarkdownUrls:
    def test_removes_bare_http_url(self):
        text = "Visit https://example.com for more info"
        result = clean_markdown_urls(text)
        assert "https://example.com" not in result
        assert "Visit" in result

    def test_removes_bare_http_url(self):
        text = "See http://example.com/page"
        result = clean_markdown_urls(text)
        assert "http://example.com/page" not in result

    def test_removes_url_from_markdown_link(self):
        text = "[click here](https://example.com/path)"
        result = clean_markdown_urls(text)
        assert "https://example.com/path" not in result

    def test_cleans_empty_parentheses_after_url_removal(self):
        text = "[link](https://example.com)"
        result = clean_markdown_urls(text)
        assert "()" not in result

    def test_preserves_plain_text(self):
        text = "This is plain text without any URLs."
        result = clean_markdown_urls(text)
        assert result == text

    def test_removes_multiple_urls(self):
        text = "Check https://foo.com and https://bar.com/baz for details"
        result = clean_markdown_urls(text)
        assert "https://foo.com" not in result
        assert "https://bar.com/baz" not in result
        assert "Check" in result
        assert "for details" in result

    def test_removes_permalink_artifact(self):
        text = 'Some section ( "Permalink to this headline") content'
        result = clean_markdown_urls(text)
        assert '"Permalink to this headline"' not in result

    def test_preserves_non_url_parentheses(self):
        text = "Function call (argument) here"
        result = clean_markdown_urls(text)
        assert "(argument)" in result


def _mock_crawler(arun_result):
    """Build a properly-configured AsyncMock for AsyncWebCrawler.

    AsyncMock's __aenter__ returns a different AsyncMock by default, not
    the crawler itself. We override __aenter__.return_value so that the
    object inside `async with AsyncWebCrawler(...) as crawler` is the same
    mock we configure with .arun.return_value.
    """
    mock_crawler = AsyncMock()
    mock_crawler.__aenter__.return_value = mock_crawler
    mock_crawler.arun.return_value = arun_result
    return mock_crawler


class TestScrapeSiteToDict:
    async def test_single_page_success_returns_cleaned_content(self):
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.url = "https://example.com"
        mock_result.markdown = "# Hello World\nSee https://some-link.com for info."

        with patch("scraper.AsyncWebCrawler") as MockClass:
            MockClass.return_value = _mock_crawler(mock_result)
            result = await scrape_site_to_dict("https://example.com", single_page=True)

        assert len(result) == 1
        url_key = next(iter(result))
        assert "Hello World" in result[url_key]
        assert "https://some-link.com" not in result[url_key]

    async def test_single_page_failure_returns_empty_dict(self):
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error_message = "Connection refused"

        with patch("scraper.AsyncWebCrawler") as MockClass:
            MockClass.return_value = _mock_crawler(mock_result)
            result = await scrape_site_to_dict("https://example.com", single_page=True)

        assert result == {}

    async def test_single_page_uses_result_url_as_key(self):
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.url = "https://example.com/canonical"
        mock_result.markdown = "content"

        with patch("scraper.AsyncWebCrawler") as MockClass:
            MockClass.return_value = _mock_crawler(mock_result)
            result = await scrape_site_to_dict("https://example.com", single_page=True)

        assert "https://example.com/canonical" in result
