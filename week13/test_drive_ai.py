import cv2 as cv
import numpy as np
import threading, time
import SDcar 
import sys
import tensorflow as tf
from tensorflow.keras.models import load_model

speed = 80
epsilon = 0.0001

enable_object_detection = False
object_detected = False
detection_lock = None
is_running = True
enable_AIdrive = False

# frame
current_frame = None
frame_lock = None

def func_thread():
    i = 0
    while True:
        time.sleep(1)
        i = i+1
        if is_running is False:
            break

def object_detection_thread():
    global object_detected, enable_object_detection, model_od, class_names, COLORS, detection_lock
    global current_frame, frame_lock

    while is_running:
        if not enable_object_detection:
            time.sleep(0.1)
            continue

        # ✅ 메인 스레드에서 촬영한 프레임 가져오기
        with frame_lock:
            if current_frame is None:
                time.sleep(0.05)
                continue
            frame = current_frame.copy() 

        image_height, image_width, _ = frame.shape
        blob = cv.dnn.blobFromImage(image=frame, size=(300,300), mean=(104,117,123), swapRB=True)

        model_od.setInput(blob)
        output = model_od.forward()

        detect_in_frame = False

        for detection in output[0,0,:,:]:
            confidence = detection[2]

            if confidence > 0.4:
                class_id = int(detection[1])
                class_name = class_names[class_id - 1] if class_id <= len(class_names) else 'Unknown'
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
        cv.waitKey(1)
        
        time.sleep(0.05)

    # ✅ 스레드 종료 시 창 닫기 (창이 있는 경우에만)
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
        print('enable_AIdrive 2: ', enable_AIdrive)   
    elif which_key & 0xFF == ord('t'):
        enable_object_detection = True
        print('물체 감지 활성화:', enable_object_detection)
    elif which_key & 0xFF == ord('r'):
        enable_object_detection = False
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
    
    # 물체 감지 시 긴급 제동
    if detection_lock is not None:
        with detection_lock:
            if object_detected and enable_object_detection:
                print("!!! 물체 감지 - 긴급 제동 !!!")
                car.motor_stop()
                time.sleep(0.3)
                return
    
    # 정상 주행
    img = np.expand_dims(img, 0)
    res = model.predict(img)[0]
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

def main():
    global current_frame, frame_lock
    
    camera = cv.VideoCapture(0)
    camera.set(cv.CAP_PROP_FRAME_WIDTH, v_x) 
    camera.set(cv.CAP_PROP_FRAME_HEIGHT, v_y)
    
    if not camera.isOpened():
        return
    
    try:
        while camera.isOpened():
            ret, frame = camera.read()
            if not ret:
                print("프레임을 읽을 수 없습니다")
                break
                
            frame = cv.flip(frame, -1)
            
            # ✅ 현재 프레임을 전역 변수에 저장 (물체 감지 스레드와 공유)
            with frame_lock:
                current_frame = frame.copy()
            
            cv.imshow('camera', frame)
            
            # image processing start here
            crop_img = frame[int(v_y/2):, :]
            crop_img = cv.resize(crop_img, (200, 66))
            cv.imshow('crop_img', cv.resize(crop_img, dsize=(0,0), fx=2, fy=2))

            if enable_AIdrive == True:
                drive_AI(crop_img)

            # 물체 감지 상태 화면 표시
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
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno

        print("Exception type: ", exception_type)
        print("File name: ", filename)
        print("Line number: ", line_number)
        
    finally:
        # ✅ 카메라 리소스 정리
        camera.release()
        print("카메라 해제 완료")

if __name__ == '__main__':
    v_x = 320
    v_y = 240
    v_x_grid = [int(v_x*i/10) for i in range(1, 10)]
    print("Grid positions:", v_x_grid)
    moment = np.array([0, 0, 0])

    model_path = 'lane_navigation_20251122_0111.h5'
    model = load_model(model_path)


    model_od = cv.dnn.readNetFromTensorflow(model='frozen_inference_graph.pb', 
                                            config='ssd_mobilenet_v2_coco_2018_03_29.pbtxt')
    
    # class
    class_names = []
    with open('object_detection_classes_coco.txt', 'r') as f:
        class_names = f.read().split('\n')
    print(f"✅ COCO 클래스 {len(class_names)}개 로드 완료")
    
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

    print("\n=== 키보드 명령어 ===")
    print("화살표 키: 수동 제어")
    print("e: AI 주행 활성화")
    print("w: AI 주행 비활성화")
    print("t: 물체 감지 활성화")
    print("r: 물체 감지 비활성화")
    print("q: 종료")
    print("===================\n")

    main() 
    
    is_running = False
    car.clean_GPIO()
    print('프로그램 종료')