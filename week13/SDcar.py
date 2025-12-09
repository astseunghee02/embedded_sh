import threading
import time
import RPi.GPIO as GPIO

class Drive:
    def __init__(self):
        self.pins = {
            "SW1":5, "SW2":6, "SW3":13, "SW4":19,
            "PWMA":18, "AIN1":22, "AIN2":27,
            "PWMB":23, "BIN1":25, "BIN2":24,
            "LED1":26, "LED2":16, "LED3":21, 
            "LED4":20, "BUZ":12,
        }    
        self.config_GPIO()
        self.L_Motor = GPIO.PWM(self.pins["PWMA"], 500)
        self.L_Motor.start(0)
        self.R_Motor = GPIO.PWM(self.pins["PWMB"], 500)
        self.R_Motor.start(0)
        
        # 부저 PWM 초기화
        self.Buzzer = GPIO.PWM(self.pins["BUZ"], 100)
        self.Buzzer.start(0)
        
        # 음계 주파수 (도레미파솔라시도)
        self.notes = {
            'C': 262,   # 도
            'D': 294,   # 레
            'E': 330,   # 미
            'F': 349,   # 파
            'G': 392,   # 솔
            'A': 440,   # 라
            'B': 494,   # 시
            'C2': 523,  # 높은 도
        }

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
        GPIO.setup(self.pins["LED1"], GPIO.OUT)
        GPIO.setup(self.pins["LED2"], GPIO.OUT)
        GPIO.setup(self.pins["LED3"], GPIO.OUT)
        GPIO.setup(self.pins["LED4"], GPIO.OUT)
        
        # 부저 핀 설정
        GPIO.setup(self.pins["BUZ"], GPIO.OUT)
        
        # 초기 상태: 모두 OFF
        GPIO.output(self.pins["LED1"], GPIO.LOW)
        GPIO.output(self.pins["LED2"], GPIO.LOW)
        GPIO.output(self.pins["LED3"], GPIO.LOW)
        GPIO.output(self.pins["LED4"], GPIO.LOW)

    def clean_GPIO(self):
        # 부저 끄기
        self.Buzzer.stop()
        
        # LED 끄기
        GPIO.output(self.pins["LED1"], GPIO.LOW)
        GPIO.output(self.pins["LED2"], GPIO.LOW)
        GPIO.output(self.pins["LED3"], GPIO.LOW)
        GPIO.output(self.pins["LED4"], GPIO.LOW)
        GPIO.cleanup()
    
    def motor_go(self, speed):
        GPIO.output(self.pins["AIN1"], 0)
        GPIO.output(self.pins["AIN2"], 1)
        self.L_Motor.ChangeDutyCycle(speed)
        GPIO.output(self.pins["BIN1"], 0)
        GPIO.output(self.pins["BIN2"], 1)
        self.R_Motor.ChangeDutyCycle(speed)
        # LED 끄기 (직진 시)
        GPIO.output(self.pins["LED1"], GPIO.LOW)
        GPIO.output(self.pins["LED2"], GPIO.LOW)
        GPIO.output(self.pins["LED3"], GPIO.LOW)
        GPIO.output(self.pins["LED4"], GPIO.LOW)

    def motor_back(self, speed):
        GPIO.output(self.pins["AIN1"], 1)
        GPIO.output(self.pins["AIN2"], 0)
        self.L_Motor.ChangeDutyCycle(speed)
        GPIO.output(self.pins["BIN1"], 1)
        GPIO.output(self.pins["BIN2"], 0)
        self.R_Motor.ChangeDutyCycle(speed)
        # LED 끄기 (후진 시)
        GPIO.output(self.pins["LED1"], GPIO.LOW)
        GPIO.output(self.pins["LED2"], GPIO.LOW)
        GPIO.output(self.pins["LED3"], GPIO.LOW)
        GPIO.output(self.pins["LED4"], GPIO.LOW)
        
    def motor_left(self, speed):
        GPIO.output(self.pins["AIN1"], 1)
        GPIO.output(self.pins["AIN2"], 0)
        self.L_Motor.ChangeDutyCycle(speed)
        GPIO.output(self.pins["BIN1"], 0)
        GPIO.output(self.pins["BIN2"], 1)
        self.R_Motor.ChangeDutyCycle(speed)
        # 좌회전 LED만 켜기
        GPIO.output(self.pins["LED1"], GPIO.HIGH)
        GPIO.output(self.pins["LED2"], GPIO.LOW)
        GPIO.output(self.pins["LED3"], GPIO.LOW)
        GPIO.output(self.pins["LED4"], GPIO.HIGH)

    def motor_right(self, speed):
        GPIO.output(self.pins["AIN1"], 0)
        GPIO.output(self.pins["AIN2"], 1)
        self.L_Motor.ChangeDutyCycle(speed)
        GPIO.output(self.pins["BIN1"], 1)
        GPIO.output(self.pins["BIN2"], 0)
        self.R_Motor.ChangeDutyCycle(speed)
        # 우회전 LED만 켜기
        GPIO.output(self.pins["LED1"], GPIO.LOW)
        GPIO.output(self.pins["LED2"], GPIO.HIGH)
        GPIO.output(self.pins["LED3"], GPIO.HIGH)
        GPIO.output(self.pins["LED4"], GPIO.LOW)

    def motor_stop(self):
        GPIO.output(self.pins["AIN1"], 0)
        GPIO.output(self.pins["AIN2"], 1)
        self.L_Motor.ChangeDutyCycle(0)
        GPIO.output(self.pins["BIN1"], 0)
        GPIO.output(self.pins["BIN2"], 1)
        self.R_Motor.ChangeDutyCycle(0)
        # 정지 시 모든 LED 끄기
        GPIO.output(self.pins["LED1"], GPIO.LOW)
        GPIO.output(self.pins["LED2"], GPIO.LOW)
        GPIO.output(self.pins["LED3"], GPIO.LOW)
        GPIO.output(self.pins["LED4"], GPIO.LOW)

    # 알람 (모든 LED ON)
    def alarm_on(self):
        GPIO.output(self.pins["LED1"], GPIO.HIGH)
        GPIO.output(self.pins["LED2"], GPIO.HIGH)
        GPIO.output(self.pins["LED3"], GPIO.HIGH)
        GPIO.output(self.pins["LED4"], GPIO.HIGH)

    # 알람 해제 (모든 LED OFF)
    def alarm_off(self):
        GPIO.output(self.pins["LED1"], GPIO.LOW)
        GPIO.output(self.pins["LED2"], GPIO.LOW)
        GPIO.output(self.pins["LED3"], GPIO.LOW)
        GPIO.output(self.pins["LED4"], GPIO.LOW)

       # ===== 부저 함수 =====
    
    def buzzer_sound(self):
        
        self.Buzzer.ChangeFrequency(262)
        self.Buzzer.ChangeDutyCycle(10)
        time.sleep(0.5)
        self.Buzzer.ChangeFrequency(330)
        self.Buzzer.ChangeDutyCycle(10)
        time.sleep(0.5)
        self.Buzzer.ChangeFrequency(392)
        self.Buzzer.ChangeDutyCycle(10)
        time.sleep(0.5)
        
        self.Buzzer.ChangeDutyCycle(0)
    
    def buzzer_off(self):
        self.Buzzer.ChangeDutyCycle(0)

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
