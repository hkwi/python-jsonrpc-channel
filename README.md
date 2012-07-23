python-jsonrpc-channel
======================

jsonrpc channel I/O python implementation. This library supports bidirectional communication.
Supported protocol versions are original one, and version 2.0.
jsonrpcch.wsgi and jsonrpcch.proxy are just convenient classes that support typical use cases.

Bidirectional communication channel can be build up by registering callbacks. There are two
layers of binary I/O layer and api I/O layer.

binary I/O channel call/callback are:
* sendout : callback that channel will sendout binary stream chunks.
* feed : call this to feed incoming binary stream chunks.

application method call/callback are:
* register or register_server : callback that respond to incoming json method request.
* call : call this to request json method call.


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

LICENSE
-------
Apache 2.0 license
