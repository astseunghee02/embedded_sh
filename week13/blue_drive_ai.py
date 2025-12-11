import cv2 as cv
import numpy as np
import threading, time
import SDcar 
import sys
import serial
import time
import tensorflow as tf
from tensorflow.keras.models import load_model

speed = 80
epsilon = 0.0001

enable_object_detection = False
object_detected = False
detection_lock = None
is_running = True
enable_AIdrive = False

current_frame = None
frame_lock = None

LED_state = False
LED_last_toggle = 0

DETECT_CLASSES = ['clock']  

ble_buffer = ""

def serial_thread(): 
    global gData, bleSerial, is_running, ble_buffer
    
    print("[BLE] 시리얼 스레드 시작")
    
    while is_running:
        try:
            if bleSerial is None:
                time.sleep(0.1)
                continue
            
            byte_data = bleSerial.read(1)
            
            if byte_data and len(byte_data) > 0:
                decoded = byte_data.decode('utf-8', errors='ignore')
                
                if decoded in ['\r', '\n', '\x00']:
                    continue
                
                if decoded.isprintable():
                    ble_buffer += decoded
                    
                    while len(ble_buffer) >= 2:
                        b_idx = ble_buffer.find('B')
                        
                        if b_idx == -1:
                            ble_buffer = ""
                            break
                        
                        if b_idx > 0:
                            ble_buffer = ble_buffer[b_idx:]
                        
                        if len(ble_buffer) >= 2:
                            if ble_buffer[1].isdigit():
                                command = ble_buffer[:2]
                                gData = command
                                print(f"[BLE] 명령어: {command}")  # 이것만 출력
                                ble_buffer = ble_buffer[2:]
                            else:
                                ble_buffer = ble_buffer[1:]
                        else:
                            break
                            
        except serial.SerialException as e:
            time.sleep(0.5)
        except Exception as e:
            if is_running:
                pass
            time.sleep(0.1)
    
    print("[BLE] 스레드 종료")

def func_thread():
    global is_running
    i = 0
    while True:
        time.sleep(1)
        i = i+1
        if is_running is False:
            break

def object_detection_thread():
    global object_detected, enable_object_detection, model_od, class_names, COLORS, detection_lock
    global current_frame, frame_lock, is_running

    frame_count = 0
    SKIP_FRAMES = 2
    window_created = False
    
    while is_running:
        if not enable_object_detection:
            time.sleep(0.1)
            continue

        with frame_lock:
            if current_frame is None:
                time.sleep(0.05)
                continue
            frame = current_frame.copy()

        frame_count += 1
        
        if frame_count % SKIP_FRAMES != 0:
            time.sleep(0.01)
            continue
        
        image_height, image_width, _ = frame.shape
        blob = cv.dnn.blobFromImage(image=frame, size=(200,200), mean=(104,117,123), swapRB=True)

        model_od.setInput(blob)
        output = model_od.forward()

        detect_in_frame = False

        for detection in output[0,0,:,:]:
            confidence = detection[2]

            if confidence > 0.4:
                class_id = int(detection[1])
                class_name = class_names[class_id - 1] if class_id <= len(class_names) else 'Unknown'
                
                if class_name not in DETECT_CLASSES:
                    continue
                
                color = COLORS[class_id] if class_id < len(COLORS) else (0, 255, 0)
                
                box_x = int(detection[3] * image_width)
                box_y = int(detection[4] * image_height)
                box_width = int(detection[5] * image_width)
                box_height = int(detection[6] * image_height)
                
                cv.rectangle(frame, (box_x, box_y), (box_width, box_height), color, thickness=2)
                cv.putText(frame, f'{class_name}: {confidence:.2f}', (box_x, box_y - 5), cv.FONT_HERSHEY_SIMPLEX, 1, color, 2)

                detect_in_frame = True

        with detection_lock:
            object_detected = detect_in_frame
        
        cv.imshow('Object Detection', frame)
        window_created = True
        cv.waitKey(1)
        
        time.sleep(0.01)

    if window_created:
        try:
            cv.destroyWindow('Object Detection')
        except:
            pass

def key_cmd(which_key):
    is_exit = False 
    global enable_AIdrive, enable_object_detection
    
    if which_key & 0xFF == 184:
        car.motor_go(speed)
    elif which_key & 0xFF == 178:
        car.motor_back(speed)
    elif which_key & 0xFF == 180:
        car.motor_left(30)   
    elif which_key & 0xFF == 182:
        car.motor_right(30)            
    elif which_key & 0xFF == 181:
        car.motor_stop()
        enable_AIdrive = False     
    elif which_key & 0xFF == ord('q'):  
        car.motor_stop()
        car.alarm_off()
        enable_AIdrive = False
        enable_object_detection = False
        is_exit = True    
    elif which_key & 0xFF == ord('e'):  
        enable_AIdrive = True
        print('[KEY] AI 주행 ON')
    elif which_key & 0xFF == ord('w'):  
        enable_AIdrive = False
        car.motor_stop()
        car.alarm_off()
        print('[KEY] AI 주행 OFF')
    elif which_key & 0xFF == ord('t'):
        enable_object_detection = True
        print('[KEY] 물체 감지 ON')
    elif which_key & 0xFF == ord('r'):
        enable_object_detection = False
        car.alarm_off()
        print('[KEY] 물체 감지 OFF')

    return is_exit  

