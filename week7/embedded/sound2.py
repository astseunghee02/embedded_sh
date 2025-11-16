import RPi.GPIO as GPIO
import time

SW1 = 5     
BUZZER = 12

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER, GPIO.OUT)
GPIO.setup(SW1 ,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

p = GPIO.PWM(BUZZER, 261)
p.start(0) 

frequncy = [523,500,1,1,1,1,500,400,300]

prev_sw_state = GPIO.LOW

try:
    while True:
        current_sw_state = GPIO.input(SW1)
        
        if current_sw_state == GPIO.HIGH and prev_sw_state == GPIO.LOW:
            for freq in frequncy:
                if freq < 20:
                    p.ChangeDutyCycle(0)
                else:
                    p.ChangeFrequency(freq)
                    p.ChangeDutyCycle(50)
                
                time.sleep(1.0)
            
            p.ChangeDutyCycle(0)
         

        prev_sw_state = current_sw_state
        time.sleep(0.01)

except KeyboardInterrupt:
    pass

finally:
    p.stop()
    GPIO.cleanup()