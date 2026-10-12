import time
import requests
from datetime import datetime
from pathlib import Path
from time import perf_counter
from urllib.parse import urlparse, unquote, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from src.data_processing.wikipedia.wiki_links_processing import WikipediaParser
from src.data_processing.wikipedia.wiki_article_processing import WikipediaChunker
from src.data_processing.wikipedia.wiki_articles_saving import WikipediaStorage
from src.graph.graph_builder import GraphBuilder
from src.graph.age_repository import AgeRepository
from src.utils.db import get_engine


# ---------------------------------------------------------
# Num of links to parse
# ---------------------------------------------------------
start_idx = 10000
end_idx = 15740

# ---------------------------------------------------------
# Max parallel flows
# ---------------------------------------------------------
MAX_WORKERS = 6

# ---------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------

MAX_RETRIES = 5
REQUEST_DELAY = 1

# ---------------------------------------------------------
# Statistics
# ---------------------------------------------------------
stats_lock = Lock()

processed = 0
last_reported = 0

parse_time = 0.0
chunk_time = 0.0
storage_time = 0.0
graph_build_time = 0.0
graph_save_time = 0.0

images_downloaded = 0
retries_429 = 0


def parse_with_retry(parser, title: str):
    global retries_429
    delay = 1.0

    for attempt in range(MAX_RETRIES):

        try:

            page = parser.parse(title)

            # небольшая пауза после каждого успешного запроса
            time.sleep(REQUEST_DELAY)


            return page

        except requests.HTTPError as e:

            response = e.response

            if (
                response is not None
                and response.status_code == 429
            ):
                retries_429 += 1

                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    wait = min(float(retry_after), 1.0)  # максимум 1 секунда
                else:
                    wait = 1.0

                print(
                    f"[429] {title} | "
                    f"retry in {wait:.1f}s "
                    f"({attempt + 1}/{MAX_RETRIES})"
                )

                time.sleep(wait)
                continue

            raise

        except requests.RequestException:

            if attempt == MAX_RETRIES - 1:
                raise

            print(
                f"[Retry] {title} | "
                f"retry in {delay:.1f}s "
                f"({attempt + 1}/{MAX_RETRIES})"
            )

            time.sleep(delay)
            delay *= 2


    raise RuntimeError(
        f"Maximum retries exceeded: {title}"
    )


def process_url(url: str) -> bool:
    global parse_time
    global chunk_time
    global storage_time
    global graph_build_time
    global graph_save_time
    global images_downloaded

    try:

        path = urlparse(url).path
        title = unquote(path.removeprefix("/wiki/"))

        parser = WikipediaParser()

        chunker = WikipediaChunker(
            max_chars=1200,
        )

        storage = WikipediaStorage(
            engine,
        )

        graph_builder = GraphBuilder()

        age_repository = AgeRepository(
            engine_graph_db,
        )

        # -----------------------------
        # Parse
        # -----------------------------

        t = perf_counter()
        page = parse_with_retry(
            parser,
            quote(title, safe=""),
        )
        parse_elapsed = perf_counter() - t

        if page is None or not page.sections:
            return False

        # -----------------------------
        # Chunk
        # -----------------------------

        t = perf_counter()
        chunks = chunker.chunk(page)
        chunk_elapsed = perf_counter() - t

        if not chunks:
            return False

        images = sum(
            len(chunk.metadata.images)
            for chunk in chunks
        )

        # -----------------------------
        # Storage
        # -----------------------------

        t = perf_counter()
        storage.save(chunks)
        storage_elapsed = perf_counter() - t

        # -----------------------------
        # Graph build
        # -----------------------------

        t = perf_counter()
        graph = graph_builder.build(page, chunks)
        graph_build_elapsed = perf_counter() - t

        # -----------------------------
        # Graph save
        # -----------------------------

        t = perf_counter()
        age_repository.save(graph)
        graph_save_elapsed = perf_counter() - t

        # -----------------------------
        # Statistics
        # -----------------------------

        with stats_lock:

            global processed

            processed += 1

            parse_time += parse_elapsed
            chunk_time += chunk_elapsed
            storage_time += storage_elapsed
            graph_build_time += graph_build_elapsed
            graph_save_time += graph_save_elapsed

            images_downloaded += images

        return True

    except Exception as ex:

        print(f"[ERROR] {url}")
        print(ex)

        return False


# ---------------------------------------------------------
# Config
# ---------------------------------------------------------

env_path = Path(__file__).resolve().parents[2] / "src/env"

engine = get_engine(env_path / ".env")
engine_graph_db = get_engine(env_path / "graph_db.env")

links_file = (
    Path(__file__).resolve().parents[2]
    / "data/raw/wiki/wiki_links.txt"
)

# ---------------------------------------------------------
# Read links
# ---------------------------------------------------------

with open(links_file, encoding="utf-8") as f:
    links = [
        line.strip()
        for line in f
        if line.strip()
    ]

links = links[start_idx:end_idx]

# ---------------------------------------------------------
# Processing
# ---------------------------------------------------------

start_time = datetime.now()
last_checkpoint = start_time

