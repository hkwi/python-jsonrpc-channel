# coding: UTF-8
# This code is available from http://github.com/hkwi/python-jsonrpc-channel
from twisted.internet.protocol import Factory, Protocol, ProcessProtocol
from twisted.web.resource import IResource
from zope.interface import implements
import jsonrpcch

class JsonrpcProtocol(Protocol):
	channel = None
	
	def _ensure_channel(self):
		if self.channel is None:
			self.channel = jsonrpcch.Channel()
	
	def connectionMade(self):
		self._ensure_channel()
		self.channel.sendout = self.transport.write
	
	def connectionLost(self, reason):
		self.channel.reset()
	
	def dataReceived(self, data):
		self.channel.feed(data)
	
	def register(self, method, callback):
		self._ensure_channel()
		self.channel.register(method, callback)
	
	def register_server(self, server_instance):
		self._ensure_channel()
		self.channel.register_server(server_instance)

class _DeferredProxy(jsonrpcch.Proxy):
	encoding = "UTF-8"
	
	def call(self, obj):
		d = obj.get("result")
		if isinstance(d, defer.Deferred):
			d.addCallback(self._obj_to_callback)
			d.addErrback(self.errback)
		else:
			self._obj_to_callback(obj)
	
	def _obj_to_stream(self, obj):
		self.callback(json.dumps(obj).encode(self.encoding))
	
	def callback(self, binary):
		warnings.warn("_DeferredProxy callback not registered")
	
	def errback(self, e):
		warnings.warn("_DeferredProxy errback not registered")

class JsonrpcResource:
	implements(IResource)
	
	isLeaf = True
	
	def __init__(self, server):
		self.server = server
	
	def render(self, request):
		if not request.getHeader("content-type").startswith("application/json") or self.method != "POST":
			request.setResponseCode(400)
			request.finish()
			return
		
		proxy = _DeferredProxy()
		channel = jsonrpcch.Channel()
		channel.register_server(self.server)
		channel.proxy = proxy
		proxy.encoding = channel.encoding
		
		def body_sendout(error=False):
			def resp(binary_or_error):
				if error:
					request.setResponseCode(500)
				else:
					request.setHeader("content-type", "application/json; charset=%s" % (proxy.encoding,))
					request.setHeader("content-length", len(binary_or_error))
					request.write(binary_or_error)
				request.finish()
		
		proxy.callback = channel.sendout = body_sendout()
		proxy.errback = body_sendout(True)
		
		channel.feed(request.content.read())
		return NOT_DONE_YET
	
	def putChild(self, path, child):
		raise NotImplemented("JsonrpcResource.putChild unavailable")
	
	def getChildWithDefault(self, name, request):
		raise NotImplemented("JsonrpcResource.getChildWithDefault unavailable")
