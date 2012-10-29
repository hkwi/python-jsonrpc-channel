# coding: UTF-8
# This code is available from http://github.com/hkwi/python-jsonrpc-channel
import json
import uuid
import codecs
import traceback
import warnings

class JsonrpcException(Exception):
	pass

class InternalJsonrpcException(JsonrpcException):
	def __str__(self):
		return str(self.to_plain())
	
	def to_plain(self, v2=False):
		if v2:
			return {"code":self.code, "message":self.message, "data":self.data}
		else:
			return "%s: %s" % (self.message, str(self.data))

def jsonrpc_error_factory(code, message):
	class _JsonrpcException(InternalJsonrpcException):
		def __init__(self, data=None):
			super(_JsonrpcException, self).__init__(message)
			self.data = data
			self.code = code
			self.message = message
	return _JsonrpcException

ParseError     = jsonrpc_error_factory(-32700, "Parse error")
InvalidRequest = jsonrpc_error_factory(-32600, "Invalid Request")
MethodNotFound = jsonrpc_error_factory(-32601, "Method not found")
InvalidParams  = jsonrpc_error_factory(-32602, "Invalid params")
InternalError  = jsonrpc_error_factory(-32603, "Internal error")

def is_v2(request):
	return request.get("jsonrpc")=="2.0"

class Feeder:
	"""
	Channel representing binary input call & api output callback
	"""
	buf = ""
	encoding = "UTF-8"
	decoder = None # binary to text decoder
	jsondec = None # json text to object decoder
	
	def feed(self, binary):
		"""
		@return true if callback was called
		"""
		emit = False
		if self.decoder is None:
			self.decoder = codecs.getincrementaldecoder(self.encoding)()
		buf = self.buf + self.decoder.decode(binary)
		if self.jsondec is None:
			self.jsondec = json.JSONDecoder()
		while True:
			try:
				obj,pos = self.jsondec.raw_decode(buf)
			except ValueError,e:
				self.buf = buf
				break
			
			emit = True
			self.callback(obj)
			
			while pos<len(buf) and buf[pos] in "\r\n":
				pos += 1
		
			buf = buf[pos:]
		return emit
	
	def callback(self, obj):
		warnings.warn("feeder callback not registered")

class Proxy:
	"""
	Channel representing api input call & binary output callback
	"""
	encoding = "UTF-8"
	
	def __init__(self, default=str):
		self.json_encoder_default = default
	
	def call(self, obj):
		self.callback(json.dumps(obj, default=self.json_encoder_default).encode(self.encoding))
	
	def callback(self, binary):
		warnings.warn("proxy callback not registered")

