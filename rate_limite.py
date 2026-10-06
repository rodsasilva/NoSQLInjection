#!/usr/bin/env python3

import argparse
import queue
import sqlite3
import sys
import threading
import time
from pathlib import Path


class Database:
    def __init__(self, database="files.db"):
        self.database = database
        self._db_lock = threading.Lock()
        self._create_table()

    def _create_connection(self):
        try:
            return sqlite3.connect(
                self.database,
                timeout=30,
            )
        except sqlite3.Error as exc:
            print(f"[ERRO] Não foi possível abrir o SQLite: {exc}")
            sys.exit(1)

    def _create_table(self):
        conn = self._create_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    character TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    UNIQUE(name, position)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS files_size (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    size INTEGER NOT NULL
                )
                """
            )

            conn.commit()

        finally:
            conn.close()

    def insert_character(self, data):
        with self._db_lock:
            conn = self._create_connection()

            try:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO files
                    (name, character, position)
                    VALUES (?, ?, ?)
                    """,
                    data,
                )

                conn.commit()
                return cursor.lastrowid

            finally:
                conn.close()

    def insert_file_size(self, data):
        with self._db_lock:
            conn = self._create_connection()

            try:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO files_size
                    (name, size)
                    VALUES (?, ?)
                    """,
                    data,
                )

                conn.commit()
                return cursor.lastrowid

            finally:
                conn.close()

    def exists_character_by_position(self, data):
        conn = self._create_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 1
                FROM files
                WHERE name = ? AND position = ?
                LIMIT 1
                """,
                data,
            )

            return cursor.fetchone() is not None

        finally:
            conn.close()

    def get_file_size(self, data):
        conn = self._create_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT size
                FROM files_size
                WHERE name = ?
                LIMIT 1
                """,
                data,
            )

            row = cursor.fetchone()

            return row[0] if row else 0

        finally:
            conn.close()

    def get_downloaded_quantity(self, data):
        conn = self._create_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT MAX(position)
                FROM files
                WHERE name = ?
                """,
                data,
            )

            row = cursor.fetchone()

            if row and row[0] is not None:
                return row[0]

            return 0

        finally:
            conn.close()

    def print_archive(self, data):
        conn = self._create_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT character
                FROM files
                WHERE name = ?
                ORDER BY position
                """,
                data,
            )

            rows = cursor.fetchall()

            return "".join(
                row[0]
                for row in rows
            )

        finally:
            conn.close()


class LocalFileWorker(threading.Thread):
    """
    Worker para importar um arquivo LOCAL autorizado
    para o SQLite, preservando a lógica de threads.
    """

    def __init__(
        self,
        work_queue,
        source_data,
        archive_name,
        database,
        worker_id,
        print_lock,
    ):
        super().__init__(daemon=True)

        self.work_queue = work_queue
        self.source_data = source_data
        self.archive_name = archive_name
        self.database = database
        self.worker_id = worker_id
        self.print_lock = print_lock

    def run(self):

        while True:

            try:
                position = self.work_queue.get_nowait()

            except queue.Empty:
                return

            try:

                if not self.database.exists_character_by_position(
                    (
                        self.archive_name,
                        position,
                    )
                ):

                    char = self.source_data[position - 1]

                    self.database.insert_character(
                        (
                            self.archive_name,
                            char,
                            position,
                        )
                    )

            except Exception as exc:

                with self.print_lock:
                    print(
                        f"[ERRO] "
                        f"Thread={self.worker_id} "
                        f"Posição={position} "
                        f"Erro={exc}"
                    )

            finally:
                self.work_queue.task_done()


def import_local_file(
    source_path,
    archive_name,
    threads,
    database,
):
    source = Path(source_path)

    if not source.is_file():
        raise FileNotFoundError(
            f"Arquivo local não encontrado: {source}"
        )

    data = source.read_text(
        encoding="utf-8",
        errors="replace",
    )

    database.insert_file_size(
        (
            archive_name,
            len(data),
        )
    )

    work_queue = queue.Queue()

    for position in range(
        1,
        len(data) + 1,
    ):
        work_queue.put(position)

    print_lock = threading.Lock()
    workers = []

    for worker_id in range(
        1,
        threads + 1,
    ):

        worker = LocalFileWorker(
            work_queue=work_queue,
            source_data=data,
            archive_name=archive_name,
            database=database,
            worker_id=worker_id,
            print_lock=print_lock,
        )

        worker.start()
        workers.append(worker)

    while any(
        worker.is_alive()
        for worker in workers
    ):

        downloaded = database.get_downloaded_quantity(
            (archive_name,)
        )

        print(
            f"\r[PROGRESS] "
            f"{downloaded}/{len(data)}",
            end="",
            flush=True,
        )

        time.sleep(0.2)

    for worker in workers:
        worker.join()

    print()

    print(
        f"[+] Arquivo importado: {source}"
    )

    print(
        f"[+] Tamanho: {len(data)} bytes"
    )


def show_from_database(
    archive_name,
    database,
):
    stored_size = database.get_file_size(
        (archive_name,)
    )

    downloaded = database.get_downloaded_quantity(
        (archive_name,)
    )

    if downloaded == 0:

        print(
            "[!] Não existem dados armazenados "
            f"para: {archive_name}"
        )

        return

    print()

    print(
        f"File size: "
        f"{stored_size or downloaded} bytes"
    )

    print()

    print(
        database.print_archive(
            (archive_name,)
        )
    )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Ferramenta de laboratório para "
            "armazenamento e consulta de arquivos "
            "no SQLite."
        )
    )

    parser.add_argument(
        "-f",
        "--file",
        required=True,
        help=(
            "Nome usado para identificar o "
            "conteúdo no SQLite."
        ),
    )

    parser.add_argument(
        "-u",
        "--url",
        help=(
            "URL do laboratório. "
            "A extração remota não é implementada."
        ),
    )

    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=1,
        help=(
            "Número de threads para importação "
            "local. Padrão: 1."
        ),
    )

    parser.add_argument(
        "--local-source",
        help=(
            "Arquivo local autorizado para importar "
            "no SQLite."
        ),
    )

    parser.add_argument(
        "--database",
        default="files.db",
        help=(
            "Arquivo SQLite. "
            "Padrão: files.db"
        ),
    )

    args = parser.parse_args()

    if args.threads < 1:
        parser.error(
            "--threads deve ser maior que zero."
        )

    database = Database(
        args.database
    )

    print("=" * 60)
    print("EXTRACT FILES - LABORATÓRIO")
    print("=" * 60)

    print(
        f"Arquivo : {args.file}"
    )

    print(
        f"Threads : {args.threads}"
    )

    print(
        f"SQLite  : {args.database}"
    )

    if args.url:
        print(
            f"URL     : {args.url}"
        )

    print("=" * 60)

    # ---------------------------------------------------------
    # IMPORTAÇÃO DE ARQUIVO LOCAL
    # ---------------------------------------------------------

    if args.local_source:

        try:

            import_local_file(
                source_path=args.local_source,
                archive_name=args.file,
                threads=args.threads,
                database=database,
            )

            print()

            show_from_database(
                args.file,
                database,
            )

        except (
            OSError,
            UnicodeError,
            ValueError,
        ) as exc:

            print(
                f"[ERRO] {exc}"
            )

            sys.exit(1)

        return

    # ---------------------------------------------------------
    # URL INFORMADA
    # ---------------------------------------------------------

    if args.url:

        print()

        print(
            "[!] A extração remota via SQL "
            "Injection/LOAD_FILE não está "
            "implementada nesta versão."
        )

        print()

        print(
            "[i] Para testar SQLite + threads, "
            "use --local-source."
        )

        return

    # ---------------------------------------------------------
    # CONSULTA DO SQLITE
    # ---------------------------------------------------------

    show_from_database(
        args.file,
        database,
    )


if __name__ == "__main__":
    main()