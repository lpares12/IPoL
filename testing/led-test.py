import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(23, GPIO.OUT)
print "Led on"
GPIO.output(23, GPIO.HIGH)
time.sleep(2)
print "Led off"
GPIO.output(23, GPIO.LOW)

