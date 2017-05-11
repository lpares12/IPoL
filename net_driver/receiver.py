#!/bin/python
import socket
import sys
import os
import time

NAME = '(RECEIVER)'

def log(file, text):
	file.write('[' + str(time.strftime("%H:%M:%S")) + ']('+NAME+') ' + str(text) + '\n')

logFile = open("/tmp/ipol_receiver.log", "w")

tuncAddress = '/tmp/ipol_recv'

tuncsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

try:
	log(logFile, 'Trying to connect to tunc ' + tuncAddress)
	while True:
		try:
			tuncsocket.connect(tuncAddress)
			log(logFile, 'Connected to tunc at ' + tuncAddress)
			break
		except Exception, e:
			log(logFile, 'Error connecting to IPoL server ' + str(e))
			time.sleep(1)

	####################
	# Set up IPoL server
	# TODO: Now we set up a basic TCP server to fake the IPol communication
	ipolsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serverAddress = (os.environ['HOST_REAL_IP'], int(os.environ['HOST_PORT']))
	ipolsock.bind(serverAddress)
	ipolsock.listen(1)
	##################

	####################
	# Wait for messages from ipol
	# TODO: For now we just wait for IP packets from 10.0.0.2
	try:
		log(logFile, 'Waiting for connection to ' + tuncAddress)
		connection, peerAddress = ipolsock.accept()
		log(logFile, 'Client connected to ' + tuncAddress)
		while True:
			data = connection.recv(84, socket.MSG_WAITALL)
			if len(data) == 0:
				break
			log(logFile, "Received a packet of size " + str(len(data)))

			log(logFile, "Sending " + str(len(data)) + " to tunc")
			sent = tuncsocket.send(data)
			log(logFile, "Sent " + str(sent))
			# sent = 0
			# while sent < str(len(data)):
			# 	sent += ipolsock.send(data)
			# 	log(logFile, "Sent " + str(sent) + "bytes of " + str(len(data)))
	except Exception, e:
		print "Error: " + str(e)
	finally:
		ipolsock.close()
	####################

except socket.error, msg:
	log(logFile, 'Error connecting to tunc at ' + tuncAddress + ': ' + str(msg))
finally:
	logFile.close()