
import cv2 as cv
import numpy as np
import threading
import time
import SDcar

def func_thread():
    i = 0
    while True:
        print("alive")
        time.sleep(1)
        i = i + 1
        if is_running is False:
            break

def key_cmd(which_key):
    print('which_key' , which_key)
    if_exit = False

def camera():
     camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)

    while camera.isOpened():
        _, image = camera.read()
        cv2.imshow('camera test', image)

        if cv2.waitKey(1) == ord('q'):
            break
            
    cv2.destroyAllWindows()

def key_cmd(which_key):
    print('which_key', which_key)
    is_exit = False
    global enable_linetracing

    #정지
    if which_key & 0xFF == ord('q'):
        car.motor_stop()
        print('exit')
    #시작
    elif which_key & 0xFF == ord('e'):
        enable_linetracing = True
        print('enable_linetracing: ', enable_linetracing)
    #일시정지
    elif which_key & 0xFF == ord('w'):
        enable_linetracing = False
        car.motor_stop()
        print('enable_linetracing: ', enable_linetracing)
        
    return is_exit

def detect_maskY_BGR(frame):
    B = frame[:,:,0]
    G = frame[:,:,1]
    R = frame[:,:,2]
    Y = np.zeros_like(G, np.unit8)

    Y = G*0.5 + R*0.5 - B*0.7 
    Y = Y.astype(np.unit8)
    Y = cv.GaussianBlur(Y, (5,5), cv.BORDER_DEFAULT)

    _, mask_Y = cv.threshold(Y, 100, 255, cv.THRESH_BINARY)
    
    return mask_Y


def detect_maskY_HVS(frame):
    crop_hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    crop_hsv = cv.GaussianBlur(crop_hsv, (5,5), cv.BORDER_DEFAULT)

    mask_Y = cv.inrang(crop_hsv , (25, 50, 100), (35, 255, 255))
    return mask_Y



def show_grid(img):
    h,_,_ = img.shape
    for x in v_x_grid:
        cv.line(img, (x,0), (x,h), (0,255,0),1,cv.LINE_4)





if __name__ == '__main__':

    v_x = 320
    v_y = 240 
    v_x_grid = [int(v_x*i/10) for i in range(1,10)]

    moment = np.array([0,0,0])
    print(v_x_grid)

    t_task1 = threading.Thread(target = func = func_thread)
    t_task1.start()

    car = SDcar.Drive()

    is_running = True
    enable_linetracing = False
    main()
    is_running = False
    car.clean_GPIO()
    print('end vis')
