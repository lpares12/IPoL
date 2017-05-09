#!/bin/python
import socket
import sys
import time

NAME = '(RECEIVER)'

def log(file, text):
	file.write('[' + str(time.strftime("%H:%M:%S")) + ']('+NAME+') ' + str(text) + '\n')

logFile = open("/tmp/ipol.log", "w")

socketAddress = './ipol_recv'

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

try:
	log(logFile, 'Trying to connect to ' + socketAddress)
	sock.connect(socketAddress)
	log(logFile, 'Connected to ' + socketAddress)
except socket.error, msg:
	log(logFile, 'Error connecting to ' + socketAddress + ': ' + str(msg))
