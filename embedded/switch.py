import RPi.GPIO as GPIO
import time 

sw_pins = [5, 6, 13, 19]
prev_status = [GPIO.LOW] * 4
click_counts = [0] * 4


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

for pin in sw_pins:
    GPIO.setup(pin ,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


try:
    while True:
       
       current_status = [GPIO.input(pin) for pin in sw_pins]
       
       for i in range(len(sw_pins)):
        if current_status[i] == GPIO.HIGH and prev_status[i] == GPIO.LOW:
                click_counts[i] += 1
                print("'SW " + str(i+1) + " click', " + str(click_counts[i]))
           

       prev_status = current_status[:]

    time.sleep(0.1)

except KeyboardInterrupt:
    pass
    
finally:
    GPIO.cleanup()