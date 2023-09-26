from functools import cached_property
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse
from bs4 import BeautifulSoup
import re
import redis
import uuid

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses = True)

class WebRequestHandler(BaseHTTPRequestHandler):

    @cached_property
    def cookies(self):
        return SimpleCookie(self.headers.get("Cookie"))

    @cached_property
    def query_data(self):
        return dict(parse_qsl(self.url.query))

    def do_GET(self):
        self.url = urlparse(self.path)
#        bookid = re.findall(r'^/Books/(\d+)$',self.url.path)
#        strbookid = "".join(bookid)
#        print(strbookid)
        method = self.get_metodo(self.url.path)
        print("path: " + str(self.url.path))
        if method:
            method_name, dict_params = method 
            method = getattr(self, method_name)
            method(**dict_params)
            return
        else:
            self.send_error(404, "Not found")
    
    def set_cookie(self, sesion,max_age=10):
        sc = SimpleCookie()
        sc["session"] = sesion
        sc["session"]["max-age"] = max_age
        self.send_header('Set-Cookie', sc.output(header='')) #considerar otra manera de hacer


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
        print("sesion:" + str(sesion))
        print("libro" + str(book_id))
       # if r.exists se repiten numeros
        r.rpush(sesion,book_id)

    def get_recomienda(self,sesion,book_id):
        indice = 1
        llaves = r.dbsize()
        #print(llaves)
        total_libros = []
        while indice <= llaves:
            if r.exists((indice)) == 1:
                total_libros.append(str(indice))
                indice += 1
            else:
                break
        
        libros_visitados = r.lrange(sesion,0,indice)
       
        print("TOTAL DE LIBROS: " + str(total_libros))
        print("LIBROS VISITADOS: " + str(libros_visitados))


        recomendacion = [b for b in total_libros if b not in 
                [libros for libros in libros_visitados]]

        #print(indice)
        #print(libros_visitados)
        mensaje = ''
        if recomendacion:
            for i in (recomendacion):
                if i == '1':
                    mensaje += ' Los Miserables '
                elif i == '2':
                    mensaje += ' El principito '
                elif i == '3':
                    mensaje += ' El padrino '
                elif i == '4':
                    mensaje += ' Habitos atomicos '
            return 'le recomendamos leer los siguientes libros: ' + mensaje 
            #return recomendacion #Mandar un mejor mensaje de libros a leer utilizar: BeatifulShop
        else: 
            return "Has leido todos los libros"
        #print(total_libros)



    def get_book(self,book_id):
        book_page = r.get(book_id)
        sesion = self.obtiene_cookie()
        self.inserta_sesion(sesion,book_id)
        recomienda = self.get_recomienda(sesion,book_id)
        if book_page:    
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.set_cookie(sesion)
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


    def get_html(self):
        #print('entre ak metoodoooooo')
        obj1 = 'html.parser'
        #html_bruto = BeautifulSoup(r.get(1), obj1)
        #html_solo_texto = html_bruto.get_text()
        #Se necesita hacer un sadd para agregar la llave de la busqueda y lo que quieres buscar
        #Despues se necesita dividir todo el texto resultante de los libros en otras saad
        #para despues hacer un sinter y ver si coinciden
        indice = 1
        llaves = r.dbsize()
        print('estoy en html, antes de iniciar el while')
        total_libros_found = []
        while indice <= llaves:
            if r.exists((indice)) == 1:
                html_bruto = BeautifulSoup(r.get(indice), obj1)
                html_solo_texto = html_bruto.get_text()
                print('cree el beatifulsoup')
                #r.sadd('libro' + str(indice),html_solo_texto)
                x = html_solo_texto.split(' ')
                print(x)
                self.getprueba(x,indice)
                #r.sadd('unos',x)
                #print('despues de agregar')
                r.sadd('busca',)#aqui agregar los parametros de busqueda
                busqueda = r.sinter('libro'+str(indice),'busca')
                #print('buscando el jean')
                if busqueda:
                    total_libros_found.append(str(indice))
                indice += 1
            else:
                break

        #print('entre al metodo' + html_bruto.get_text())
        #return html_solo_texto
        return total_libros_found

    def getprueba(self):
        #html = BeautifulSoup(r.get(1), 'html.parse')
        #html1 = html.get_text()
        #texto = 'Soy Selvin Anibal Toledo'
        #delim = ' '
        #x = texto.split(delim)
        #print(x)
        mensaje = ''
        res = None
        if self.query_data and 'busca' in self.query_data:
            res = r.sinter(self.query_data['busca'].split(' '))
            print(res)
        
            for i in (res):
                if i == '1':
                    mensaje += ' Los Miserables '
                elif i == '2':
                    mensaje += ' El principito '
                elif i == '3':
                    mensaje += ' El padrino '
                elif i == '4':
                    mensaje += ' Habitos atomicos '
        #return 'le recomendamos leer los siguientes libros: ' + mensaje 
        
        if not mensaje:
            mensaje = 'NO SE ENCONTRO EN NINGUN LIBRO'
            return mensaje
        else:
            return 'Se encontro en: ' + mensaje 



    def get_busqueda(self):
        print('Estoy en la busqueda')
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        #res = self.get_html()
        #res = self.getprueba()
        self.getprueba()
        response = f"""
        <h1>BUSQUEDA</h1>
        <p>USED BUSCO: {self.query_data['busca'].split(' ')}<p>
        <p> el resultado de la busqueda es: <p>
        <p>{self.getprueba()}<p>
        """
       #self.wfile.write() 
        self.wfile.write(response.encode("utf-8"))
        #print('Hola, estoy en la busqueda' + str(self.query_data))


    def get_metodo(self,path):
        for pattern, method in mapping:
            match = re.match(pattern, path)
            if match:
                return (method, match.groupdict())


mapping = [
           (r'^/Books/(?P<book_id>\d+)$', 'get_book'),
           (r'/$', 'get_inicio'),
         #  (r'/busqueda?busqueda=(?P<busqueda>\S+)$', 'get_busqueda')
           (r'/busqueda$', 'get_busqueda')
          ]


if __name__ == "__main__":
    print("Server starting...")
    server = HTTPServer(("0.0.0.0", 80), WebRequestHandler)
    server.serve_forever()
