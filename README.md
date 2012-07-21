python-jsonrpc-channel
======================

jsonrpc channel I/O python implementation

<pre>
import json
import jsonrpcch
ch=jsonrpcch.Channel()
def server_echo(*args):
 return args

result = None
def store_result(x):
 global result
 result = x

ch.register("echo", server_echo)
ch.sendout = store_result
ch.feed(json.dumps({"method":"echo","params":["hello","world"],"id":1}))
print result
</pre>
