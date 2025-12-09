import threading
import time
import RPi.GPIO as GPIO

class Drive:
    def __init__(self):
        self.pins = {
            "SW1":5, "SW2":6, "SW3":13, "SW4":19,
            "PWMA":18, "AIN1":22, "AIN2":27,
            "PWMB":23, "BIN1":25, "BIN2":24,
            "LED":26,      # GPIO26을 LED로 사용
        }    
        self.config_GPIO()
        self.L_Motor = GPIO.PWM(self.pins["PWMA"], 500)
        self.L_Motor.start(0)
        self.R_Motor = GPIO.PWM(self.pins["PWMB"], 500)
        self.R_Motor.start(0)

    def config_GPIO(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pins["SW1"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.pins["SW2"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.pins["SW3"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.pins["SW4"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.pins["PWMA"], GPIO.OUT)
        GPIO.setup(self.pins["AIN1"], GPIO.OUT)
        GPIO.setup(self.pins["AIN2"], GPIO.OUT)
        GPIO.setup(self.pins["PWMB"], GPIO.OUT)
        GPIO.setup(self.pins["BIN1"], GPIO.OUT)
        GPIO.setup(self.pins["BIN2"], GPIO.OUT)
        
        # LED 핀 설정
        GPIO.setup(self.pins["LED"], GPIO.OUT)
        GPIO.output(self.pins["LED"], GPIO.LOW)

    def clean_GPIO(self):
        # LED 끄기
        GPIO.output(self.pins["LED"], GPIO.LOW)
        GPIO.cleanup()
    
    def motor_go(self, speed):
        GPIO.output(self.pins["AIN1"], 0)
        GPIO.output(self.pins["AIN2"], 1)
        self.L_Motor.ChangeDutyCycle(speed)
        GPIO.output(self.pins["BIN1"], 0)
        GPIO.output(self.pins["BIN2"], 1)
        self.R_Motor.ChangeDutyCycle(speed)

    def motor_back(self, speed):
        GPIO.output(self.pins["AIN1"], 1)
        GPIO.output(self.pins["AIN2"], 0)
        self.L_Motor.ChangeDutyCycle(speed)
        GPIO.output(self.pins["BIN1"], 1)
        GPIO.output(self.pins["BIN2"], 0)
        self.R_Motor.ChangeDutyCycle(speed)
        
    def motor_left(self, speed):
        GPIO.output(self.pins["AIN1"], 1)
        GPIO.output(self.pins["AIN2"], 0)
        self.L_Motor.ChangeDutyCycle(speed)
        GPIO.output(self.pins["BIN1"], 0)
        GPIO.output(self.pins["BIN2"], 1)
        self.R_Motor.ChangeDutyCycle(speed)
        
    def motor_right(self, speed):
        GPIO.output(self.pins["AIN1"], 0)
        GPIO.output(self.pins["AIN2"], 1)
        self.L_Motor.ChangeDutyCycle(speed)
        GPIO.output(self.pins["BIN1"], 1)
        GPIO.output(self.pins["BIN2"], 0)
        self.R_Motor.ChangeDutyCycle(speed)

    def motor_stop(self):
        GPIO.output(self.pins["AIN1"], 0)
        GPIO.output(self.pins["AIN2"], 1)
        self.L_Motor.ChangeDutyCycle(0)
        GPIO.output(self.pins["BIN1"], 0)
        GPIO.output(self.pins["BIN2"], 1)
        self.R_Motor.ChangeDutyCycle(0)

    # 알람 켜기 (LED ON)
    def alarm_on(self):
        GPIO.output(self.pins["LED"], GPIO.HIGH)

    # 알람 끄기 (LED OFF)
    def alarm_off(self):
        GPIO.output(self.pins["LED"], GPIO.LOW)


if __name__ == '__main__':
    drive = Drive()
    
    # 모터 테스트
    drive.motor_go(100)
    time.sleep(2)
    drive.motor_left(100)
    time.sleep(2)
    drive.motor_right(100)
    time.sleep(2)
    drive.motor_back(100)          
    time.sleep(2)
    
    # 알람 테스트 (깜빡임)
    print("알람 테스트 시작")
    for i in range(5):  # 5번 깜빡임
        drive.alarm_on()
        time.sleep(0.3)
        drive.alarm_off()
        time.sleep(0.3)
    
    drive.clean_GPIO()
