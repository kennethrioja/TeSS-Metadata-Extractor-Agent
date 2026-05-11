import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import NoExtractionStrategy

async def scrape_site_to_dict(base_url):
    results_dict = {}

    # Configuration optimisée pour le contenu LLM
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(
        word_count_threshold=10,        # Ignore les fragments de texte inutiles
        exclude_external_links=True,   # Reste sur le site
        process_iframes=False          # Gain de temps
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # 1. On crawle la page principale pour découvrir les liens
        # Note: Crawl4AI peut aussi gérer le crawling récursif automatiquement
        result = await crawler.arun(url=base_url, config=run_config)

        if result.success:
            # On récupère les liens internes (sublinks)
            internal_links = [link['href'] for link in result.links.get("internal", []) if base_url in link['href']]
            # On ajoute la home
            internal_links.append(base_url)
            # On retire les doublons
            internal_links = list(set(internal_links))

            print(f"Pages trouvées : {len(internal_links)}")

            # 2. On scrappe toutes les pages en parallèle
            # Crawl4AI gère très bien les sessions pour éviter d'être banni
            pages_results = await crawler.arun_many(urls=internal_links, config=run_config)

            for res in pages_results:
                if res.success:
                    # On stocke le Markdown (parfait pour ton LLM)
                    results_dict[res.url] = res.markdown
                else:
                    print(f"Erreur sur {res.url}: {res.error_message}")

    return results_dict


