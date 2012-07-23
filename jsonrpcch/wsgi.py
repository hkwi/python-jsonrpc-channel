# coding: UTF-8
# This code is available from http://github.com/hkwi/python-jsonrpc-channel
import jsonrpcch
from jsonrpcch import jsonrpcmethod

class JsonrpcServer:
	def __init__(self, server):
		self.server = server
	
	def __call__(self, environ, start_response):
		holder = []
		def sink(result):
			holder.append(result)
		
		ch = jsonrpcch.Channel()
		ch.register_server(self.server)
		ch.sendout = sink
		
		length= int(environ.get('CONTENT_LENGTH', '0'))
		if ch.feed(environ['wsgi.input'].read(length)):
			start_response("200 OK", [("content-type",'application/json; charset=UTF-8'),])
			return holder
		
		raise Exception("input broken?")

if __name__ == "__main__":
	class Echo:
		@jsonrpcmethod("echo")
		def echo_method(self, *args):
			return args
		
		@jsonrpcmethod("fail")
		def fail_method(self, *args):
			raise jsonrpcch.jsonrpc_error_factory(5, "EIO")(args)
		
	from wsgiref.simple_server import make_server
	httpd = make_server("", 8000, JsonrpcServer(Echo()))
	httpd.handle_request()
