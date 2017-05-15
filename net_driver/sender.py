#!/bin/python
import socket
import sys
import os
import logging
import threading
from ipol import *

#################
# Setup Logger
logger = logging.getLogger('Sender')
workerLogger = logging.getLogger('SenderWorker')
handler = logging.FileHandler('/tmp/ipol.log')
if len(sys.argv) >= 2:
	if str(sys.argv[1]) == 'debug':
		logger.setLevel(logging.DEBUG)
		workerLogger.setLevel(logging.DEBUG)
	elif str(sys.argv[1]) == 'info':
		logger.setLevel(logging.INFO)
		workerLogger.setLevel(logging.DEBUG)
else:
	logger.setLevel(logging.WARNING)
	workerLogger.setLevel(logging.DEBUG)
#
logger.setLevel(logging.DEBUG)
workerLogger.setLevel(logging.DEBUG)
#
formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s', '%H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
workerLogger.addHandler(handler)
###################

#################
# Create a packet queue to store the packets to send
packetQueue = [] # This variable WILL be protected
packetQueueCond = threading.Condition()
#################

def senderWorker(queueCond):
	global packetQueue
	logger = logging.getLogger('SenderWorker')
	startIpolSend()
	logger.info('Initialised')
	while True:
		queueCond.acquire()
		while len(packetQueue) == 0:
			queueCond.wait()
		packet = packetQueue.pop(0)
		queueCond.release()

		logger.debug('Got a packet from queue')
		# Todo: send packet data through Led
		ipolSend(packet)
		logger.debug('Packet sent')

def sizeToInt(received):
	data = bytearray(received)
	num = 0
	for offset, byte in enumerate(data):
		num += byte << (offset *8)
	return num

#################
# Create the worker thread (the Led thing)
ipolWorker = threading.Thread(name='SenderWorker', target=senderWorker, args=(packetQueueCond,))
ipolWorker.daemon = True
ipolWorker.start()
#################

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
		# Read data from tunc
		while True:
			try:
				data = connection.recv(500)
				if not data or len(data) == 0: # If packet is empty the pipe is broken
					raise Exception('Received an empty packet (could be a disconnection')
				# if str(len(data)) != sizeInt: # Todo: get the byte length correctly
				# 	raise Exception('Received less bytes than expected')
			except Exception, e:
				logger.error('Problem receiving data packet: %s', str(e))
				sys.exit()

			logger.debug('Received the packet correctly')

			###################
			# Add the message to packet queue
			packetQueueCond.acquire()
			packetQueue.append(data)
			packetQueueCond.notify()
			packetQueueCond.release()
			##########
			
	except Exception, e:
		logger.error('Error somewhere: ', str(e))
		logger.info('Ending server because of error')
		connection.close()
		tuncfd.close()
		sys.exit()
	# finally:
	# 	logger.info('Ending sender')
	# 	connection.close()

except Exception, e:
	logger.info('Error accepting connection to %s: %s', str(tuncAddress), str(e)) # If there was a failure accepting the connection
finally:
	tuncfd.close()
	logger.info('Ending sender')
	sys.exit()

