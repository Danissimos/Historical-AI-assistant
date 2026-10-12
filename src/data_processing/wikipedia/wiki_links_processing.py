from dataclasses import dataclass, field
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag


# ==========================================================
# Models
# ==========================================================

@dataclass
class Paragraph:
    text: str
    type: str = "paragraph"


@dataclass
class Image:
    url: str | None
    caption: str | None
    type: str = "image"


@dataclass
class Table:
    rows: list[list[str]]
    table_type: str | None = None
    images: list[str] = field(default_factory=list)
    type: str = "table"


@dataclass
class ListBlock:
    items: list[str]
    ordered: bool
    type: str = "list"


@dataclass
class Section:
    title: str | None

    blocks: list[Any] = field(default_factory=list)

    children: list["Section"] = field(
        default_factory=list
    )


@dataclass
class WikiPage:
    title: str
    sections: list[Section]



# ==========================================================
# Parser
# ==========================================================

class WikipediaParser:

    BASE_URL = (
        "https://ru.wikipedia.org/"
        "api/rest_v1/page/html/{}"
    )

    HEADERS = {
        "User-Agent": (
            "HistoricalAIAssistant/0.1 "
            "(Research project for local use and education; "
            "contact: ghj228822@gmail.com)"
        )
    }

    def parse(self, title: str) -> WikiPage:
        """
        Главная точка входа.
        """

        soup = self._get_soup(title)

        self._clean_html(soup)

        sections = []

        for section in soup.body.find_all(
            "section",
            recursive=False
        ):
            sections.append(
                self._parse_section(section)
            )

        return WikiPage(
            title=title,
            sections=sections,
        )


    # ------------------------------------------------------
    # HTTP
    # ------------------------------------------------------

    def _get_soup(
        self,
        title: str,
    ) -> BeautifulSoup:

        response = requests.get(
            self.BASE_URL.format(title),
            headers=self.HEADERS,
            timeout=30,
        )

        response.raise_for_status()

        return BeautifulSoup(
            response.text,
            "html.parser",
        )


    # ------------------------------------------------------
    # Cleaning
    # ------------------------------------------------------

    @staticmethod
    def _clean_html(
        soup: BeautifulSoup,
    ):

        selectors = [
            "sup.reference",
            ".mw-editsection",
            ".navbox",
        ]

        for selector in selectors:

            for tag in soup.select(selector):
                tag.decompose()


        for tag in soup.find_all(
            ["style", "script"]
        ):
            tag.decompose()



    # ------------------------------------------------------
    # Helpers
    # ------------------------------------------------------

    @staticmethod
    def _text(
        element: Tag | None,
    ) -> str:

        if element is None:
            return ""

        return " ".join(
            element.stripped_strings
        )


    # ------------------------------------------------------
    # Section parsing
    # ------------------------------------------------------

    def _parse_section(
        self,
        section: Tag,
    ) -> Section:


        heading = section.find(
            [
                "h2",
                "h3",
                "h4",
                "h5",
            ],
            recursive=False,
        )


        title = (
            self._text(heading)
            if heading
            else None
        )


        result = Section(
            title=title,
        )


        for child in section.find_all(
            recursive=False
        ):

            if not isinstance(child, Tag):
                continue


            if child.name in {
                "h2",
                "h3",
                "h4",
                "h5",
            }:
                continue


            if child.name == "section":

                result.children.append(
                    self._parse_section(child)
                )

            else:

                block = self._parse_block(child)

                if block:
                    result.blocks.append(block)


        return result



    # ------------------------------------------------------
    # Blocks
    # ------------------------------------------------------

    def _parse_block(
        self,
        tag: Tag,
    ):


        # -------------------------
        # Paragraph
        # -------------------------

        if tag.name == "p":

            value = self._text(tag)

            if value:

                return Paragraph(
                    text=value
                )


        # -------------------------
        # Image
        # -------------------------

        if tag.name == "figure":

            img = tag.find("img")

            caption = tag.find(
                "figcaption"
            )


            return Image(
                url=(
                    img.get("src")
                    if img
                    else None
                ),
                caption=(
                    self._text(caption)
                    if caption
                    else None
                ),
            )


        # -------------------------
        # Table
        # -------------------------

        if tag.name == "table":

            rows = []

            for tr in tag.find_all("tr"):

                row = [
                    self._text(cell)
                    for cell in tr.find_all(
                        [
                            "td",
                            "th",
                        ]
                    )
                ]

                if row:
                    rows.append(row)


            classes = tag.get(
                "class",
                []
            )


            table_type = None

            if "infobox" in classes:
                table_type = "infobox"

            elif "wikitable" in classes:
                table_type = "wikitable"

            images = []

            for img in tag.find_all("img"):

                url = img.get("src")

                if not url:
                    continue

                if url.startswith("//"):
                    url = "https:" + url

                images.append(url)

            return Table(
                rows=rows,
                images=images,
                table_type=table_type,
            )


        # -------------------------
        # Lists
        # -------------------------

        if tag.name in {
            "ul",
            "ol",
        }:

            items = [
                self._text(li)
                for li in tag.find_all(
                    "li",
                    recursive=False,
                )
            ]


            return ListBlock(
                items=items,
                ordered=tag.name == "ol",
            )

        return None


# =========================================
# Пример использования
# =========================================
# parser = WikipediaParser()
# page = parser.parse("Австрия")
#
# print(page.title)


# чекаем секции
# for section in page.sections:
#
#     print(section.title)
#
#     for block in section.blocks:
#         print(
#             "   ",
#             block.type
#         )


# Чекаем вложенные секции
# section = next(
#     s
#     for s in page.sections
#     if s.title == "Культура"
# )
#
# print(section.title)
# print(len(section.blocks))
# print(len(section.children))
#
# for child in section.children:
#     print(child.title)