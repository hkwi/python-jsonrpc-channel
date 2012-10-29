# coding: UTF-8
# This code is available from http://github.com/hkwi/python-jsonrpc-channel
import jsonrpcch
import urlparse
import httplib

class JsonrpcServerError(jsonrpcch.JsonrpcException):
	def __init__(self, data):
		super(JsonrpcServerError, self).__init__(str(data))
		self.value = data

class _CaptureData:
	def __init__(self,):
		self.captured = False
	
	def __call__(self, data):
		self.captured = True
		self.data = data

class _Method:
	def __init__(self, serv, name):
		self.__serv = serv
		self.__name = name
	
	def __getattr__(self, name):
		return _Method(self.__serv, "%s.%s" % (self.__name, name))
	
	def __call__(self, *params, **kwargs):
		serv = self.__serv
		
		if kwargs and (not params) and serv.version==2:
			params = kwargs
		
		ps = urlparse.urlparse(serv.url)
		hp = ps[1].split(":",1)
		if ps[0] == "http":
			con = httplib.HTTPConnection(*hp)
		elif ps[0] == "https":
			con = httplib.HTTPSConnection(*hp)
		else:
			raise NotImplementedException("unknown scheme")
		
		callback = _CaptureData()
		
		def errback(e):
			if callable(serv.errback):
				serv.errback(e)
			raise JsonrpcServerError(e)
		
		ch = jsonrpcch.Channel()
		def sendout(data):
			con.request("POST", ps[2], data, {"Host":ps[1], "Content-type":"application/json; charset=UTF-8", "Content-length":"%d" % (len(data),)})
			if not ch.feed(con.getresponse().read()):
				raise JsonrpcServerError("server response broken?")
		ch.sendout = sendout
		
		ch.call(self.__name, params, callback=callback, errback=errback, version=serv.version)
		if callback.captured:
			return callback.data
		else:
			raise JsonrpcServerError("no response from server")


class JsonrpcServer:
	def __init__(self, url, version=None, errback=None):
		self.url = url
		self.version = version
		self.errback = errback
	
	def __getattr__(self, name):
		return _Method(self, name)


if __name__=="__main__":
	print JsonrpcServer("http://127.0.0.1:8000/", version=2).echo("hogehoge")
