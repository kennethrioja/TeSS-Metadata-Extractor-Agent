import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import NoExtractionStrategy
import re


async def scrape_site_to_dict(base_url, single_page=True):
    """
    Scrape a website and return a dictionary {url: markdown}.

    Args:
        base_url (str): Starting URL
        single_page (bool): If True, only scrape the provided page.
                            If False (default), scrape all discovered internal pages.
    """
    results_dict = {}

    # Optimized configuration for LLM content
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(
        word_count_threshold=10,        # Ignore useless text fragments
        exclude_external_links=True,    # Stay on the site
        process_iframes=False           # Save time
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # 1. Crawl the main page
        result = await crawler.arun(url=base_url, config=run_config)

        if not result.success:
            print(f"Error on main page {base_url}: {result.error_message}")
            return results_dict

        # Single page mode: return the result directly
        if single_page:
            print("Single page mode: scraping the main page only.")
            results_dict[result.url] = clean_markdown_urls(result.markdown)
            return results_dict

        # Full mode: discover and scrape all internal pages
        internal_links = [
            link['href']
            for link in result.links.get("internal", [])
            if base_url in link['href']
        ]
        # Add the home page
        internal_links.append(base_url)
        # Remove duplicates
        internal_links = list(set(internal_links))

        print(f"Full mode: {len(internal_links)} page(s) found.")

        # 2. Scrape all pages in parallel
        pages_results = await crawler.arun_many(urls=internal_links, config=run_config)

        for res in pages_results:
            if res.success:
                results_dict[res.url] = clean_markdown_urls(res.markdown)
            else:
                print(f"Error on {res.url}: {res.error_message}")

    return results_dict

import re

def clean_markdown_urls(text):
    # Regex breakdown:
    # (?<=\()https?://\S+(?=\))  -> Matches URLs inside parentheses (Markdown links)
    # |                          -> OR
    # (?<!\]\()https?://\S+      -> Matches bare URLs not preceded by ']('
    
    # This pattern focuses on strings starting with http/https 
    # and continues until it hits a space or a closing parenthesis.
    url_pattern = r'https?://[^\s\)]+'
    
    # We replace the found URLs with an empty string
    cleaned_text = re.sub(url_pattern, '', text)
    
    # Optional: Clean up empty parentheses left behind: []() -> []
    cleaned_text = cleaned_text.replace('()', '').replace('( "Permalink to this headline")', '')
    
    return cleaned_text


# Usage examples
if __name__ == "__main__":
    # Single page only (default behavior)
    asyncio.run(scrape_site_to_dict("https://example.com", single_page=True))

    # Full site 
    asyncio.run(scrape_site_to_dict("https://example.com"))
    # or explicitly:
    asyncio.run(scrape_site_to_dict("https://example.com", single_page=False))