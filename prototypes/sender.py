import RPi.GPIO as GPIO
from time import sleep, time
from random import randrange

ledPin = 18

GPIO.setmode(GPIO.BCM)

GPIO.setup(ledPin, GPIO.OUT)

led = GPIO.PWM(ledPin, 100)
led.start(0)

toSend = [1,0,1,0,1,1,0,1]

# Start connection BIT
led.ChangeDutyCycle(100)
sleep(0.02508)

for i in range(8):
	#randBit = randrange(0,2)
	if toSend[i] == 0:
		led.ChangeDutyCycle(0)
	else:
		led.ChangeDutyCycle(100)
	sleep(0.0252)

led.stop()
GPIO.cleanup()
