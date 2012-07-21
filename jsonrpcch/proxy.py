import jsonrpcch
import urlparse
import httplib

class JsonrpcServer:
	def __init__(self, url):
		self.url = url
	
	def __getattr__(self, name):
		def func(*params):
			ps = urlparse.urlparse(self.url)
			hp = ps[1].split(":",1)
			if ps[0] == "http":
				con = httplib.HTTPConnection(*hp)
			elif ps[0] == "https":
				con = httplib.HTTPSConnection(*hp)
			else:
				raise NotImplementedException("unknown scheme")
			
			self.result = None
			def store_data(result):
				self.result = result
			
			ch = jsonrpcch.Channel()
			
			def sendout(data):
				con.request("POST", ps[1], data, {"Content-type":"application/json; charset=UTF-8"})
				ch.feed(con.getresponse().read())
			
			ch.sendout = sendout
			ch.call(name, params, callback=store_data)
			
			return self.result
		
		return func

if __name__=="__main__":
	print JsonrpcServer("http://127.0.0.1:8000/").echo("hogehoge")
