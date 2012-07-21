import json
import uuid
import codecs
import traceback

class Feeder:
	buf = ""
	encoding = "UTF-8"
	decoder = None # binary to text decoder
	jsondec = None # json text to object decoder
	
	def feed(self, binary):
		if self.decoder is None:
			self.decoder = codecs.getincrementaldecoder(self.encoding)()
		buf = self.buf + self.decoder.decode(binary)
		if self.jsondec is None:
			self.jsondec = json.JSONDecoder()
		while True:
			try:
				obj,pos = self.jsondec.raw_decode(buf)
			except ValueError:
				self.buf = buf
				break
			
			try:
				self.callback(obj)
			except Exception,e:
				self.errback(e)
			
			while pos<len(buf) and buf[pos] in "\r\n":
				pos += 1
			
			buf = buf[pos:]
	
	def callback(self, obj):
		warnings.warn("feeder callback not registered")
	
	def errback(self, e):
		traceback.print_exc()

class Proxy:
	encoding = "UTF-8"
	
	def call(self, obj):
		try:
			self.callback(json.dumps(obj).encode(self.encoding))
		except Exception, e:
			self.errback(e)
	
	def callback(self, binary):
		warnings.warn("proxy callback not registered")
	
	def errback(self, e):
		traceback.print_exc()

class Channel:
	encoding = "UTF-8"
	callbacks = {}
	feeder = None
	proxy = None
	server = {}
	
	def feed(self, data):
		if self.feeder is None:
			self.feeder = Feeder()
			self.feeder.encoding = self.encoding
			self.feeder.callback = self.dispatcher
		self.feeder.feed(data)
	
	def dispatcher(self, obj):
		keys = obj.keys()
		if "method" in keys:
			method = obj["method"]
			if method.startswith("rpc."):
				# special method
				pass
			elif method in self.server:
				v2 = (obj.get("jsonrpc")=="2.0")
				try:
					if v2 and isinstance(obj["params"],dict):
						result = self.server[method](**obj["params"])
					else:
						result = self.server[method](*obj["params"])
					
					ret = {"result":result, "error":None}
				except Exception,e:
					ret = {"result":None, "error":str(e)}
				
				ret["id"] = obj["id"]
				if self.proxy is None:
					self.proxy = Proxy()
					self.proxy.encoding = self.encoding
					self.proxy.callback = self.sendout
				self.proxy.call(ret)
			else:
				raise ValueError("unhandled jsonrpc method")
		elif "result" in keys and "error" in keys and "id" in keys:
			(callback, errback) = self.callbacks.pop(obj["id"])
			if obj["error"]:
				errback(obj["error"])
			else:
				callback(obj["result"])
		else:
			raise ValueError("jsorpc format error(v1/v2)")
	
	def register(self, method, callback):
		self.server[method] = callback
	
	def register_server(self, server_instance):
		for x in dir(server_instance):
			attr = getattr(server_instance, x)
			method = getattr(attr, "__jsonrpcmethod__")
			if callable(attr) and method:
				self.server[method] = attr
	
	def call(self, method, params, callback=None, errback=None, version=1):
		req = {"method":method, "params":params}
		if version == 2:
			req["jsonrpc"] = "2.0"
		else:
			req["id"] = None
		
		if callback:
			id = str(uuid.uuid1())
			req["id"] = id
			if errback is None:
				errback = lambda x:traceback.print_exc()
			self.callbacks[id] = (callback, errback)
		
		if self.proxy is None:
			self.proxy = Proxy()
			self.proxy.encoding = self.encoding
			self.proxy.callback = self.sendout
		self.proxy.call(req)
	
	def sendout(self, binary):
		pass

import functools
def jsonrpcmethod(method):
	def factory(func):
		@functools.wraps(func)
		def wrapper(*args, **kwarg):
			return func(*args, **kwarg)
		
		wrapper.__jsonrpcmethod__ = method
		return wrapper
	return factory
