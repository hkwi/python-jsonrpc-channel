from twisted.internet.protocol import Factory, Protocol, ProcessProtocol
import jsonrpcch

class JsonrpcProtocol(Protocol):
	channel = None
	
	def _ensure_channel(self):
		if self.channel is None:
			self.channel = Jsonrpcch.Channel()
	
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
		self.channel.register_server(method, server_instance)
	
	def call(self, method, params, version):
		"""
		DO CALL unpause, when you've done adding callbacks.
		"""
		d = defer.Deferred()
		d.pause()
		self.channel.call(method, params, callback=d.callback, errback=d.errback, version=version)
		return d

class JsonfeedProtocolProtocol(ProcessProtocol):
	feeder = None
	def outReveived(self, data):
		if self.feeder is None:
			self.feeder = jsonrpcch.Feeder()
			self.feeder.callback = self.callback
		self.feeder.feed(data)
