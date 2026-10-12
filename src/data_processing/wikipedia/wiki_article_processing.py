from dataclasses import dataclass, field
from urllib.parse import quote, unquote

from src.data_processing.wikipedia.wiki_links_processing import (
    WikipediaParser,
    WikiPage,
    Section,
    Paragraph,
    Image,
    Table,
    ListBlock,
)


# ==========================================================
# Models
# ==========================================================

@dataclass
class ChunkMetadata:
    page_title: str
    section_path: list[str]

    chunk_index: int

    source: str
    url: str

    images: list[str] = field(default_factory=list)


@dataclass
class Chunk:
    text: str
    metadata: ChunkMetadata


# ==========================================================
# Chunker
# ==========================================================

class WikipediaChunker:

    def __init__(
        self,
        max_chars: int = 1200,
    ):
        self.max_chars = max_chars

        self._chunks: list[Chunk] = []

        self._buffer: list[str] = []
        self._images: list[str] = []

        self._page_title = ""
        self._page_url = ""

        self._chunk_index = 0

    # ------------------------------------------------------
    # Public
    # ------------------------------------------------------

    def chunk(
        self,
        page: WikiPage,
    ) -> list[Chunk]:

        self._chunks.clear()

        self._buffer.clear()

        self._images.clear()

        self._page_title = unquote(
            page.title
        )

        self._page_url = (
                "https://ru.wikipedia.org/wiki/"
                + quote(
            page.title.replace(" ", "_"),
            safe="()"
            )
        )

        self._chunk_index = 0

        for section in page.sections:
            self._walk_section(
                section,
                [],
            )

        self._flush([])

        return self._chunks

    # ------------------------------------------------------
    # Recursive traversal
    # ------------------------------------------------------

    def _walk_section(
        self,
        section: Section,
        path: list[str],
    ):

        current_path = path.copy()

        if section.title:
            current_path.append(section.title or "Введение")

        for block in section.blocks:

            # -----------------------------
            # Paragraph
            # -----------------------------

            if isinstance(block, Paragraph):

                self._add_text(
                    block.text,
                    current_path,
                )

            # -----------------------------
            # Image
            # -----------------------------

            elif isinstance(block, Image):

                if block.url:
                    self._images.append(block.url)

            # -----------------------------
            # List
            # -----------------------------

            elif isinstance(block, ListBlock):

                text = "\n".join(
                    f"- {item}"
                    for item in block.items
                )

                self._add_text(
                    text,
                    current_path,
                )

            # -----------------------------
            # Table
            # -----------------------------

            elif isinstance(block, Table):

                rows = [
                    " | ".join(row)
                    for row in block.rows
                ]

                self._add_text(
                    "\n".join(rows),
                    current_path,
                )

                self._images.extend(block.images)

        for child in section.children:
            self._walk_section(
                child,
                current_path,
            )

        self._flush(current_path)

    # ------------------------------------------------------
    # Buffer
    # ------------------------------------------------------

    def _add_text(
        self,
        text: str,
        path: list[str],
    ):

        current = "\n\n".join(
            self._buffer
        )

        future = len(current) + len(text)

        if (
            self._buffer
            and future > self.max_chars
        ):
            self._flush(path)

        self._buffer.append(text)

    def _flush(
        self,
        path: list[str],
    ):

        if not self._buffer:
            return

        self._chunks.append(

            Chunk(

                text="\n\n".join(
                    self._buffer
                ),

                metadata=ChunkMetadata(

                    page_title=self._page_title,

                    section_path=path.copy(),

                    chunk_index=self._chunk_index,

                    source="Wikipedia",

                    url=self._page_url,

                    images=self._images.copy(),
                ),
            )
        )

        self._chunk_index += 1
        self._buffer.clear()
        self._images.clear()


# # Пример использования
# parser = WikipediaParser()
# page = parser.parse("Австрия")
#
# chunker = WikipediaChunker(
#     max_chars=1200,
# )
#
# chunks = chunker.chunk(page)
# for chunk in chunks:
#     print("=" * 80)
#     print(chunk.metadata.section_path)
#     print(chunk.metadata.images)
#     print(chunk.text[:1200])
#     print(chunk.metadata.url)