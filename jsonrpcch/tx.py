from twisted.internet.protocol import Factory, Protocol, ProcessProtocol
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
