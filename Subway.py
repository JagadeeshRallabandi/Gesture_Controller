import os
import cv2 
import time
from pynput.keyboard import Key, Controller
import pyautogui
import numpy as np
import tensorflow as tf
from object_detection.utils import config_util
from object_detection.protos import pipeline_pb2
from google.protobuf import text_format
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder

def main():

    keyboard = Controller() 
    configs = config_util.get_configs_from_pipeline_file("workspace/models/my_ssd_mobnet/pipeline.config")
    detection_model = model_builder.build(model_config=configs['model'], is_training=False)

    # Restore checkpoint
    ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
    ckpt.restore(os.path.join("workspace/models/my_ssd_mobnet/ckpt-6")).expect_partial()

    @tf.function
    def detect_fn(image):
        image, shapes = detection_model.preprocess(image)
        prediction_dict = detection_model.predict(image, shapes)
        detections = detection_model.postprocess(prediction_dict, shapes)
        return detections


    category_index = label_map_util.create_category_index_from_labelmap("workspace/annotations/label_map.pbtxt")

    cap = cv2.VideoCapture(0)
    flag = True

    while True: 
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        # frame = cv2.resize(frame, (1200, 900))
        image_np = np.array(frame)
        
        input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
        detections = detect_fn(input_tensor)
        
        num_detections = int(detections.pop('num_detections'))
        detections = {key: value[0, :num_detections].numpy()
                    for key, value in detections.items()}
        detections['num_detections'] = num_detections

        # detection_classes should be ints.
        detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

        label_id_offset = 1
        image_np_with_detections = image_np.copy()

        viz_utils.visualize_boxes_and_labels_on_image_array(
                    image_np_with_detections,
                    detections['detection_boxes'],
                    detections['detection_classes']+label_id_offset,
                    detections['detection_scores'],
                    category_index,
                    use_normalized_coordinates=True,
                    max_boxes_to_draw=5,
                    min_score_thresh=.5,
                    agnostic_mode=False)

        cv2.imshow('Object Detection',  cv2.resize(image_np_with_detections, (930,800)))
        pred = detections["detection_classes"][0]
        score = detections["detection_scores"][0]

        if(pred == 0 and score >= 0.40):            # Up   
                keyboard.press(Key.up)
                print("Up")
        elif(pred == 1 and score >= 0.30):          # Down         
                keyboard.press(Key.down)
                print("Down")
        elif(pred == 2 and score >= 0.30):          # Right                
            keyboard.press(Key.right)
            print("Right")
        elif(pred == 3 and score >= 0.30):          # Left              
            keyboard.press(Key.left)
            print("Left")
        else:
            keyboard.release(Key.up)
            keyboard.release(Key.down)
            keyboard.release(Key.right)
            keyboard.release(Key.left)
            pass

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            break

if __name__ == "__main__":
    main()