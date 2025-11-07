import cv2
import numpy as np

threshold_move = 50
diff_compare = 10

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

_, img_first = cap.read()
_, img_second = cap.read()
img_first = cv2.flip(img_first, 0)
img_second = cv2.flip(img_second, 0)

while True:
    _, img_third = cap.read()
    img_third = cv2.flip(img_third, 0)
    scr = img_third.copy()

    img_first_gray = cv2.cvtColor(img_first, cv2.COLOR_BGR2GRAY)
    img_second_gray = cv2.cvtColor(img_second, cv2.COLOR_BGR2GRAY)
    img_third_gray = cv2.cvtColor(img_third, cv2.COLOR_BGR2GRAY)

    diff_1 = cv2.absdiff(img_first_gray, img_second_gray)
    diff_2 = cv2.absdiff(img_second_gray, img_third_gray)

    _, mask1 = cv2.threshold(diff_1, threshold_move, 255, \
        cv2.THRESH_BINARY)
    _, mask2 = cv2.threshold(diff_2, threshold_move, 255, \
        cv2.THRESH_BINARY)
    
    diff = cv2.bitwise_and(mask1, mask2)
    diff_cnt = cv2.countNonZero(diff)

    if diff_cnt > diff_compare:
        nzero = np.nonzero(diff)
        cv2.rectangle(scr, (min(nzero[1]), min(nzero[0])), \
            (max(nzero[1]), max(nzero[0])), (0, 255, 0), 1)
        cv2.putText(scr, "Motion Detected", (10, 10), \
            cv2.FONT_HERSHEY_DUPLEX, 0.3, (0, 255, 0))

    cv2.imshow('Motion detection', scr)

    img_first = img_second
    img_second = img_third

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()