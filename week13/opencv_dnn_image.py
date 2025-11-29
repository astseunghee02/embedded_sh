import cv2 as cv
import numpy as np

class_names = []
with open('object_detection_classes_coco.txt', 'r') as f:
    class_names = f.read().split('\n')
print(class_names)
COLORS = np.random.uniform(0, 255, size=(len(class_names), 3))
print(COLORS)

model = cv.dnn.readNetFromTensorflow(model='frozen_inference_graph.pb', \
                                     config='ssd_mobilenet_v2_coco_2018_03_29.pbtxt')

image = cv.imread('person.jpeg')
image_height, image_width, _ = image.shape
# create blob from image
blob = cv.dnn.blobFromImage(image=image, size=(300, 300), swapRB=True)
# set the blob to the model
model.setInput(blob)
# forward pass through the model to carry out the detection
output = model.forward()

# loop over each of the detection
for detection in output[0, 0, :, :]:
    # extract the confidence of the detection
    confidence = detection[2]
    # draw bounding boxes only if the detection confidence is above...
    # ... a certain threshold, else skip
    if confidence > .4:
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

#cv.imshow('image', image)
cv.imwrite('person_result.jpeg', image)
#cv.waitKey(0)
#cv.destroyAllWindows()