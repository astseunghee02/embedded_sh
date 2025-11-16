import cv2

img = cv2.imread("./img_1.png", cv2.IMREAD_COLOR)

if img is not None:

    img = cv2.resize(img, (600, 400))
    
    print('img shape : ', img.shape)

    img_1ch = img.copy()
    img_1ch[:, :, 1] = 0
    img_1ch[:, :, 2] = 0

    cv2.imshow("img", img)
    cv2.imshow("img_1ch", img_1ch)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

else:
    print("Image file not found")