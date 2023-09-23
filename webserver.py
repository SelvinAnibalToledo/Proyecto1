from functools import cached_property
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse
import re
import redis
import uuid

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses = True)

class WebRequestHandler(BaseHTTPRequestHandler):

    @cached_property
    def cookies(self):
        return SimpleCookie(self.headers.get("Cookie"))

    def do_GET(self):
        self.url = urlparse(self.path)
#        bookid = re.findall(r'^/Books/(\d+)$',self.url.path)
#        strbookid = "".join(bookid)
#        print(strbookid)
        method = self.get_metodo(self.url.path)
        if method:
            method_name, dict_params = method 
            method = getattr(self, method_name)
            method(**dict_params)
            return
        else:
            self.send_error(404, "Not found")
    
    def set_cookie(self, sesion):
        sc = SimpleCookie()
        sc["session"] = sesion
        sc["session"]["max_age"] = 10
        self.send_header('Set-Cookie', sc.output(headers = '')) #considerar otra manera de hacer


    def obtiene_cookie(self):
        cookie = self.cookies
        if not cookie:
            cookie = SimpleCookie()
            cookie["session"] = uuid.uuid4() # Se agrega identificador unico
        else:
            print("Ya existe cookie")
        return cookie.get("session").value # Siempre se retorna el obj.value


    def get_response(self,bookid):
#        r = redis.Redis(host='localhost', decode_responses = True)
        ruta = 'book' + (bookid)
        print(r.exists(ruta))
        if r.exists(ruta) == 1:
            return f"""
            {r.hgetall('book' + bookid)}
            """
        if r.exists(ruta) == 0:
            return f"""
            {'NO EXISTE'}
            """

    def inserta_sesion(self,sesion,book_id):
        r.rpush(sesion,book_id)

    def get_recomienda(self,sesion,book_id):
        indice = 1
        llaves = r.dbsize()
        print(llaves)
        total_libros = []
        while indice <= llaves:
            if r.exists((indice)) == 1:
                total_libros.append(indice)
                indice += 1
        print(total_libros)



    def get_book(self,book_id):
        book_page = r.get(book_id)
        sesion = self.obtiene_cookie()
       # self.inserta_sesion(sesion,book_id)
        recomienda = self.get_recomienda(sesion,book_id)
        if book_page:    
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
       #     self.set_cookie(sesion)
            self.end_headers()
            response = f"""
            {book_page}
            <p> Ruta: {self.path} <p>
            <p> URL: {self.url} <p>
            <p> Sesion: {sesion} <p>
            <p> Recomendacion: {recomienda} <p>
            """
            self.wfile.write(response.encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def get_inicio(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        with open('html/index.html') as f:
            response = f.read()
        self.wfile.write(response.encode("utf-8"))



    def get_metodo(self,path):
        for pattern, method in mapping:
            match = re.match(pattern, path)
            if match:
                return (method, match.groupdict())


mapping = [
           (r'^/Books/(?P<book_id>\d+)$', 'get_book'),
           (r'/$', 'get_inicio'),
          ]


if __name__ == "__main__":
    print("Server starting...")
    server = HTTPServer(("0.0.0.0", 80), WebRequestHandler)
    server.serve_forever()
