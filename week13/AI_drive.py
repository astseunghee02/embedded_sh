import cv2 as cv
import numpy as np
import threading, time
import SDcar 
import sys
import tensorflow as tf
from tensorflow.keras.models import load_model

speed = 80
epsilon = 0.0001

enable_object_detection = False #물체 감지 활성화
object_detected = False #물체 감지 상태
detection_lock = None #thread lock
is_running = True #프로그램 실행 상태
enable_AIdrive = False #ai drive 활성화 상태

# frame
current_frame = None
frame_lock = None

# led 관련 전역 변수
alarm_state = False  # 알람 상태 추적
alarm_last_toggle = 0  # 마지막 토글 시간

#object list
DETECT_CLASSES = ['clock','book']  

def func_thread():
    i = 0
    while True:
        time.sleep(1)
        i = i+1
        if is_running is False:
            break

#object_detection thread
def object_detection_thread():
    global object_detected, enable_object_detection, model_od, class_names, COLORS, detection_lock
    global current_frame, frame_lock

    frame_count = 0
    SKIP_FRAMES = 2
    window_created = False  # 윈도우 생성 여부 추적
    
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
                print(f" {class_name}  신뢰도: {confidence:.2f}")

        with detection_lock:
            object_detected = detect_in_frame
        
        cv.imshow('Object Detection', frame)
        window_created = True  # 윈도우가 생성되었음을 표시
        cv.waitKey(1)
        
        time.sleep(0.01)

    # 윈도우가 실제로 생성된 경우에만 종료 시도
    if window_created:
        try:
            cv.destroyWindow('Object Detection')
        except:
            pass
    
    print("물체 감지 스레드 종료")

def key_cmd(which_key):
    print('which_key', which_key)
    is_exit = False 
    global enable_AIdrive, enable_object_detection
    
    if which_key & 0xFF == 184:
        print('up')
        car.motor_go(speed)
    elif which_key & 0xFF == 178:
        print('down')
        car.motor_back(speed)
    elif which_key & 0xFF == 180:
        print('left')     
        car.motor_left(30)   
    elif which_key & 0xFF == 182:
        print('right')   
        car.motor_right(30)            
    elif which_key & 0xFF == 181:
        car.motor_stop()
        enable_AIdrive = False     
        print('stop')   
    elif which_key & 0xFF == ord('q'):  
        car.motor_stop()
        car.alarm_off()  # 프로그램 종료 시 알람 끄기
        print('exit')   
        enable_AIdrive = False
        enable_object_detection = False
        is_exit = True    
        print('enable_AIdrive: ', enable_AIdrive)          
    elif which_key & 0xFF == ord('e'):  
        enable_AIdrive = True
        print('enable_AIdrive: ', enable_AIdrive)        
    elif which_key & 0xFF == ord('w'):  
        enable_AIdrive = False
        car.motor_stop()
        car.alarm_off()  # AI 주행 중지 시 알람 끄기
        print('enable_AIdrive 2: ', enable_AIdrive)   
    elif which_key & 0xFF == ord('t'):
        enable_object_detection = True
        print('물체 감지 활성화:', enable_object_detection)
    elif which_key & 0xFF == ord('r'):
        enable_object_detection = False
        car.alarm_off()  # 물체 감지 비활성화 시 알람 끄기
        print('물체 감지 비활성화:', enable_object_detection)

    return is_exit  

def detect_maskY_HSV(frame):
    crop_hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    crop_hsv = cv.GaussianBlur(crop_hsv, (5,5), cv.BORDER_DEFAULT)
    mask_Y = cv.inRange(crop_hsv, (25, 50, 100), (35, 255, 255))
    return mask_Y

def detect_maskY_BGR(frame):
    B = frame[:,:,0]
    G = frame[:,:,1]
    R = frame[:,:,2]
    Y = np.zeros_like(G, np.uint8)
    Y = G*0.5 + R*0.5 - B*0.7
    Y = Y.astype(np.uint8)
    Y = cv.GaussianBlur(Y, (5,5), cv.BORDER_DEFAULT)
    _, mask_Y = cv.threshold(Y, 100, 255, cv.THRESH_BINARY)
    return mask_Y

def line_tracing(cx):
    global moment
    global v_x
    tolerance = 0.1
    diff = 0

    if moment[0] != 0 and moment[1] != 0 and moment[2] != 0:
        avg_m = np.mean(moment)
        diff = np.abs(avg_m - cx) / v_x
    
    if diff <= tolerance:
        moment[0] = moment[1]
        moment[1] = moment[2]
        moment[2] = cx
        print('cx : ', cx)
        if v_x_grid[2] <= cx < v_x_grid[4]:
            car.motor_go(speed) 
            print('go')
        elif v_x_grid[3] >= cx:
            car.motor_left(30) 
            print('turn left')
        elif v_x_grid[1] <= cx:
            car.motor_right(30) 
            print('turn right')
        else:
            print("skip")    
    else:
        car.motor_go(speed) 
        print('go')    
        moment = [0,0,0]

def show_grid(img):
    h, _, _ = img.shape
    for x in v_x_grid:
        cv.line(img, (x, 0), (x, h), (0,255,0), 1, cv.LINE_4)

