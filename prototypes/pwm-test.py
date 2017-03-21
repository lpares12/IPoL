import RPi.GPIO as GPIO
from time import sleep

ledPin = 18

GPIO.setmode(GPIO.BCM)

GPIO.setup(ledPin, GPIO.OUT)

led = GPIO.PWM(ledPin, 100)
led.start(0)

for i in range(0,100):
	led.ChangeDutyCycle(i)
	sleep(0.025)


led.stop()
GPIO.cleanup()
