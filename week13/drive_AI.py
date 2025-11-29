import cv2 as cv
import numpy as np
import threading, time
import SDcar 
import sys
import tensorflow as tf
from tensorflow.keras.models import load_model

speed = 80
epsilon = 0.0001

def func_thread():
    i = 0
    while True:
        #print("alive!!")    
        time.sleep(1)
        i = i+1
        if is_running is False:
            break

def object_detection_thread():

    model = cv.dnn.readNetFromTensorflow(model='frozen_inference_graph.pb', \
                                     config='ssd_mobilenet_v2_coco_2018_03_29.pbtxt')

    camera_od = cv.VideoCapture(0)
    camera_od.set(cv.CAP_PROP_FRAME_WIDTH, 320)
    camera_od.set(cv.CAP_PROP_FRAME_HEIGHT, 240)
    
    while is_running:
        if not enable_object_detection:
            time.sleep(0.1)
            continue

        ret,frame = camera_od.read()
        if not ret:
            continue

        frame = cv.flip(frame, -1)

        image_height , image_width, _ = frame.shape
        blob = cv.dnn.blobFromImage(image=frame, size=(300,300), mean=(104,117,123), swapRB=True)

        model_od.setInput(blob)
        output = model_od.forward()

        detect_in_frame = False

        for detection in output[0,0,:,:]:
            confidence = detection[2]

            if confidence > 0.4:
                # get the class id
                class_id = detection[1]
                # map the class id to the class
                class_name = class_names[int(class_id)-1]
                color = COLORS[int(class_id)]
                # get the bounding box coordinates
                box_x = detection[3] * image_width
                box_y = detection[4] * image_height
                # get the bounding box width and height
                box_width = detection[5] * image_width
                box_height = detection[6] * image_height
                # draw a rectangle around each detected object
                cv.rectangle(image, (int(box_x), int(box_y)), (int(box_width), int(box_height)), color, thickness=2)
                # put the FPS text on top of the frame
                cv.putText(image, class_name, (int(box_x), int(box_y - 5)), cv.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            detected_in_frame = True

            with detection_lock:
                object_detected = detected_in_frame
                
            cv.imshow('object Detection', frame)
            cv.waitKey(1)

        camera_od.release()
        cv.destroyAllWindows('object')
         
def key_cmd(which_key):
    print('which_key', which_key)
    is_exit = False 
    global enable_AIdrive # assignment가 있는 경우는 global 키워드로 표시
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
        is_exit = True    
        print('enable_AIdrive: ', enable_AIdrive)          
    elif which_key & 0xFF == ord('e'):  
        enable_AIdrive = True
        print('enable_AIdrive: ', enable_AIdrive)        
    elif which_key & 0xFF == ord('w'):  
        enable_AIdrive = False
        car.motor_stop()
        print('enable_AIdrive 2: ', enable_AIdrive)   
    elif which_key & 0xFF == ord('t'):#OpenCv 물체감지 활성화
        enable_object_detection = True
        print('object On', enable_object_detection)
    elif which_key & 0xFF == ord('r') 
        enable_object_detection = False
        print('object off', enable_object_detection)


    return is_exit  

def detect_maskY_HSV(frame):
    crop_hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    crop_hsv = cv.GaussianBlur(crop_hsv, (5,5), cv.BORDER_DEFAULT)
    # need to tune params
    mask_Y = cv.inRange(crop_hsv, (25, 50, 100), (35, 255, 255))
    return mask_Y

def detect_maskY_BGR(frame):
    B = frame[:,:,0]
    G = frame[:,:,1]
    R = frame[:,:,2]
    Y = np.zeros_like(G, np.uint8)
    # need to tune params
    Y = G*0.5 + R*0.5 - B*0.7 # 연산 수행 시 float64로 바뀜
    Y = Y.astype(np.uint8)
    Y = cv.GaussianBlur(Y, (5,5), cv.BORDER_DEFAULT)
    # need to tune params
    _, mask_Y = cv.threshold(Y, 100, 255, cv.THRESH_BINARY)
    return mask_Y

def line_tracing(cx):
    #print('cx, ', cx)
    #print('v_x_grid', v_x_grid)
    global moment
    global v_x
    tolerance = 0.1
    diff = 0

    if moment[0] != 0 and moment[1] != 0 and moment[2] != 0:
        avg_m = np.mean(moment)
        diff = np.abs(avg_m - cx) / v_x
    
    #print('diff ={:.4f}'.format(diff))

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
        #print('show_grid', x)
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
    #print('id', id(model))
    img = np.expand_dims(img, 0)
    res = model.predict(img)[0]
    #print('res', res)
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
    camera = cv.VideoCapture(0)
    camera.set(cv.CAP_PROP_FRAME_WIDTH,v_x) 
    camera.set(cv.CAP_PROP_FRAME_HEIGHT,v_y)

    camera2 = cv.VideoCapture(0)
    camera2.set(cv.CAP_PROP_FRAME_WIDTH,v_x_1)
    camera2.set(cv.CAP_PROP_FRAME_HEIGHT,v_y_1)

    
    try:
        while( camera.isOpened() ):
            ret, frame = camera.read()
            frame = cv.flip(frame,-1)
            cv.imshow('camera',frame)
            # image processing start here
            crop_img = frame[int(v_y/2):,:]
            crop_img = cv.resize(crop_img, (200, 66))
            cv.imshow('crop_img ', cv.resize(crop_img, dsize=(0,0), fx=2, fy=2))

            if enable_AIdrive == True:
                drive_AI(crop_img)

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
        global is_running
        is_running = False

if __name__ == '__main__':

    v_x = 320
    v_y = 240
    v_x_grid = [int(v_x*i/10) for i in range(1, 10)]
    print(v_x_grid)
    moment = np.array([0, 0, 0])

    model_path = 'lane_navigation_20251122_0111.h5'
    #model_path = 'my_checkpoint/lane_navigation_ce_stable.h5'     # tf1.15  
    #model_path = 'my_checkpoint/lane_navigation_20221115_0808.h5'  # tf1.15  
    #model_path = 'my_checkpoint/lane_navigation_20221115_0815.h5'  # tf2.2  
    
    model = load_model(model_path)
    '''print('id', id(model))
    print(model.summary())'''

    #test_fun(model)

    #DNN prepare
    class_names = []
    with open('object_detection_classes_coco.txt', 'r') as f:
        class_names = f.read().split('\n')
    COLORS = np.random.uniform(0, 255, size=(len(class_names), 3))

    model_od = cv.dnn.readNetFromTensorflow(model='frozen_inference_graph.pb', 
                                            config='ssd_mobilenet_v2_coco_2018_03_29.pbtxt')
    
    #Thread start
    t_task1 = threading.Thread(target = func_thread)
    t_task1.start()
    
    t_task2 = threading.Thread(target = object_detection_thread)
    t_task2.daemon = True
    t_task2.start()

    #car control object
    car = SDcar.Drive()
    
    #declare variable
    global object_detected, enable_object_detection, model_od, class_names
    #reset variable

    enable_object_detection = False
    object_detected = False
    lock = threading.Lock() #thread lock

    is_running = True
    enable_AIdrive = False
    main() 
    is_running = False
    car.clean_GPIO()
    print('end vis')
