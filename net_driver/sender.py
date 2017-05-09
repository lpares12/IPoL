#!/bin/python
import socket
import sys
import os
import time

NAME = '(SENDER)'

def log(file, text):
	file.write('[' + str(time.strftime("%H:%M:%S")) + ']('+NAME+') ' + str(text) + '\n')

logFile = open("/tmp/ipol.log", "w")

socketAddress = './ipol_send'

# Make sure the socket does not already exist
try:
    os.unlink(socketAddress)
    log(logFile, 'Correctly unlinked')
except OSError:
	log(logFile, 'Problem unlinking')

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind(socketAddress)
sock.listen(1)
log(logFile, 'Listening on ' + socketAddress)

try:
	log(logFile, 'Waiting for a connection to ' + socketAddress)
	connection, client_address = sock.accept()
	try:
		log(logFile, 'Connection from ' + client_address)
		while True:
			packet = connection.recv()
			if not packet:
				continue
			log(logFile, 'Received: ' + str(len(packet)) + 'bytes')
	except:
		log(logFile, 'Error in the connection')
	finally:
		connection.close()
except socket.error, msg:
	log(logFile, 'Error connecting to ' + socketAddress + ': ' + str(msg))