class Channel:
	encoding = "UTF-8"
	notified = None
	callbacks = {}
	feeder = None
	proxy = None
	server = {}
	
	def feed(self, data):
		if self.feeder is None:
			self.feeder = Feeder()
			self.feeder.encoding = self.encoding
			self.feeder.callback = self.dispatcher
		return self.feeder.feed(data)
	
	def dispatcher(self, obj):
		if is_v2(obj):
			if "id" in obj:
				if "method" in obj:
					method = obj["method"]
					if method.startswith("rpc."):
						# special method
						self.serve_error(obj, Exception("not supported"))
					elif method in self.server:
						params = obj.get("params")
						try:
							if isinstance(params, list):
								result = self.server[method](*params)
							elif isinstance(params, dict):
								result = self.server[method](**params)
							else:
								raise InvalidParams("typed %s" % (params.__class__.__name__,))
							self.serve_result_fixup(obj, result)
						except Exception,e:
							self.serve_error(obj, e)
					else:
						self.serve_error(obj, MethodNotFound(method))
				else:
					recv = self.callbacks.pop(obj["id"])
					if recv:
						(callback, errback) = recv
						if "result" in obj:
							callback(obj["result"])
						elif "error" in obj:
							errback(obj["error"])
						else:
							raise ParseError("Got invalid response (id %s)" % repr(id))
					else:
						raise ParseError("Got unknown response id %s" % repr(id))
			else:
				if callable(self.notified): self.notified(obj)
		elif "id" in obj:
			id = obj["id"]
			if "method" in obj:
				method = obj["method"]
				if method in self.server:
					params = obj.get("params")
					if isinstance(params, list):
						try:
							result = self.server[method](*params)
							self.serve_result_fixup(obj, result)
						except Exception,e:
							self.serve_error(obj, e)
					else:
						if id is None:
							if callable(self.notified): self.notified(obj)
						else:
							self.serve_error(obj, InvalidParams("typed %s" % (params.__class__.__name__,)))
				else:
					if id is None:
						if callable(self.notified): self.notified(obj)
					else:
						self.serve_error(obj, MethodNotFound(method))
			else:
				recv = self.callbacks.pop(obj["id"])
				if recv:
					(callback, errback) = recv
					if obj.get("error"):
						errback(obj["error"])
					elif "result" in obj:
						callback(obj["result"])
					else:
						callback()
				else:
					if id is None:
						if callable(self.notified): self.notified(obj)
					else:
						raise ParseError("Got unknown response id %s" % repr(id))
		else:
			if callable(self.notified):
				self.notified(obj)
			else:
				self.serve_error(obj, ParseError("Could not handle jsonrpc message"))
	
	def serve_result_fixup(self, request, result):
		# You can replace this fixup.
		self.serve_result(request, result)
	
	def serve_result(self, request, result):
		if is_v2(request):
			self._serve_response(request, {"result":result})
		else:
			self._serve_response(request, {"result":result, "error":None})
	
	def serve_error(self, request, exception):
		if isinstance(exception, InternalJsonrpcException):
			error = exception.to_plain(is_v2(request))
		else:
			error = InternalError(exception).to_plain(is_v2(request))
		if is_v2(request):
			self._serve_response(request, {"error":error})
		else:
			self._serve_response(request, {"result":None, "error":error})
	
	def _serve_response(self, request, response):
		if "id" in request:
			response["id"] = request["id"]
		if is_v2(request):
			response["jsonrpc"] = "2.0"
		if self.proxy is None:
			self.proxy = Proxy()
			self.proxy.encoding = self.encoding
			self.proxy.callback = self.sendout
		self.proxy.call(response)
	
	def register(self, method, callback):
		if callable(callback):
			self.server[method] = callback
		else:
			raise ValueError("argument is not a callable")
	
	def register_server(self, server_instance):
		for x in dir(server_instance):
			attr = getattr(server_instance, x)
			if attr and hasattr(attr, "__jsonrpcmethod__"):
				for method in getattr(attr, "__jsonrpcmethod__"):
					if callable(attr) and method:
						self.server[method] = attr
	
	def call(self, method, params, callback=None, errback=None, version=None):
		req = {"method":method, "params":params}
		if version == 2:
			req["jsonrpc"] = "2.0"
		else:
			req["id"] = None
		
		if callback:
			if callable(callback):
				id = str(uuid.uuid1())
				req["id"] = id
				if not callable(errback):
					if errback is None:
						errback = lambda x:traceback.print_exc()
					else:
						raise ValueError("errback is not a callable")
				self.callbacks[id] = (callback, errback)
			else:
				raise ValueError("callback is not a callable")
		
		if self.proxy is None:
			self.proxy = Proxy()
			self.proxy.encoding = self.encoding
			self.proxy.callback = self.sendout
		self.proxy.call(req)
	
	def sendout(self, binary):
		pass
	
	def reset(self):
		if self.feeder:
			self.feeder = None

import functools
def jsonrpcmethod(method):
	def factory(func):
		@functools.wraps(func)
		def wrapper(*args, **kwarg):
			return func(*args, **kwarg)
		
		if hasattr(wrapper, "__jsonrpcmethod__"):
			wrapper.__jsonrpcmethod__.add(method)
		else:
			wrapper.__jsonrpcmethod__ = set((method,))
		return wrapper
	return factory
