import RPi.GPIO as GPIO
import time

PWMA = 18
AIN1 = 22
AIN2 = 27

PWMB = 23
BIN1 = 24
BIN2 = 25

SW1 = 5
SW2 = 6
SW3 = 13
SW4 = 19

speed = 50

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(PWMA, GPIO.OUT)
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(PWMB, GPIO.OUT)
GPIO.setup(BIN1, GPIO.OUT)
GPIO.setup(BIN2, GPIO.OUT)

GPIO.setup(SW1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SW2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SW3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SW4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

L_Motor = GPIO.PWM(PWMA, 500)
L_Motor.start(0)
R_Motor = GPIO.PWM(PWMB, 500)
R_Motor.start(0)


try:
    while True:
        if GPIO.input(SW1) == GPIO.HIGH:
            print("SW1: Forward")
            GPIO.output(AIN1, 1)
            GPIO.output(AIN2, 0)
            GPIO.output(BIN1, 1)
            GPIO.output(BIN2, 0)
            L_Motor.ChangeDutyCycle(speed)
            R_Motor.ChangeDutyCycle(speed)
            
        elif GPIO.input(SW4) == GPIO.HIGH:
            print("SW4: Backward")
            GPIO.output(AIN1, 0)
            GPIO.output(AIN2, 1)
            GPIO.output(BIN1, 0)
            GPIO.output(BIN2, 1)
            L_Motor.ChangeDutyCycle(speed)
            R_Motor.ChangeDutyCycle(speed)

        elif GPIO.input(SW2) == GPIO.HIGH:
            print("SW2: Right Turn")
            GPIO.output(AIN1, 1)
            GPIO.output(AIN2, 0)
            GPIO.output(BIN1, 0)
            GPIO.output(BIN2, 1)
            L_Motor.ChangeDutyCycle(speed)
            R_Motor.ChangeDutyCycle(speed)

        elif GPIO.input(SW3) == GPIO.HIGH:
            print("SW3: Left Turn")
            GPIO.output(AIN1, 0)
            GPIO.output(AIN2, 1)
            GPIO.output(BIN1, 1)
            GPIO.output(BIN2, 0)
            L_Motor.ChangeDutyCycle(speed)
            R_Motor.ChangeDutyCycle(speed)
            
        else:
            L_Motor.ChangeDutyCycle(0)
            R_Motor.ChangeDutyCycle(0)

        time.sleep(0.1)

except KeyboardInterrupt:
    pass

finally:
    GPIO.cleanup()