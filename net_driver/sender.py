#!/bin/python
import socket
import sys
import os
import time
import logging
import struct

def sendToPeer(fd, data):
	fd.sendall(data)

def sizeToInt(received):
	data = bytearray(received)
	num = 0
	for offset, byte in enumerate(data):
		num += byte << (offset *8)
	return num

#################
# Setup Logger
logger = logging.getLogger('sender')
handler = logging.FileHandler('/tmp/ipol.log')
if len(sys.argv) >= 2:
	if str(sys.argv[1]) == 'debug':
		logger.setLevel(logging.DEBUG)
		handler.setLevel(logging.DEBUG)
	elif str(sys.argv[1]) == 'info':
		logger.setLevel(logging.INFO)
		handler.setLevel(logging.INFO)
else:
	logger.setLevel(logging.WARNING)
	handler.setLevel(logging.WARNING)
#
logger.setLevel(logging.DEBUG)
handler.setLevel(logging.DEBUG)
#
formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s', '%H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
###################

###################
# Create the linux socket
tuncAddress = '/tmp/ipol_send'
try:
	os.unlink(tuncAddress) # Make sure the unix socket does not already exist
	logger.debug('%s unlinked', tuncAddress)
except OSError:
	logger.debug('Nothing to unlink')
tuncfd = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) # AF_UNIX = Unix Socket
tuncfd.bind(tuncAddress)
tuncfd.listen(1) # Accept only 1 connection
###################

try:
	##################
	# Accept a connection from tunc
	logger.info('Waiting for a connection to %s', str(tuncAddress))
	connection, client_address = tuncfd.accept()
	logger.info('Connection from %s at %s', str(client_address), str(tuncAddress))
	#################

	try:
		######################
		# Connect to IPoL server (this won't be necessay for IPoL, since it will be connectionless)
		ipolsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serverAddress = (os.environ['PEER_REAL_IP'], int(os.environ['PEER_PORT']))
		while True:
			try:
				ipolsock.connect(serverAddress)
				break
			except Exception, e:
				logger.warning('Can not connect to IP server: %s', str(e))
				time.sleep(1)
		logger.info('Connected to IP server at %s', str(serverAddress))
		###################### To delete this block when integrated the true IPoL <

		######################
		# Read data from tunc
		while True:
			# Receive the size of the packet
			try:
				sizeNet = connection.recv(4, socket.MSG_WAITALL) # expect size_t (4 bytes)
				# if str(len(sizeNet)) != 4: # Todo: get the byte length correctly
				# 	raise Exception('Received a size packet smaller than 4 bytes')
			except Exception, e:
				logger.error('Problem receiving size packet: %s', str(e))
				sys.exit()
			# Receive the packet
			sizeInt = sizeToInt(sizeNet)
			logger.debug('Expecting a packet of size %s', str(sizeInt))

			try:
				packet = connection.recv(sizeInt, socket.MSG_WAITALL)
				if not packet or len(packet) == 0: # If packet is empty the pipe is broken
					raise Exception('Received an empty packet (could be a disconnection')
				# if str(len(packet)) != sizeInt: # Todo: get the byte length correctly
				# 	raise Exception('Received less bytes than expected')
			except Exception, e:
				logger.error('Problem receiving data packet: %s', str(e))
				sys.exit()

			logger.debug('Received the packet correctly')

			###################
			# Send to IPoL server
			sendToPeer(ipolsock, packet)
			##########
	except Exception, e:
		logger.error('Error somewhere: ', str(e))
	finally:
		logger.info('Ending sender')
		ipolsock.close()
		connection.close()

except Exception, e:
	logger.info('Error accepting connection to %s: %s', str(tuncAddress), str(e)) # If there was a failure accepting the connection
finally:
	tuncfd.close()
