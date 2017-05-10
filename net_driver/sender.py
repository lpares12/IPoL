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

logFile = open("/tmp/ipol.log", "w")

socketAddress = '/tmp/ipol_send'

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
	log(logFile, 'Connection from ' + socketAddress)
	try:
		while True:
			log(logFile, 'Waiting to receive packet size')
			sizeNet = connection.recv(4, socket.MSG_WAITALL) # expect size_t (4 bytes)
			sizeInt = sizeToInt(sizeNet)

			log(logFile, 'Waiting to receive packet of size: ' + str(sizeInt) + 'bytes')
			packet = connection.recv(sizeInt, socket.MSG_WAITALL)
			log(logFile, 'Packet recieved')
			if not packet:
				continue
			log(logFile, 'Received: ' + str(len(packet)) + 'bytes')
	except Exception, e:
		print e
		log(logFile, 'Error in the connection')
	finally:
		connection.close()
except socket.error, msg:
	log(logFile, 'Error connecting to ' + socketAddress + ': ' + str(msg))
