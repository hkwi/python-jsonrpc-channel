# coding: UTF-8
# This code is available from http://github.com/hkwi/python-jsonrpc-channel
import jsonrpcch
import urlparse
import httplib

class JsonrpcServerError(jsonrpcch.JsonrpcException):
	def __init__(self, data):
		super(JsonrpcServerError, self).__init__(str(data))
		self.value = data

class JsonrpcServer:
	def __init__(self, url, version=None):
		self.url = url
		self.version = version
	
	def __getattr__(self, name):
		def func(*params):
			ps = urlparse.urlparse(self.url)
			hp = ps[1].split(":",1)
			if ps[0] == "http":
				con = httplib.HTTPConnection(*hp)
			elif ps[0] == "https":
				con = httplib.HTTPSConnection(*hp)
			else:
				raise NotImplementedException("unknown scheme")
			
			holder = {}
			def callback(result):
				holder["done"] = result
			
			def errorback(e):
				raise JsonrpcServerError(e)
			
			ch = jsonrpcch.Channel()
			def sendout(data):
				con.request("POST", ps[1], data, {"Content-type":"application/json; charset=UTF-8"})
				if not ch.feed(con.getresponse().read()):
					raise JsonrpcServerError("server response broken?")
			ch.sendout = sendout
			
			ch.call(name, params, callback=callback, errback=errorback, version=self.version)
			return holder["done"]
		
		return func

if __name__=="__main__":
	print JsonrpcServer("http://127.0.0.1:8000/", version=2).echo("hogehoge")
