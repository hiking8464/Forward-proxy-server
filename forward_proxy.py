import threading 
import time
from typing import final
import requests
import socket
import ssl

class Server():  # creating a class named server 
	def __init__(self, dd, urls):
    		
		# creating a socket
		self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   

		# reusing the socket
		self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
		# binding localhost to a port
		self.serverSocket.bind((dd['localhost'], dd['port']))       
		self.serverSocket.listen(10)
		self.num_client = 0


		#  loop for accepting new connections
		while 1:
    			
			# establishing a connection
			(clientSocket, client_address) = self.serverSocket.accept()	

			# assigning a thread to each client
			t = threading.Thread(name = self.count_client(client_address), target = self.proxy, args = (clientSocket, dd, urls))

			# to ensure that threads are terminated after main program exits
			t.setDaemon(True)
			t.start()
		self.serverSocket.close()
	
	def parse_url(self,url,method):
    	
		# finding the index of ":" to remove http://
		pointer = url.find("://")
		if pointer != -1:
    			
			# obtaining the url
			url = url[(pointer+3):] 
		
		# port number from the request
		index_port = url.find(":")
		try:
			num_port = int(url[(index_port+3):])
		except:
			if method == "GET":	
				num_port = 80
			elif method == "CONNECT":
				num_port = 443
		
		# finding destination server (requested server)) address
		webserver = url[:index_port]

		# returning webserver and its port number
		return webserver,num_port

	def proxy(self, clientSocket, dd, urls):
    		
		# receiving client request
		client_request = clientSocket.recv(dd['max_len'])

		# converting client request from bytes to string
		client_request_str = str(client_request)

		# extracting information about the type of method
		method = str(client_request_str.split(' ')[0])
		method = method[2:]

		# printing the method
		print("\n" + method + "\n")
		
		# extracting details of url from the http client request
		try:
			url = client_request_str.split('\n')[0].split(' ')[1]
		except:
			exit(0)

		# calling the parse function to get destination server (requested server))  address and its port number
		webserver,num_port = self.parse_url(url,method)

		# printing webserver
		print("\n" + str(webserver) + "\n")

		# checking if the site is blocked or not
		if webserver in urls:
			print("*************** Blocked website - "  +  webserver + " ***************")
			x = """ Hey there.
you cannot acces this site through our proxy server"""
			x = bytes(x,"utf-8")
			clientSocket.send(x)

			# closing the connection as requested site is a blocked site
			clientSocket.close()

		# calling the appropriate function after extracting the method from the http request 
		if (method == "GET"):
			self.get_http(webserver,num_port,clientSocket,client_request,dd)
		elif (method == "CONNECT"):
			self.connect_https(webserver,num_port,clientSocket,dd)
		elif (method == "POST"):
			self.post_http(webserver,num_port,clientSocket,client_request,dd)

	
	def get_http(self,webserver,num_port,clientSocket,client_request,dd):	

		# creating a socket for our proxy server
		proxy_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		proxy_client_socket.settimeout(dd['timeout'])
		
		# establishing connection between the proxy server and the requested server
		try:
			proxy_client_socket.connect((webserver,num_port))
		except:
			exit(0)

		# sending client request to the requested server from proxy
		proxy_client_socket.sendall(client_request)
		
		while True:
    		
			#  receiving the requested data from the server
			data = proxy_client_socket.recv(dd['buff_size'])

			#  sending the data to client
			if len(data) > 0:
				clientSocket.send(data)
			else:
				break
		exit(0)

		
	def connect_https(self,webserver,num_port,clientSocket,dd):
    	# creating a socket for our proxy server
		proxy_client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		proxy_client_socket = ssl.wrap_socket(proxy_client_socket)
		proxy_client_socket.settimeout(dd['timeout1'])
		try:
			
			# establishing connection between the proxy server and the requested server
			proxy_client_socket.connect((webserver,num_port))
			# proxy_client_socket.send(client_request)
			reply="HTTP/1.0 200 Connection established\r\n"
			reply+= "Proxy-agent: Hiking\r\n"
			reply+="\r\n"
			clientSocket.sendall(reply.encode())
		except socket.error as err:
			pass
		
		# clientSocket.setblocking(0)
		# proxy_client_socket.setblocking(0)
		try:
			client_request = clientSocket.recv(dd['buff_size'])

			# sending client request to the requested server from proxy
			proxy_client_socket.sendall(client_request)
		except socket.error as err:
			pass
		while True:

			#  sending the requested data to client 
			try:
				reply = proxy_client_socket.recv(dd['buff_size'])
				clientSocket.sendall(reply)
			except socket.error as e:
				pass
    

		
	def post_http(self,webserver,num_port,clientSocket,client_request,dd):
    
		# creating a socket for our proxy server
		proxy_client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		proxy_client_socket.settimeout(dd['timeout1'])
		
		# establishing connection between the proxy server and the requested server
		try:
			proxy_client_socket.connect((webserver,num_port))
		except:
			exit(0)

		headers= client_request.split(b"\r\n")
		n = len(headers)
		one = str(headers[0])
		nn = str(headers[n-1])
		headers = headers[1:n-1]
		z = headers.pop()
		x = "PROXY_COUNT : 1"
		x = bytes(x,"utf-8")
		headers.append(x)
		headers.append(z)
		y = "\r\n"
		one = one + y
		for i in range(0,len(headers)):
			one += str(headers[i]) + y
		final_request = one + nn
		final_request = bytes(final_request,"utf-8")

		# sending client request to the requested server from proxy
		proxy_client_socket.sendall(final_request)
		
				
	#  counting number of clients to assign the number as their name
	def count_client(self, addr): 
		self.num_client += 1
		return self.num_client


# required information
dd = {'localhost': '127.0.0.1', 
	  'port': 12345,
	  'max_len': 1000,
	  'buff_size': 1024*1024,
	  'timeout': 40,
	  'timeout1': 100,
		 }

# blocked sites
urls = ["google.com",
		"beacons.gcp.gvt2.com",
		"meet.google.com",
		"clients4.google.com",
		"www.google.com",
		"geeksforgeeks.org",
		"www.geeksforgeeks.org",
		"www.meet.google.com"]

server = Server(dd, urls)

