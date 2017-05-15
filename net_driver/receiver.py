#!/bin/python
import socket
import sys
import os
import time as t
import logging
import threading
from ipol import *

#################
# Setup Logger
logger = logging.getLogger('Receiver')
workerLogger = logging.getLogger('ReceiverWorker')
handler = logging.FileHandler('/tmp/ipol.log')
if len(sys.argv) >= 2:
	if str(sys.argv[1]) == 'debug':
		logger.setLevel(logging.DEBUG)
		workerLogger.setLevel(logging.DEBUG)
	elif str(sys.argv[1]) == 'info':
		logger.setLevel(logging.INFO)
		workerLogger.setLevel(logging.INFO)
else:
	logger.setLevel(logging.WARNING)
	workerLogger.setLevel(logging.WARNING)
#
logger.setLevel(logging.DEBUG)
workerLogger.setLevel(logging.DEBUG)
#
formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s', "%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)
workerLogger.addHandler(handler)
###################

#################
# Create a packet queue to store the received packets
packetQueue = [] # This variable WILL be protected
packetQueueCond = threading.Condition()

#################
def receiverWorker(queueCond):
	global packetQueue
	logger = logging.getLogger('ReceiverWorker')
	bus = startIpolReceive()
	logger.info('Initialised')
	while True:
		logger.info('Waiting to receive')
		# Receive data from IPoL
		data = ipolReceive(bus)
		logger.info('Packet Received')
		queueCond.acquire()
		packetQueue.append(data)
		queueCond.notify()
		queueCond.release()
	endIpolReceive(bus)

###################
# Create the worker thread (the sensor thing)
ipolWorker = threading.Thread(name='Receiver Worker', target=receiverWorker, args=(packetQueueCond,))
ipolWorker.daemon = True
ipolWorker.start()
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
		t.sleep(1)
logger.info('Connected to tunc server at %s', str(tuncAddress))
###################

try:
	####################
	# Wait for messages from IPoL to transfer them to tunc
	####################
	# Wait for data from IPoL
	while True:
		packetQueueCond.acquire()
		while len(packetQueue) == 0:
			packetQueueCond.wait()
		data = packetQueue.pop(0)
		packetQueueCond.release()

		if len(data) <= 0:
			continue
		logger.debug('Received a packet of size %s, transfering to tunc', str(len(data)))

		#################
		# Transfer data to tunc
		try:
			sent = tuncsocket.send(data)
			if sent == 0:
				raise Exception("Sent 0 bytes to tunc")
		except Exception, e:
			logger.error('Sent 0 bytes to tunc (could be a disconnection)')
			tuncsocket.close()
			sys.exit()
		################
except Exception, e:
	logger.error('Unknown error: %s', str(e))
finally:
	tuncsocket.close()
	logger.info('Ending receiver')
	sys.exit()