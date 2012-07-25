import warnings
from jsonrpcch import Feeder, Proxy
from twisted.internet.protocol import Factory, Protocol
from twisted.application import service, internet

class JsonProtocol(Protocol):
	feeder = None
	proxy = None
	
	def connectionMade(self):
		if len(self.factory.connected)==2:
			self.transport.loseConnection()
		
		self.factory.connected.add(self)
	
	def dataReceived(self, data):
		def pass_next(obj):
			for hop in self.factory.connected:
				if hop != self:
					return hop.objectRecieved(obj)
			warnings.warn("relay error. data come from "+ str(self.transport.getPeer()))
		
		if self.feeder is None:
			self.feeder = Feeder()
			self.feeder.callback = pass_next
		self.feeder.feed(data)
	
	def objectRecieved(self, obj):
		if obj.get("method"):
			diag=["REQ", obj.get("method"), obj.get("id"), ">"]
		else:
			diag=["RES", obj.get("id"), "<"]
		diag.append(self.transport.getPeer())
		diag.append("->")
		diag.append(self.transport.getHost())
		print " ".join([str(o) for o in diag])
		print obj
		if self.proxy is None:
			self.proxy = Proxy()
			self.proxy.callback = self.transport.write
		
		self.proxy.call(obj)
	
	def connectionLost(self, reason):
		self.factory.connected.remove(self)
		for hop in self.factory.connected:
			if hop != self:
				hop.transport.loseConnection()

class JsonPipeFactory(Factory):
	protocol = JsonProtocol
	connected = set()
	
	def startedConnecting(self, *args, **kwarg):
		pass
	
	def clientConnectionLost(self, *args, **kwarg):
		if len(self.connected) == 0:
			client_connect()

application = service.Application("json-pipe")
factory = JsonPipeFactory()
peer1 = internet.UNIXServer("piped.sock", factory)
peer1.setServiceParent(application)
def client_connect():
	peer2 = internet.UNIXClient("origin.sock", factory)
	peer2.setServiceParent(application)

client_connect()
