# coding: UTF-8
# This code is available from http://github.com/hkwi/python-jsonrpc-channel
import jsonrpcch
import urlparse
import httplib

class JsonrpcServerError(jsonrpcch.JsonrpcException):
	def __init__(self, data):
		super(JsonrpcServerError, self).__init__(str(data))
		self.value = data


class _Method:
	def __init__(self, serv, name):
		self.__serv = serv
		self.__name = name
	
	def __getattr__(self, name):
		return _Method(self.__serv, "%s.%s" % (self.__name, name))
	
	def __call__(self, *params):
		serv = self.__serv
		
		ps = urlparse.urlparse(serv.url)
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
			con.request("POST", ps[1], data, {"Content-type":"application/json; charset=UTF-8", "Content-length":"%d" % (len(data),)})
			if not ch.feed(con.getresponse().read()):
				raise JsonrpcServerError("server response broken?")
		ch.sendout = sendout
		
		ch.call(self.__name, params, callback=callback, errback=errorback, version=serv.version)
		return holder["done"]


class JsonrpcServer:
	def __init__(self, url, version=None):
		self.url = url
		self.version = version
	
	def __getattr__(self, name):
		return _Method(self, name)


if __name__=="__main__":
	print JsonrpcServer("http://127.0.0.1:8000/", version=2).echo("hogehoge")
