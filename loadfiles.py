import os
import redis
import re

r = redis.Redis(host = 'localhost', port = 6379, db = 0)


def carga(path):
    files = os.listdir(path)
    for file in files:
        match = re.match(r'^book(\d+).html$', file)
        if match:
            with open(path + file) as f:
                html = f.read()
                r.set(match.group(1), html)
            print(match.group(0), match.group(1))

carga('html/books/')