def drive_AI(img):
    global object_detected, enable_object_detection, detection_lock
    global LED_state, LED_last_toggle
    
    if detection_lock is not None:
        with detection_lock:
            if object_detected and enable_object_detection:
                car.motor_stop()
                current_time = time.time()
                if current_time - LED_last_toggle >= 0.3:
                    if LED_state:
                        car.alarm_off()
                        LED_state = False
                    else:
                        car.alarm_on()
                        LED_state = True
                    LED_last_toggle = current_time
                
                time.sleep(0.05)
                return
            else:
                if LED_state:
                    car.alarm_off()
                    LED_state = False
    
    try:
        img = np.expand_dims(img, 0)
        res = model.predict(img, verbose=0)[0]
        steering_angle = np.argmax(np.array(res))
        
        if steering_angle == 0:
            car.motor_go(60)
        elif steering_angle == 1:
            car.motor_left(20)
        elif steering_angle == 2:
            car.motor_right(20)
    except Exception as e:
        car.motor_stop()

def main():
    global current_frame, frame_lock, gData
    global enable_AIdrive, enable_object_detection, is_running
    
    camera = cv.VideoCapture(0)
    camera.set(cv.CAP_PROP_FRAME_WIDTH, v_x) 
    camera.set(cv.CAP_PROP_FRAME_HEIGHT, v_y)
    camera.set(cv.CAP_PROP_BUFFERSIZE, 1)
    
    if not camera.isOpened():
        print("카메라를 열 수 없습니다")
        return
    
    try:
        while camera.isOpened() and is_running:
            ret, frame = camera.read()
            if not ret:
                break
                
            frame = cv.flip(frame, -1)
           
            with frame_lock:
                current_frame = frame.copy()
            
            cv.imshow('camera', frame)
            
            # 블루투스 명령 처리
            if len(gData) > 0:
                if gData == "B1":
                    enable_object_detection = True
                    print('[BLE] 물체 감지 ON')
                    gData = ""
                    
                elif gData == "B2":
                    enable_object_detection = False
                    car.alarm_off()
                    print('[BLE] 물체 감지 OFF')
                    gData = ""

                elif gData == "B0":
                    enable_AIdrive = True
                    print('[BLE] AI 주행 ON')
                    gData = ""
                    
                elif gData == "B3":
                    car.alarm_off()
                    print('[BLE] 프로그램 종료')   
                    enable_AIdrive = False
                    enable_object_detection = False
                    is_running = False
                    car.motor_stop()
                    gData = ""
                    break
                else:
                    gData = ""

            crop_img = frame[int(v_y/2):, :]
            crop_img = cv.resize(crop_img, (200, 66))
            cv.imshow('crop_img', cv.resize(crop_img, dsize=(0,0), fx=2, fy=2))

            if enable_AIdrive == True:
                drive_AI(crop_img)

            is_exit = False
            which_key = cv.waitKey(20)
            if which_key > 0:
                is_exit = key_cmd(which_key)    
            if is_exit is True:
                is_running = False
                cv.destroyAllWindows()
                break

    except Exception as e:
        print(f"오류: {e}")

    finally:
        camera.release()
        cv.destroyAllWindows()
  

if __name__ == '__main__':
    v_x = 320
    v_y = 240
    v_x_grid = [int(v_x*i/10) for i in range(1, 10)]
    moment = np.array([0, 0, 0])

    LED_state = False
    LED_last_toggle = 0

    gData = ""
    ble_buffer = ""
    
    print("[INIT] 블루투스 초기화...")
    
    try:
        bleSerial = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=0.1)
        print("[INIT] 블루투스 연결: /dev/ttyS0")
    except Exception as e:
        print(f"[WARNING] 블루투스 연결 실패: {e}")
        bleSerial = None

    model_path = 'lane_navigation_20251129_0502.h5'
    model = load_model(model_path)
    
    model_od = cv.dnn.readNetFromTensorflow(model='frozen_inference_graph.pb', 
                                            config='ssd_mobilenet_v2_coco_2018_03_29.pbtxt')
    
    class_names = []
    with open('object_detection_classes_coco.txt', 'r') as f:
        class_names = f.read().split('\n')
    
    COLORS = np.random.uniform(0, 255, size=(len(class_names), 3))

    enable_object_detection = False
    object_detected = False
    detection_lock = threading.Lock()
    frame_lock = threading.Lock()  
    current_frame = None
    is_running = True
    enable_AIdrive = False

    car = SDcar.Drive()

    t_task1 = threading.Thread(target=func_thread)
    t_task1.daemon = True
    t_task1.start()
    
    t_task2 = threading.Thread(target=object_detection_thread)
    t_task2.daemon = True
    t_task2.start()

    if bleSerial is not None:
        t_task3 = threading.Thread(target=serial_thread)
        t_task3.daemon = True
        t_task3.start()
    
    print("\n" + "=" * 40)
    print("    자율주행 자동차 제어 프로그램")
    print("=" * 40)
    print("B0:AI주행 B1:감지ON B2:감지OFF B3:종료")
    print("e:AI ON  w:AI OFF  t:감지ON  r:감지OFF")
    print("=" * 40 + "\n")
    
    main() 
    
    is_running = False
    car.motor_stop()
    car.alarm_off()
    car.clean_GPIO()
    print('종료')