processed = 0

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

    futures = [
        executor.submit(process_url, url)
        for url in links
    ]

    last_reported = 0

    for future in as_completed(futures):

        future.result()

        with stats_lock:

            current_processed = processed

            if current_processed - last_reported >= 100:
                last_reported = current_processed

                current_parse = parse_time
                current_chunk = chunk_time
                current_storage = storage_time
                current_graph_build = graph_build_time
                current_graph_save = graph_save_time
                current_images = images_downloaded
                current_retries = retries_429

        if current_processed - last_reported == 0:
            now = datetime.now()

            print("=" * 80)
            print(f"Current time : {now:%Y-%m-%d %H:%M:%S}")
            print(f"Processed    : {current_processed}")
            print(f"Elapsed      : {now - start_time}")
            print(f"Last 100     : {now - last_checkpoint}")
            print()

            print(f"Parse        : {current_parse:.2f}s")
            print(f"Chunk        : {current_chunk:.2f}s")
            print(f"Storage      : {current_storage:.2f}s")
            print(f"Graph build  : {current_graph_build:.2f}s")
            print(f"Graph save   : {current_graph_save:.2f}s")
            print()

            print(f"429 retries  : {current_retries}")
            print(f"Images       : {current_images}")
            print("=" * 80)

            last_checkpoint = now

        with stats_lock:
            parse_time = 0.0
            chunk_time = 0.0
            storage_time = 0.0
            graph_build_time = 0.0
            graph_save_time = 0.0
            images_downloaded = 0
            retries_429 = 0


now = datetime.now()

print("=" * 80)
print('Итоговая статистика\n')
print(f"Current time : {now:%Y-%m-%d %H:%M:%S}")
print(f"Processed    : {processed}")
print(f"Elapsed      : {now - start_time}")
print(f"Last 100     : {now - last_checkpoint}")
print()














# from src.data_processing.wikipedia.wiki_links_processing import WikipediaParser
# from src.data_processing.wikipedia.wiki_article_processing import WikipediaChunker
# from src.data_processing.wikipedia.wiki_articles_saving import WikipediaStorage
# from src.graph.graph_builder import GraphBuilder
# from src.graph.age_repository import AgeRepository
# from src.utils.db import get_engine
#
# from pathlib import Path



# # ==================================================================================
# # Базовая работа на примере
# # ==================================================================================
# env_path = Path(__file__).resolve().parents[2] / "src/utils/"
# engine = get_engine(env_path / ".env")
# engine_graph_db = get_engine(env_path/ "graph_db.env")
#
# parser = WikipediaParser()
#
#
# chunker = WikipediaChunker(
#     max_chars=1200
# )
#
#
# storage = WikipediaStorage(
#     engine
# )
#
#
# graph_builder = GraphBuilder()
#
#
# age_repository = AgeRepository(
#     engine_graph_db
# )
#
#
# page = parser.parse(
#     "Австрия"
# )
#
#
# chunks = chunker.chunk(
#     page
# )
#
#
# storage.save(
#     chunks
# )
#
#
# graph = graph_builder.build(
#     page,
#     chunks
# )
#
# age_repository.save(
#     graph
# )



# # ==================================================================================
# # Вывод вершин и связей
# # ==================================================================================
# print("=" * 100)
# print(f"Vertices: {graph.vertex_count}")
# print(f"Edges: {graph.edge_count}")
# print("=" * 100)
#
# for edge in sorted(
#     graph.edges,
#     key=lambda e: (
#         e.source_label,
#         e.source_id,
#         e.relationship,
#         e.target_label,
#         e.target_id,
#     ),
# ):
#     print(
#         f"({edge.source_label}:{edge.source_id}) "
#         f"-[{edge.relationship}]-> "
#         f"({edge.target_label}:{edge.target_id})"
#     )


# # # ==================================================================================
# # # Вывод вершин и связей + свойства
# # # ==================================================================================
# print("=" * 100)
# print("VERTICES")
# print("=" * 100)
#
# for vertex in sorted(
#     graph.vertices,
#     key=lambda v: (v.label, v.id),
# ):
#     print(
#         f"{vertex.label:<10} {vertex.id}"
#     )
#     print(vertex.properties)
#     print()



# # ==================================================================================
# # Вывод вершин и связей в виде графа
# # ==================================================================================
# from collections import defaultdict
#
# tree = defaultdict(list)
#
# for edge in graph.edges:
#     tree[(edge.source_label, edge.source_id)].append(edge)
#
# root = ("Document", page.title)
#
# def walk(node, indent=0):
#     print(" " * indent + f"{node[0]}: {node[1]}")
#
#     for edge in sorted(
#         tree.get(node, []),
#         key=lambda e: (
#             e.relationship,
#             e.target_label,
#             e.target_id,
#         ),
#     ):
#         print(" " * (indent + 2) + f"|-- {edge.relationship}")
#         walk(
#             (edge.target_label, edge.target_id),
#             indent + 6,
#         )
#
# walk(root)





# ============================================================================
# Рабочая версия, но без формирования графов.
# ============================================================================
# engine = get_engine()
#
# # ---------------------------------------------------------
# # Создаем объекты
# # ---------------------------------------------------------
#
# parser = WikipediaParser()
#
# chunker = WikipediaChunker(
#     max_chars=1200,
# )
#
# storage = WikipediaStorage(
#     engine=engine,
# )
#
# # ---------------------------------------------------------
# # Парсим страницу
# # ---------------------------------------------------------
#
# page = parser.parse("Австрия")
#
# # ---------------------------------------------------------
# # Разбиваем на чанки
# # ---------------------------------------------------------
#
# chunks = chunker.chunk(page)
#
# print(f"Получено {len(chunks)} чанков")
#
# # ---------------------------------------------------------
# # Сохраняем
# # ---------------------------------------------------------
#
# storage.save(chunks)
#
# print("Готово!")