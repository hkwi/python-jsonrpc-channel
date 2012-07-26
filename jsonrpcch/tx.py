# coding: UTF-8
# This code is available from http://github.com/hkwi/python-jsonrpc-channel
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Factory, Protocol, ProcessProtocol
from twisted.web.resource import IResource
from twisted.web.server import NOT_DONE_YET
from zope.interface import implements
import jsonrpcch

class DeferredChannel(jsonrpcch.Channel):
	def serve_result_fixup(self, request, result):
		if isinstance(result, Deferred):
			def catch_result_fail(fail):
				self.serve_error(request, fail.value)
			result.addCallback(self.serve_result, catch_result_fail)
		else:
			self.serve_result(request, result)

class JsonrpcProtocol(Protocol):
	channel = None
	
	def _ensure_channel(self):
		if self.channel is None:
			self.channel = DeferredChannel()
	
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

class JsonrpcResource:
	implements(IResource)
	
	isLeaf = True
	
	def __init__(self, server):
		self.server = server
	
	def render(self, request):
		if not request.getHeader("content-type").startswith("application/json") or request.method != "POST":
			request.setResponseCode(400)
			request.finish()
			return
		
		channel = DeferredChannel()
		channel.register_server(self.server)
		def body_sendout(binary):
			request.setHeader("content-type", "application/json; charset=%s" % (channel.encoding,))
			request.setHeader("content-length", len(binary))
			request.write(binary)
			request.finish()
		
		channel.sendout = body_sendout
		channel.feed(request.content.read())
		return NOT_DONE_YET
	
	def putChild(self, path, child):
		raise NotImplemented("JsonrpcResource.putChild unavailable")
	
	def getChildWithDefault(self, name, request):
		raise NotImplemented("JsonrpcResource.getChildWithDefault unavailable")
