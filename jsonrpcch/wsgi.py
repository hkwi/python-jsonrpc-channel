import jsonrpcch
from jsonrpcch import jsonrpcmethod

class JsonrpcServer:
	def __init__(self, server):
		self.server = server
	
	def __call__(self, environ, start_response):
		self.result = None
		def sink(result):
			self.result = result
		
		ch = jsonrpcch.Channel()
		ch.register_server(self.server)
		ch.sendout = sink
		
		length= int(environ.get('CONTENT_LENGTH', '0'))
		ch.feed(environ['wsgi.input'].read(length))
		start_response("200 OK", [("content-type",'application/json; charset=UTF-8'),])
		return [self.result,]

if __name__ == "__main__":
	class Echo:
		@jsonrpcmethod("echo")
		def echo_method(self, *args):
			return args
		
	from wsgiref.simple_server import make_server
	httpd = make_server("", 8000, JsonrpcServer(Echo()))
	httpd.handle_request()
