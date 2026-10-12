from pathlib import Path
import wikipediaapi

class WikiLinkCrawler:

    def __init__(self, user_agent: str = "WikiCrawler/1.0"):
        self.wiki = wikipediaapi.Wikipedia(
            language="ru",
            user_agent=user_agent,
        )

    @staticmethod
    def load_links(file: Path) -> set[str]:
        if not file.exists():
            return set()

        return {
            line.strip()
            for line in file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    @staticmethod
    def append_links(file: Path, links: set[str]):
        if not links:
            return

        with file.open("a", encoding="utf-8") as f:
            for link in sorted(links):
                f.write(link + "\n")

    def extract_links(self, wiki_url: str, namespace: str) -> set[str]:
        title = wiki_url.split("/wiki/")[-1]

        page = self.wiki.page(title)

        return {
            f"https://ru.wikipedia.org/wiki/{link.title.replace(' ', '_')}"
            for link in page.links.values()
            if link.title.startswith(namespace)
        }

    def update_links(
        self,
        source_file: Path,
        target_file: Path,
        namespace: str,
    ):
        source_links = self.load_links(source_file)
        known_links = self.load_links(target_file)

        discovered = set()

        for url in source_links:
            discovered |= self.extract_links(url, namespace)

        new_links = discovered - known_links

        self.append_links(target_file, new_links)

        print(f"Добавлено {len(new_links)} новых ссылок.")