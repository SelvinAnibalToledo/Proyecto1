import os
import redis
import re
from bs4 import BeautifulSoup

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
    cargalibros()

def cargalibros():
    obj = 'html.parser'
    indice = 1
    encontrado = 1
    llaves = r.dbsize()
    total_libros = []
    while indice <= llaves:
        if r.exists(indice) == encontrado:
            html_bruto = BeautifulSoup(r.get(indice), obj)
            html_solo_texto = html_bruto.get_text()
            x = html_solo_texto.split(' ')

            for text in x:
                r.sadd(text, indice)
            indice += 1
   

carga('html/books/')

