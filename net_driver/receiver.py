#!/bin/python
import socket
import sys
import os
import time
import logging

#################
# Setup Logger
logger = logging.getLogger('receiver')
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
formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s', "%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)
###################

###################
# Connect to tunc
tuncAddress = '/tmp/ipol_recv'
tuncsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
while True:
	try:
		tuncsocket.connect(tuncAddress)
		break
	except Exception, e:
		logger.warning('Can not connect to tunc server: %s', str(e))
		time.sleep(1)
logger.info('Connected to tunc server at %s', str(tuncAddress))
###################

####################
# Set up IPoL server
# Now we set up a basic TCP server to fake the IPol communication
# TODO: Remove
ipolsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverAddress = (os.environ['HOST_REAL_IP'], int(os.environ['HOST_PORT']))
ipolsock.bind(serverAddress)
ipolsock.listen(1)
##################

####################
# Wait for messages from IPoL to transfer them to tunc
try:
	#################
	# Wait for connection to IPoL
	# TODO: Remove
	logger.info('Waiting for a connection to IP server')
	connection, peerAddress = ipolsock.accept()
	logger.info('Connection from %s at IP server', str(peerAddress))
	#################

	#################
	# Wait for data from IPoL
	while True:
		data = connection.recv(84, socket.MSG_WAITALL)
		if len(data) == 0:
			raise Exception('Received an empty packet (could be a disconnection')
		logger.info('Received a packet of size %s', str(len(data)))
		logger.info('Transfering %s bytes to tunc', str(len(data)))

		#################
		# Transfer data to tunc
		try:
			sent = tuncsocket.send(data)
			if sent == 0:
				raise Exception("Sent 0 bytes to tunc")
		except Exception, e:
			logger.error('Sent 0 bytes to tunc (could be a disconnection)')
			ipolsock.close()
			tuncsocket.close()
		################
	#################
except Exception, e:
	logger.error('Problem in the connection: %s', str(e))
finally:
	ipolsock.close()
####################