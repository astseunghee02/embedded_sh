import RPi.GPIO as GPIO
import time

BUZZER = 12

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER, GPIO.OUT)

p = GPIO.PWM(BUZZER, 261)
p.start(50)

frequncy = [523,500,1,1,1,1,500,400,300] #여기에 도레미파솔라시도 넣으면 됩니다.

try:
    while True:
        p.start(50)
        for i in range (len(frequncy)):
            p.ChangeFrequency(frequncy[i]) 
            time.sleep(1.0)
        
        p.stop()
        time.sleep(3.0)


except keyboardInterrupt:
    pass

p.stop()
GPIO.cleanup()


