import numpy as np
import sys
import cv2
import os

import datetime

from enum import Enum

import modules.log as log

from cvlib.object_detection import draw_bbox

class YoloModel(str, Enum):
    yolov3      = "yolov3"
    yolov3_tiny = "yolov3_tiny"
    yolov3_spp  = "yolov3_spp"

#https://github.com/arunponnusamy/object-detection-opencv/raw/master/yolov3.txt
#https://pjreddie.com/media/files/yolov3-tiny.weights
#https://github.com/pjreddie/darknet/raw/master/cfg/yolov3-tiny.cfg

yolov3_config_file="./models/yolov3.cfg"
yolov3_labels_file="./models/yolov3.txt"
yolov3_weights_file="./models/yolov3.weights"

yolov3_tiny_config_file="./models/yolov3-tiny.cfg"
yolov3_tiny_labels_file="./models/yolov3.txt"
yolov3_tiny_weights_file="./models/yolov3-tiny.weights"

yolov3_spp_config_file="./models/yolov3-spp.cfg"
yolov3_spp_labels_file="./models/yolov3.txt"
yolov3_spp_weights_file="./models/yolov3-spp.weights"

class Detector:
    def __init__(self, model: YoloModel):
        self.name = model
        self.model = model

        start = datetime.datetime.now()

        if self.model == YoloModel.yolov3_tiny:
            config_file_abs_path = yolov3_tiny_config_file
            weights_file_abs_path = yolov3_tiny_weights_file
            class_file_abs_path = yolov3_tiny_labels_file
        elif self.model == YoloModel.yolov3:
            config_file_abs_path = yolov3_config_file
            weights_file_abs_path = yolov3_weights_file
            class_file_abs_path = yolov3_labels_file
        else:
            config_file_abs_path = yolov3_spp_config_file
            weights_file_abs_path = yolov3_spp_weights_file
            class_file_abs_path = yolov3_spp_labels_file

        f = open(class_file_abs_path, 'r')
        self.classes = [line.strip() for line in f.readlines()]
        self.net = cv2.dnn.readNet(weights_file_abs_path, config_file_abs_path)
        
        log.logger.debug('Initialized detector: {}'.format(self.name))
        log.logger.debug('config:{}, weights:{}'.format(config_file_abs_path, weights_file_abs_path))

        stop = datetime.datetime.now()
        elapsed_time = stop - start
        print("initialization took:", elapsed_time)

    def get_name(self):
        return self.name
	
    def get_classes(self):
        return self.classes

    def get_output_layers(self):
        layer_names = self.net.getLayerNames()
        output_layers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
        return output_layers

    def detect(self, fi, fo, args):
        log.logger.debug("Reading {}".format(fi))
        image = cv2.imread(fi)

        Height, Width = image.shape[:2]
        scale = 0.00392
        
        blob = cv2.dnn.blobFromImage(image, scale, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.get_output_layers())
        
        class_ids = []
        confidences = []
        boxes = []
        conf_threshold = 0.5
        nms_threshold = 0.4

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    center_x = int(detection[0] * Width)
                    center_y = int(detection[1] * Height)
                    w = int(detection[2] * Width)
                    h = int(detection[3] * Height)
                    x = center_x - w / 2
                    y = center_y - h / 2
                    class_ids.append(class_id)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])

        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

        bbox = []
        label = []
        conf = []

        for i in indices:
            i = i[0]
            box = boxes[i]
            x = box[0]
            y = box[1]
            w = box[2]
            h = box[3]
            bbox.append( [int(round(x)), int(round(y)), int(round(x + w)), int(round(y + h))])
            label.append(str(self.classes[class_ids[i]]))
            conf.append(confidences[i])

        if not args['delete']:
            out = draw_bbox(image, bbox, label, conf)
            log.logger.debug("Writing {}".format(fo))
            cv2.imwrite(fo, out)

        detections = []

        for l, c, b in zip(label, conf, bbox):
            log.logger.debug ('-----------------------------------------')
            c = "{:.2f}%".format(c * 100)
            obj = {
                'type': l,
                'confidence': c,
                'box': b
            }
            log.logger.debug("{}".format(obj))
            detections.append(obj)

        if args['delete']:
            log.logger.debug("Deleting file {}".format(fi))
            os.remove(fi)

        return detections                                   
