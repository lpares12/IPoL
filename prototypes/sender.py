import RPi.GPIO as GPIO
from time import sleep, time
from random import randrange

ledPin = 18

GPIO.setmode(GPIO.BCM)

GPIO.setup(ledPin, GPIO.OUT)

led = GPIO.PWM(ledPin, 100)
led.start(0)

# Start connection BIT
led.ChangeDutyCycle(100)
sleep(0.025)

for i in range(8):
	randBit = randrange(0,2)
	print "Sending: " + str(randBit)
	if randBit == 0:
		led.ChangeDutyCycle(0)
	else:
		led.ChangeDutyCycle(100)
	sleep(0.025)

led.stop()
GPIO.cleanup()
