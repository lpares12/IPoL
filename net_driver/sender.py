#!/bin/python
import socket
import sys
import os
import time

import struct

NAME = '(SENDER)'

def sizeToInt(received):
	data = bytearray(received)
	num = 0
	for offset, byte in enumerate(data):
		num += byte << (offset *8)
	return num


def log(file, text):
	file.write('[' + str(time.strftime("%H:%M:%S")) + ']('+NAME+') ' + str(text) + '\n')

logFile = open("/tmp/ipol_sender.log", "w")

tuncAddress = '/tmp/ipol_send'

# Make sure the socket does not already exist
try:
    os.unlink(tuncAddress)
    log(logFile, 'Correctly unlinked')
except OSError:
	log(logFile, 'Problem unlinking')

tuncfd = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
tuncfd.bind(tuncAddress)
tuncfd.listen(1)
log(logFile, 'Listening on ' + tuncAddress)

try:
	log(logFile, 'Waiting for a connection to ' + tuncAddress)
	connection, client_address = tuncfd.accept()
	log(logFile, 'Connection from ' + tuncAddress)
	try:

		######################
		# Connect to IPoL server (this won't be necessay for IPoL, since it will be connectionless)
		ipolsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serverAddress = (os.environ['PEER_REAL_IP'], int(os.environ['PEER_PORT']))
		while True:
			try:
				ipolsock.connect(serverAddress)
				log(logFile, 'Connected to IPoL server at: ' + str(serverAddress))
				break
			except Exception, e:
				log(logFile, 'Error connecting to IPoL server ' + str(e))
				time.sleep(1)
		######################

		######################
		# Read data from tunc
		while True:
			log(logFile, 'Waiting to receive packet size')
			sizeNet = connection.recv(4, socket.MSG_WAITALL) # expect size_t (4 bytes)
			sizeInt = sizeToInt(sizeNet)

			log(logFile, 'Waiting to receive packet of size: ' + str(sizeInt) + 'bytes')
			packet = connection.recv(sizeInt, socket.MSG_WAITALL)
			if not packet or len(packet) == 0:
				break
			log(logFile, 'Received: ' + str(len(packet)) + 'bytes')

			###################
			# Send to IPoL server
			error = ipolsock.sendall(packet)
			##########
	except Exception, e:
		print e
		log(logFile, 'Error in the connection')
	finally:
		ipolsock.close()
		connection.close()
except socket.error, msg:
	log(logFile, 'Error connecting to ' + tuncAddress + ': ' + str(msg))
finally:
	logFile.close()