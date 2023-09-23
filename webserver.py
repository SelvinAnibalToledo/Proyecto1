from functools import cached_property
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse
import re
import redis

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses = True)

class WebRequestHandler(BaseHTTPRequestHandler):




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

    def get_book(self,book_id):
        book_page = r.get(book_id)
        if book_page:    
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            response = f"""
            {book_page}
            <p> Ruta: {self.path} <p>
            <p> URL: {self.url} <p>
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
