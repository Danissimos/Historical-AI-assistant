from __future__ import annotations

import hashlib
from urllib.parse import unquote

from src.graph.models import Graph


class GraphBuilder:
    """
    Построение графа из документа Википедии и списка чанков.
    """

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.md5(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_url(url: str | None) -> str | None:
        if not url:
            return url

        if url.startswith("//"):
            return "https:" + url

        return url

    def build(
            self,
            page,
            chunks,
    ) -> Graph:

        graph = Graph()

        page_title = unquote(page.title)

        # -------------------------------------------------
        # Document
        # -------------------------------------------------

        document = graph.add_vertex(
            label="Document",
            id=page_title,
            title=page_title,
            url=getattr(page, "url", None),
        )

        section_index = {}

        # -------------------------------------------------
        # Sections
        # -------------------------------------------------

        def add_sections(parent_vertex, sections, parent_path):

            for section in sections:
                title = section.title or "Введение"
                path = parent_path + [title]

                section_id = (
                    page_title
                    if not path
                    else page_title + "/" + "/".join(path)
                )

                section_vertex = graph.add_vertex(
                    label="Section",
                    id=section_id,
                    title=section.title,
                    path="/".join(path),
                    level=len(path),
                )

                section_index["/".join(path)] = section_vertex

                graph.add_edge(
                    parent_vertex,
                    "HAS_SECTION",
                    section_vertex,
                )

                add_sections(
                    section_vertex,
                    section.children,
                    path,
                )

        add_sections(
            document,
            page.sections,
            [],
        )

        # -------------------------------------------------
        # Chunks
        # -------------------------------------------------

        for chunk in chunks:

            chunk_id = f"{page_title}:{chunk.metadata.chunk_index}"
            section_path = "/".join(chunk.metadata.section_path)

            chunk_vertex = graph.add_vertex(
                label="Chunk",
                id=chunk_id,
                index=chunk.metadata.chunk_index,
                page=page_title,
                section=section_path,
            )


            if section_path:

                parent = section_index.get(section_path)

                if parent:

                    graph.add_edge(
                        parent,
                        "HAS_CHUNK",
                        chunk_vertex,
                    )

                else:

                    graph.add_edge(
                        document,
                        "HAS_CHUNK",
                        chunk_vertex,
                    )

            else:

                graph.add_edge(
                    document,
                    "HAS_CHUNK",
                    chunk_vertex,
                )

            # ---------------------------------------------
            # Images
            # ---------------------------------------------

            for image_url in chunk.metadata.images:
                image_url = self._normalize_url(image_url)

                image = graph.add_vertex(
                    label="Image",
                    id=f"{page_title}:image:{len(graph.vertices)}",
                    url=image_url,
                )

                graph.add_edge(
                    chunk_vertex,
                    "HAS_IMAGE",
                    image,
                )

        # # -------------------------------------------------
        # # Document links
        # # -------------------------------------------------
        #
        # for link in page.links:
        #     target = graph.add_vertex(
        #         label="Document",
        #         id=link.title,
        #         title=link.title,
        #     )
        #
        #     graph.add_edge(
        #         document,
        #         "LINKS_TO",
        #         target,
        #     )

        return graph