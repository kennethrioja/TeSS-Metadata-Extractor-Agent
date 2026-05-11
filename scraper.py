from bs4 import BeautifulSoup
import requests

def scrape_content(url: str) -> str | None:
    """
    Effectue le scraping d'une URL simple en extrayant le texte principal de la page.
    """
    print(f"-> Scraping en cours pour : {url}")
    try:
        # Ajout d'un User-Agent pour ressembler à un navigateur réel
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Lève une exception pour les codes 4xx/5xx

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tentative d'extraire le contenu du corps principal
        main_content = soup.find(['article', 'main', 'body'])
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)
        
        # On tronque le texte pour limiter le coût API et la taille du contexte
        return text[:15000] 

    except requests.exceptions.RequestException as e:
        print(f"ERREUR de scraping pour {url}: {e}")
        return None
    

if __name__ == "__main__":
    url = "https://carpentries-incubator.github.io/python-intermediate-development/"

    text = scrape_content(url=url)
    print(text)