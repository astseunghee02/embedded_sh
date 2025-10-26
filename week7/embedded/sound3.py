import RPi.GPIO as GPIO
import time

SW_PINS = [5, 6, 13, 19]
BUZZER = 12

NOTES = [261, 330, 392, 440] 

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(BUZZER, GPIO.OUT)
for pin in SW_PINS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

p = GPIO.PWM(BUZZER, NOTES[0])
p.start(0)


try:
    while True:
        note_to_play = 0

        for i in range(len(SW_PINS)):
            if GPIO.input(SW_PINS[i]) == GPIO.HIGH:
                note_to_play = NOTES[i]
        
        if note_to_play > 0:
            p.ChangeFrequency(note_to_play)
            p.ChangeDutyCycle(50)
        else:
            p.ChangeDutyCycle(0)

        time.sleep(0.01)

except KeyboardInterrupt:
   
    pass

finally:
    p.stop()
    GPIO.cleanup()
   