def test_fun(model):
    camera = cv.VideoCapture(0)
    camera.set(cv.CAP_PROP_FRAME_WIDTH,v_x) 
    camera.set(cv.CAP_PROP_FRAME_HEIGHT,v_y)
    ret, frame = camera.read()
    frame = cv.flip(frame,-1)
    cv.imshow('camera',frame)
    crop_img = frame[int(v_y/2):,:]
    crop_img = cv.resize(crop_img, (200, 66))
    crop_img = np.expand_dims(crop_img, 0)
    a = model.predict(crop_img)
    print('okey, a: ', a)

def drive_AI(img):
    global object_detected, enable_object_detection, detection_lock
    global alarm_state, alarm_last_toggle
    
    # 물체 감지 시 긴급 제동 및 알람
    if detection_lock is not None:
        with detection_lock:
            if object_detected and enable_object_detection:
                print("!!! 물체 감지 - 긴급 제동 !!!")
                car.motor_stop()
                
                # 0.3초마다 알람 토글 (깜빡임 효과)
                current_time = time.time()
                if current_time - alarm_last_toggle >= 0.3:
                    if alarm_state:
                        car.alarm_off()
                        alarm_state = False
                    else:
                        car.alarm_on()
                        alarm_state = True
                    alarm_last_toggle = current_time
                
                time.sleep(0.05)  # 짧은 대기
                return
            else:
                # 물체가 없으면 알람 끄기
                if alarm_state:
                    car.alarm_off()
                    alarm_state = False
    
    # 정상 주행
    try:
        img = np.expand_dims(img, 0)
        res = model.predict(img, verbose=0)[0]
        steering_angle = np.argmax(np.array(res))
        print('steering_angle', steering_angle)
        
        if steering_angle == 0:
            print("go")
            speedSet = 60
            car.motor_go(speedSet)
        elif steering_angle == 1:
            print("left")
            speedSet = 20
            car.motor_left(speedSet)          
        elif steering_angle == 2:
            print("right")
            speedSet = 20
            car.motor_right(speedSet)
        else:
            print("This cannot be entered")
    except Exception as e:
        print(f"AI 주행 오류: {e}")
        car.motor_stop()

def main():
    global current_frame, frame_lock
    
    camera = cv.VideoCapture(0)
    camera.set(cv.CAP_PROP_FRAME_WIDTH, v_x) 
    camera.set(cv.CAP_PROP_FRAME_HEIGHT, v_y)
    camera.set(cv.CAP_PROP_BUFFERSIZE, 1)  # 버퍼 최소화
    
    if not camera.isOpened():
        print("카메라를 열 수 없습니다")
        return
    
    try:
        while camera.isOpened():
            ret, frame = camera.read()
            if not ret:
                print("프레임을 읽을 수 없습니다")
                break
                
            frame = cv.flip(frame, -1)
           
            #frame lock
            with frame_lock:
                current_frame = frame.copy()
            
            cv.imshow('camera', frame)
            
            # image processing start here
            crop_img = frame[int(v_y/2):, :]
            crop_img = cv.resize(crop_img, (200, 66))
            cv.imshow('crop_img', cv.resize(crop_img, dsize=(0,0), fx=2, fy=2))

            if enable_AIdrive == True:
                drive_AI(crop_img)

            # show image 
            if enable_object_detection and detection_lock is not None:
                with detection_lock:
                    status_text = "물체 감지: 경고!" if object_detected else "물체 감지: 정상"
                    color = (0, 0, 255) if object_detected else (0, 255, 0)
                cv.putText(frame, status_text, (10, 30), 
                          cv.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # image processing end here
            is_exit = False
            which_key = cv.waitKey(20)
            if which_key > 0:
                is_exit = key_cmd(which_key)    
            if is_exit is True:
                cv.destroyAllWindows()
                break

    except Exception as e:
        print(f"오류 발생: {e}")
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno
        print(f"파일: {filename}, 라인: {line_number}")

    finally:
        camera.release()
        cv.destroyAllWindows()
  

if __name__ == '__main__':
    v_x = 320
    v_y = 240
    v_x_grid = [int(v_x*i/10) for i in range(1, 10)]
    print("Grid positions:", v_x_grid)
    moment = np.array([0, 0, 0])

    # 알람 관련 전역 변수 초기화
    alarm_state = False
    alarm_last_toggle = 0

    #lane detection file
    model_path = 'lane_navigation_20251129_0502.h5'
    model = load_model(model_path)
    
    model_od = cv.dnn.readNetFromTensorflow(model='frozen_inference_graph.pb', 
                                            config='ssd_mobilenet_v2_coco_2018_03_29.pbtxt')
    
    #class
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

    # car control object
    car = SDcar.Drive()

    # Thread start
    t_task1 = threading.Thread(target=func_thread)
    t_task1.start()
    
    t_task2 = threading.Thread(target=object_detection_thread)
    t_task2.daemon = True
    t_task2.start()

    main() 
    
    is_running = False
    car.clean_GPIO()
    print('프로그램 종료')
