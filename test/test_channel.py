import jsonrpcch
from jsonrpcch import jsonrpcmethod
import json
from nose.tools import eq_,ok_

class Echo:
	@jsonrpcmethod("echo")
	def echo(self, *pos, **name):
		if name:
			return name
		return pos

	@jsonrpcmethod("fail")
	def fail(self, *pos, **name):
		raise Exception("always fail")

	@jsonrpcmethod("alias1")
	@jsonrpcmethod("alias2")
	def aliasd(self, *pos, **name):
		if name:
			return name
		return pos

def echo_meth(*pos, **name):
	if name:
		return name
	return pos

def fail_meth(*pos, **name):
	raise Exception("always fail")

class CaptureData:
	def __init__(self,):
		self.captured = False
	
	def __call__(self, data):
		self.captured = True
		self.data = data

class CaptureSerialData:
	def __init__(self,):
		self.data = None
	
	def __call__(self, data):
		if self.data is None:
			self.data = data
		else:
			self.data += data

class TestChannelIo:
	def test_notification_send(self,):
		capture = CaptureSerialData()
		ch = jsonrpcch.Channel()
		ch.sendout = capture
		ch.call("echo", []) # send notification
		
		eq_(capture.data, json.dumps({"method":"echo", "params":[], "id":None}))

	def test_notification_send_v2(self,):
		capture = CaptureSerialData()
		ch = jsonrpcch.Channel()
		ch.sendout = capture
		ch.call("echo", [], version=2) # send notification
		
		eq_(capture.data, json.dumps({"method":"echo", "params":[], "jsonrpc":"2.0"})) # without "id"

	def test_call_send(self,):
		sendout = CaptureSerialData()
		ch = jsonrpcch.Channel()
		ch.sendout = sendout
		ch.call("echo", [], callback=lambda x:None)
		
		obj = json.loads(sendout.data)
		eq_(obj["method"], "echo")
		eq_(obj["params"], [])
		ok_(obj["id"] is not None)

	def test_res_call(self,):
		sendout = CaptureSerialData()
		ch = jsonrpcch.Channel()
		ch.register_server(Echo())
		ch.sendout = sendout
		ch.feed(json.dumps({"method":"echo", "params":[], "id":1}))
		
		obj = json.loads(sendout.data)
		eq_(obj["result"], [])
		eq_(obj["id"], 1)
		eq_(obj["error"], None)

	def test_callback(self,):
		ch = jsonrpcch.Channel()
		ch.register_server(Echo())
		ch.sendout = ch.feed
		
		callback = CaptureData()
		ch.call("echo", [], callback=callback)
		ok_(callback.captured)
		eq_(callback.data, [])

		callback = CaptureData()
		ch.call("echo", {}, callback=callback, version=2)
		ok_(callback.captured)
		eq_(callback.data, [])
	
	def test_callback_fail(self,):
		ch = jsonrpcch.Channel()
		ch.register_server(Echo())
		ch.sendout = ch.feed
		
		callback = CaptureData()
		errback = CaptureData()
		ch.call("fail", [], callback=callback, errback=errback)
		ok_(errback.captured)
		ok_(errback.data)

		callback = CaptureData()
		errback = CaptureData()
		ch.call("fail", {}, callback=callback, errback=errback, version=2)
		ok_(errback.captured)
		ok_(errback.data)
		ok_(isinstance(errback.data, dict))
		if "code" in errback.data:
			ok_(isinstance(errback.data["code"],int))

	def test_callback_alias(self,):
		ch = jsonrpcch.Channel()
		ch.register_server(Echo())
		ch.sendout = ch.feed
		
		callback = CaptureData()
		ch.call("alias1", [], callback=callback)
		ok_(callback.captured)
		eq_(callback.data, [])
		
		callback = CaptureData()
		ch.call("alias2", [], callback=callback)
		ok_(callback.captured)
		eq_(callback.data, [])

	def test_callback_meth(self,):
		ch = jsonrpcch.Channel()
		ch.register("echo", echo_meth)
		ch.register("fail", fail_meth)
		ch.sendout = ch.feed
		
		callback = CaptureData()
		ch.call("echo", [], callback=callback)
		ok_(callback.captured)
		eq_(callback.data, [])

	def test_callback_meth_fail(self,):
		ch = jsonrpcch.Channel()
		ch.register("echo", echo_meth)
		ch.register("fail", fail_meth)
		ch.sendout = ch.feed
		
		callback = CaptureData()
		errback = CaptureData()
		ch.call("fail", [], callback=callback, errback=errback)
		ok_(errback.captured)
		ok_(errback.data)

if __name__ == '__main__':
	nose.main(argv=['nosetests', '-v', '--nocapture'], defaultTest=__file__)
