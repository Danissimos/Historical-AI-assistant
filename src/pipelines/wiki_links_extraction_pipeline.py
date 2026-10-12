from pathlib import Path

from src.data_processing.wikipedia.wiki_links_parser import WikiLinkCrawler


# Корень проекта
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "wiki"

CATEGORY_FILE = DATA_DIR / "wiki_categories.txt"
PORTAL_FILE = DATA_DIR / "wiki_portals.txt"
LINKS_FILE = DATA_DIR / "wiki_links.txt"

# Парсинг
crawler = WikiLinkCrawler()
crawler.update_links(
    source_file=CATEGORY_FILE,
    target_file=PORTAL_FILE,
    namespace="Портал:"
)
crawler.update_links(
    source_file=PORTAL_FILE,
    target_file=LINKS_FILE,
    namespace=""
)