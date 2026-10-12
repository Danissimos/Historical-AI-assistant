import re
from pathlib import Path
from urllib.parse import (
    urljoin,
    urlparse,
    unquote,
)
import json
import requests
from sqlalchemy import text

from src.data_processing.wikipedia.wiki_article_processing import Chunk


class WikipediaStorage:

    def __init__(
        self,
        engine,
        image_dir: str = Path(__file__).resolve().parents[3] / "data/raw/images/wikipedia",
    ):
        self.engine = engine

        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ---------------------------------------------------------
    # Public
    # ---------------------------------------------------------

    def save(
        self,
        chunks: list[Chunk],
    ):

        with self.engine.begin() as conn:

            for chunk in chunks:

                images = self._download_images(
                    image_urls=chunk.metadata.images,
                )

                metadata = {
                    "doc_structure_path": chunk.metadata.section_path,
                    "images": images,
                }

                conn.execute(
                    text(
                        """
                        INSERT INTO chunks
                        (
                            page_title,
                            page_url,
                            chunk_index,
                            source,
                            chunk_text,
                            metadata
                        )
                        VALUES
                        (
                            :page_title,
                            :page_url,
                            :chunk_index,
                            :source,
                            :chunk_text,
                            CAST(:metadata AS jsonb)
                        )
                        """
                    ),
                    {
                        "page_title": chunk.metadata.page_title,
                        "page_url": chunk.metadata.url,
                        "chunk_index": chunk.metadata.chunk_index,
                        "source": chunk.metadata.source,
                        "chunk_text": chunk.text,
                        "metadata": json.dumps(
                            metadata,
                            ensure_ascii=False,
                        ),
                    },
                )

    # ---------------------------------------------------------
    # Images
    # ---------------------------------------------------------

    def _download_images(
            self,
            image_urls: list[str],
    ) -> list[dict]:

        result = []

        for url in image_urls:

            full_url = urljoin(
                "https:",
                url,
            )

            parsed = urlparse(full_url)

            original_filename = Path(
                unquote(parsed.path)
            ).name

            # Делаем имя безопасным для Windows
            filename = re.sub(
                r'[<>:"/\\|?*]',
                "_",
                original_filename,
            ).rstrip(" .")

            local_path = self.image_dir / filename

            if not local_path.exists():

                try:

                    response = requests.get(
                        full_url,
                        timeout=30,
                        headers={
                            "User-Agent": (
                                "HistoricalAIAssistant/0.1 "
                                "(Research project for local use and education; "
                                "contact: ghj228822@gmail.com)"
                            )
                        },
                    )

                    response.raise_for_status()

                    local_path.write_bytes(
                        response.content
                    )

                except Exception:
                    continue

            result.append(
                {
                    "wiki_url": full_url,
                    "local_path": str(local_path),
                    "original_filename": original_filename,
                }
            )

        return result