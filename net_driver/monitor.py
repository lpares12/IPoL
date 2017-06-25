#!/bin/python
from time import sleep
import logging

# Retrieves the CPU temperature from the integrated driver
def getCpuTemperature():
	file = open('/sys/class/thermal/thermal_zone0/temp', 'r')
	cpuTemperature = float(file.read())/1000
	file.close()
	return cpuTemperature

# Set up the logger
def setUpLogger():
	logger = logging.getLogger('Monitor')
	handler = logging.FileHandler('/tmp/ipol.log')
	logger.setLevel(logging.DEBUG)
	formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s', "%H:%M:%S")
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	return logger

if __name__ == '__main__':
	logger = setUpLogger()
	while(True):
		logger.debug('Cpu temperature: %s', str(getCpuTemperature()))
		sleep(10)