import RPi.GPIO as GPIO
from time import sleep

ledPin = 23

GPIO.setmode(GPIO.BCM)

GPIO.setup(ledPin, GPIO.OUT)

led = GPIO.PWM(ledPin, 100)
led.start(0)


# for i in range(0,5):
#	for j in range(0,100):
#		led.ChangeDutyCycle(j)
#		sleep(0.4)
for i in range(0,100):
	led.ChangeDutyCycle(i)
	sleep(0.4)


led.stop()
GPIO.cleanup()
