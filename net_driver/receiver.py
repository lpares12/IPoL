#!/bin/python
import socket
import sys
import os
import time
import logging
import threading

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

def checksum8(data):
	result = 0
	fctr = 16

	hexStr = "0123456789ABCDEF"

	for value in data:
		index = hexStr.index(str(value).upper())
		result += index * fctr
		if fctr == 16:
			fctr = 1
		else:
			fctr = 16

	if fctr == 1:
		return "Odd number of characters"
	else:
		result = (~(result & 0xff) + 1) & 0xff # result&0xff discards all bytes after low-end one
		strResult = hexStr[result/16] + hexStr[result%16]
		return strResult

def receiverWorker(queueCond):
	global packetQueue
	logger = logging.getLogger('ReceiverWorker')
	while True:
		# TODO: interact with sensor, now we just fake it to be able to run it
		data = 'AABB00DDFF' # this should be the received packet
		receivedChecksum = 'F0' # this should be the received checksum
		if checksum8(data) == receivedChecksum:
			logger.info('Checksum correct')
			queueCond.acquire()
			packetQueue.append(data)
			queueCond.notify()
			queueCond.release()
		time.sleep(5) # TODO: Remove


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

try:
	###################
	# Create the worker thread (the sensor thing)
	ipolWorker = threading.Thread(target=receiverWorker, args=(packetQueueCond,))
	ipolWorker.start()
	###################

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
		################
except Exception, e:
	logger.error('Unknown error: %s', str(e))
finally:
	tuncsocket.close()
	logger.info('Ending receiver')