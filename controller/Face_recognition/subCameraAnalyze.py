from datetime import datetime
import logging
import os
import queue
import threading
import time
import uuid
import torch

from unidecode import unidecode
from collections import Counter
from ultralytics.yolo.utils.plotting import Annotator

from controller.mivolo.person_model import PersonModel

from server.config import DATE_TIME_FORMAT, DATETIME_FORMAT, TELEGRAM_TOKEN
from server.reports.services import add_report_service, add_video_service
import cv2
from controller.Face_recognition.analyze_video_insightface import FaceAnalysisInsightFace
from controller.mivolo.predictor import Predictor

from PySide2.QtGui import (QPixmap,QImage)
from PySide2.QtWidgets import *
from config import STATIC_FOLDER
from PySide2.QtCore import QRunnable, Signal, QObject
import numpy as np
from server.extension import db_session

from PySide2.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
    QRect, QSize, QUrl, Qt,QThreadPool,QThread)

from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter,QPixmap,QImage,
    QRadialGradient)
from scipy.optimize import linear_sum_assignment
import telepot

from server.telegrams.services import get_list_telegrams_db
class CameraWorkerSignals(QObject):
    result = Signal(np.ndarray)
    finished = Signal()
    updateUI = Signal(list) 

class SubCameraAnalyze(QRunnable):
    def __init__(self,video_path):
        super().__init__()
        self.video_path = video_path
        self.video_path_report = video_path
        self.bot = telepot.Bot(TELEGRAM_TOKEN) 
        self.signals = CameraWorkerSignals()
        if type(self.video_path) == str:
            if 'rtsp' in self.video_path:
                path_dir = f"{STATIC_FOLDER}\\{os.path.dirname(str(self.video_path)).replace(':', '').replace('/', '')}"
                self.name_video = os.path.dirname(str(self.video_path)).replace(':', '').replace('/', '')
            else:
                self.name_video = os.path.basename(str(self.video_path))
                path_dir = f"{STATIC_FOLDER}\\{os.path.basename(str(self.video_path))}"
            # if not os.path.exists(path_dir):
            #     os.makedirs(path_dir)
        else:
            self.name_video = self.video_path
            path_dir = f"{STATIC_FOLDER}\\{str(self.name_video)}"
            # if not os.path.exists(path_dir):
            #     os.makedirs(path_dir)

        self.face_analyzer = FaceAnalysisInsightFace(path= self.name_video)
        self.predictor = Predictor()

        self.is_running = True
        self.is_send_telegram = True
        self.index_frame = 0
        self.telegram_buffer = queue.Queue()
        self.telegrams = get_list_telegrams_db()

        self.list_person_model = []
        self.list_total_id = []
        self.list_id_check_in_frame = []
        self.list_image_label = []
        self.buffer_frame = queue.Queue()
        # self.thread_greeting = threading.Thread(target=self.face_analyzer.welcomespeech)
        # self.thread_greeting.start()
        self.thread_send_telegram = threading.Thread(target=self.telegram_send_img_message)
        self.thread_send_telegram.start()

        if self.video_path.isdigit():
            self.video_path = int(self.video_path)
        self.video_capture = cv2.VideoCapture(self.video_path)

        self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        self.codec = self.video_capture.get(cv2.CAP_PROP_FOURCC)
        self.height_frame = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width_frame = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_count = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
       
        # self.output_video = cv2.VideoWriter(f"{path_dir}\\output.mp4",cv2.VideoWriter_fourcc(*'mp4v'), self.fps, (self.frame_width, self.frame_height))
        self.thread_analyze = threading.Thread(target=self.analyze_frame)
        self.thread_analyze = self.thread_analyze.start()
    
    
    def analyze_frame(self):
        while True:
            if not self.is_running:
                break
            frame = self.buffer_frame.get()
            if frame is not None:
                image, list_image_label = self.analyze_video(frame)
                self.signals.updateUI.emit(list_image_label)

    def run(self):
        while self.video_capture is not None:
            if not self.is_running:
                break
            ret, frame = self.video_capture.read()
            if ret:
                image = frame.copy()
                self.index_frame += 1
                self.face_analyzer.index_frame = self.index_frame  
                if self.index_frame % 3 == 0:
                    self.buffer_frame.put(image)
                self.signals.result.emit(image) 
            else:
                if not isinstance(self.video_path, int) and 'rtsp' not in self.video_path:
                    self.signals.result.emit(None)
                    print(f"{self.video_path} DONE")
                    self.signals.finished.emit()
                    self.stop()
                    return
                else:
                    self.video_capture.release()
                    self.video_capture = cv2.VideoCapture(self.video_path)
                    self.index_frame = 0
                    print(f"{self.video_path} RESTART")

    def stop(self):
        self.buffer_frame.put(None)
        if self.video_capture is not None:
            self.face_analyzer.is_running_greeting = False
            self.face_analyzer.buffer_label.put("")
            self.is_running = False
            self.is_send_telegram = False

            self.buffer_frame.put(None)
            self.telegram_buffer.put(None, None, None)

            self.video_capture.release()

            torch.cuda.empty_cache()
            
        list_thread = threading.enumerate()
        print(f"Active thread names: {', '.join([thread.name for thread in list_thread])}")

    def match_face_to_person(self,person_boxes, face_boxes):
        num_persons = len(person_boxes)
        num_faces = len(face_boxes)
        iou_matrix = np.zeros((num_persons, num_faces))
        for i in range(num_persons):
            for j in range(num_faces):
                iou_matrix[i, j] = self.calculate_iou(person_boxes[i][0][:4], face_boxes[j][0])
        row_ind, col_ind = linear_sum_assignment(-iou_matrix)
        # matched_pairs = [(row, col) for row, col in zip(row_ind, col_ind)]
        matched_pairs = [(row, col) for row, col in zip(row_ind, col_ind) if iou_matrix[row, col] > 0]
        return matched_pairs

    def get_matched_pairs(self,person_boxes, face_boxes):
        matched_pairs = self.match_face_to_person(person_boxes, face_boxes)
        all_pairs = []
        for person_idx, face_idx in matched_pairs:
            all_pairs.append((person_boxes[person_idx], face_boxes[face_idx]))
        unmatched_faces = set(range(len(face_boxes))) - set(col for _, col in matched_pairs)
        for face_idx in unmatched_faces:
            all_pairs.append((None, face_boxes[face_idx]))
        unmatched_bodies = set(range(len(person_boxes))) - set(row for row, _ in matched_pairs)
        for person_idx in unmatched_bodies:
            all_pairs.append((person_boxes[person_idx], None))
        return all_pairs

    def calculate_iou(self,box1, box2):
          try:
              x1, y1, w1, h1 = box1[0], box1[1], box1[2], box1[3]
              x2, y2, w2, h2 = box2[0], box2[1], box2[2], box2[3]

              x1_left, x1_right = x1, x1 + w1
              y1_top, y1_bottom = y1, y1 + h1
              x2_left, x2_right = x2, x2 + w2
              y2_top, y2_bottom = y2, y2 + h2

              x_intersection = max(0, min(x1_right, x2_right) - max(x1_left, x2_left))
              y_intersection = max(0, min(y1_bottom, y2_bottom) - max(y1_top, y2_top))
              intersection_area = x_intersection * y_intersection

              area1 = w1 * h1
              area2 = w2 * h2
              union_area = area1 + area2 - intersection_area
              iou = intersection_area / union_area
              return iou
          except Exception as e:
              print(f"[analyze_video_insightface][calculate_iou]: {e}")
              return 0
        
    def extend_image(self,frame, face_box):
        try:
            x, y, w, h = face_box
            frame_height, frame_width = frame.shape[:2]
            if w < 64:
                target_size = (128, 128)
            else:
                target_size = (int(w*2), int(h*2))  
            delta_w = target_size[0] - w
            delta_h = target_size[1] - h
            x1, y1 = int(x - delta_w // 2), int(y - delta_h // 2)
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = int(min(frame_width, x1 + target_size[0]))
            y2 = int(min(frame_height, y1 + target_size[1]))
            expanded_face = frame[y1:y2, x1:x2]
            return expanded_face
        except Exception as e:
            print(f"[{datetime.now().strftime(DATETIME_FORMAT)}][analyze_video][extract_face]: ", e)
            return None
    
    def count_most_frequent_element(self,lst):
        if len(lst) == 0:
            return None
        
        element_count = Counter(lst)
        max_count = max(element_count.values())
        most_frequent_elements = [key for key, value in element_count.items() if value == max_count]
        
        return most_frequent_elements[0]

    def average_number(self,age_list):
        if not age_list or age_list is None:  # Check if the list is empty to avoid division by zero
            return 0
        total_age = sum(age_list)
        average = total_age / len(age_list)
        
        return average
    
    def add_seconds_to_datetime(self,current_qdatetime, seconds):
        # Get the current QDateTime from dateTimeEdit_start
        # Add seconds to the current QDateTime
        new_qdatetime = current_qdatetime.addSecs(seconds)

        return new_qdatetime
  

    def analyze_video(self, image):
        try:
            frame = image.copy()
        
            result_track = []
            list_image_label = []
            logging.info(f"[analyze_video][time_detect]: Tracking start")
            result_track = self.predictor.analyze_tracking_boxmot(frame)
            # insightface recognition
            list_recognition_insightface = []
            logging.info(f"[analyze_video_insightface][time_insightface]: Insightface start")
            list_recognition_insightface = self.face_analyzer.analyze_insightface_frame(frame)
            logging.info(f"[analyze_video_insightface][time_insightface]: Merge start")
            list_recognition_insightface_merge = self.get_matched_pairs(result_track, list_recognition_insightface)

            annotator = Annotator(
                    frame,
                    None,
                    None,
                    font="Arial.ttf",
                    pil=False,
                )
            color_person = (0, 255, 0)
            color_text = (0, 0, 0)
            color_face = (255, 255, 0)

            box_face = []
            box_person = []

            for d, instance in list_recognition_insightface_merge:
                image_save = image.copy()
                extend_face_image = None
                person_image = None
                face_image = None
                
                label = ""
                path_dir_image = ""
                path_save_face_image = ""
                path_save_person_image = ""

                label_name = None
                label_mask = None
                position = None

                guid = None
                age = None
                gender = None
                main_color_clothes = None
                name_color = None

                annotator_save = Annotator(
                    image_save,
                    None,
                    None,
                    font="Arial.ttf",
                    pil=False,
                )

                if instance is not None and len(instance) > 0:
                    box_face = instance[0]
                    label_name = instance[1]
                    position = instance[3]
                    age = instance[4]
                    gender = instance[5]
                    label_mask = instance[6]

                    box_face = [int(box_face[0]), int(box_face[1]), int(box_face[2]), int(box_face[3])]
                    face_image = image[max(box_face[1],0):min(box_face[3], frame.shape[0]), max(box_face[0],0):min(box_face[2], frame.shape[1])]
                    box_face_plot = [box_face[0], box_face[1], box_face[2], box_face[3]]
                    
                    if face_image is None or face_image.shape[0] == 0 or face_image.shape[1] == 0:
                        face_image = None
                    else:
                        extend_face_image = self.extend_image(image, box_face)
                    if label_name is not None:
                        label_name = unidecode(label_name)
                        label = f" {label_name}"
                    else:
                        label = ""
                    label += f" {age:.1f}"
                    if gender is not None:
                        if gender == "male":
                            label += "M"
                        else:
                            label += "F"

                    if label_mask is not None:
                        if label_mask == 0:
                            label += f" No Mask"
                            color_face = (0, 0, 255)
                        elif label_mask == 1:
                            label += f" Mask"
                            color_face = (255, 0, 0)

                    annotator.box_label(box_face_plot,"",color_face)
                    annotator_save.box_label(box_face_plot,"",color_face)
                
                if d is not None and len(d) > 0:
                    box_person = d[0][0:4]
                    guid = d[0][4]
                    label += f" {guid}"
                    main_color_clothes = d[1]
                    name_color = d[2]
                    if main_color_clothes is not None:
                        color_person = main_color_clothes
                        color_text = (255, 255, 255)

                    person_image = image[box_person[1]:box_person[3], box_person[0]:box_person[2]]
                    annotator.box_label(box_person, label, color=color_person,txt_color=color_text)
                    annotator_save.box_label(box_person, label, color=color_person,txt_color=color_text)

                frame = annotator.result()

                if label_name is not None and face_image is not None:
                    path_dir_image = f"{STATIC_FOLDER}/results/{datetime.now().strftime(DATE_TIME_FORMAT)}/Camera_{self.name_video}_{os.path.basename(self.video_path_report)}/id_{label_name.replace(' ', '')}"
                    path_save_face_image = f"{path_dir_image}/face_{time.time()}.jpg"
                    if person_image is not None:
                        path_save_person_image = f"{path_dir_image}/person_{time.time()}.jpg"
                elif label_name is None:
                    if face_image is not None or person_image is not None:
                        path_dir_image = f"{STATIC_FOLDER}/results/{datetime.now().strftime(DATE_TIME_FORMAT)}/Camera_{self.name_video}_{os.path.basename(self.video_path_report)}/id_{guid}"
                    if face_image is not None:
                        path_save_face_image = f"{path_dir_image}/face_{time.time()}.jpg"
                    if person_image is not None:
                        path_save_person_image = f"{path_dir_image}/person_{time.time()}.jpg"

                if path_dir_image != "" and not os.path.exists(path_dir_image):
                    os.makedirs(path_dir_image)
                    print(f"Create folder {path_dir_image}")
                elif path_dir_image == "":
                    path_save_face_image = ""
                    path_save_person_image = ""

                path_image = f"{path_dir_image}/origin_{time.time()}.jpg"

                if guid == None:
                    guid = uuid.uuid4()
                    
                if guid not in self.list_total_id:
                    person_model = PersonModel()
                    # person model
                    person_model.id = guid
                    if label_name is not None:
                        person_model.list_face_name.append(label_name)
                        person_model.label_name = label_name
                    
                    # Mask
                    if label_mask is not None:
                        person_model.list_check_masks.append(label_mask)
                        person_model.average_check_mask = label_mask

                    # Age
                    if age is not None:
                        person_model.list_age.append(age)
                        person_model.average_age = age

                    # Gender
                    if gender is not None:
                        person_model.list_gender.append(gender)
                        person_model.average_gender = gender  
                    
                    # Main color
                    if main_color_clothes is not None:
                        person_model.code_color = f"{main_color_clothes[0]},{main_color_clothes[1]},{main_color_clothes[2]}"
                    if name_color is not None:
                        person_model.name_color = name_color

                    time_label = datetime.now().strftime(DATETIME_FORMAT)
                    person_model.list_image_path = []
                    if extend_face_image is not None and path_save_face_image != "":
                        if extend_face_image.shape[0] > 0 and extend_face_image.shape[1] > 0:
                            cv2.imwrite(path_save_face_image, face_image)
                            person_model.list_image_path.append(path_save_face_image)
                            if label_name is not None:
                                person_model.role = 2
                            else:
                                if box_face[2] < 50:
                                    person_model.role = 1
                                else:
                                    person_model.role = 0

                    if person_image is not None and person_image.shape[0] > 0 and person_image.shape[1] > 0:
                            if extend_face_image is None:
                                person_model.role = 1
                            cv2.imwrite(path_save_person_image, person_image)
                            person_model.list_image_path.append(path_save_person_image)
                            person_model.person_image = path_save_person_image

                    cv2.imwrite(path_image, image_save)
                    person_model.list_image_path.append(path_image)
                    person_model.time = int(time.time())
                    self.list_person_model.append(person_model)
                    self.list_total_id.append(guid)
                else:
                    index = self.list_total_id.index(guid)
                    if self.index_frame % 1 == 0:
                        if label_name is not None:
                            self.list_person_model[index].list_face_name.append(label_name)
                            if len(self.list_person_model[index].list_face_name) > 50:
                                del self.list_person_model[index].list_face_name[0]
                        if age is not None:
                            self.list_person_model[index].list_age.append(age)
                            if len(self.list_person_model[index].list_age) > 50:
                                del self.list_person_model[index].list_age[0]
                        
                        if gender is not None:
                            self.list_person_model[index].list_gender.append(gender)
                            if len(self.list_person_model[index].list_gender) > 50:
                                del self.list_person_model[index].list_gender[0]

                        if label_mask is not None:
                            self.list_person_model[index].list_check_masks.append(label_mask)
                            if len(self.list_person_model[index].list_check_masks) > 50:
                                del self.list_person_model[index].list_check_masks[0]
                        if label_name is not None:
                            self.list_person_model[index].label_name = label_name
                        if main_color_clothes is not None:
                            self.list_person_model[index].code_color = f"{main_color_clothes[0]},{main_color_clothes[1]},{main_color_clothes[2]}"
                        if name_color is not None:
                            self.list_person_model[index].name_color = name_color

                    self.list_person_model[index].counting_tracking += 1

                    # Send telegram
                    if (self.list_person_model[index].counting_tracking % 2 == 0 or self.list_person_model[index].counting_tracking == 1 or (self.list_person_model[index].label_name != label_name and label_name is not None)):
                        if label_name is not None:
                            self.list_person_model[index].label_name = label_name
                        if gender is not None:
                            self.list_person_model[index].average_gender = gender
                        else:
                            self.list_person_model[index].average_gender = self.count_most_frequent_element(self.list_person_model[index].list_gender)

                        self.list_person_model[index].average_age = self.average_number(self.list_person_model[index].list_age)
                        self.list_person_model[index].average_check_mask = label_mask
                        if len(self.list_person_model[index].list_age) > 0:
                            self.list_person_model[index].start_age = min(self.list_person_model[index].list_age)
                            self.list_person_model[index].end_age = max(self.list_person_model[index].list_age)
                        
                        time_label = datetime.now().strftime(DATETIME_FORMAT)
                        if extend_face_image is not None and path_save_face_image != "":
                            if extend_face_image.shape[0] > 0 and extend_face_image.shape[1] > 0:
                                extend_face_image = cv2.resize(extend_face_image, (128, 128))
                                cv2.imwrite(path_save_face_image, face_image)
                                self.list_person_model[index].face_image = path_save_face_image
                                if self.list_person_model[index].counting_telegram < 5:
                                    list_image_label.append([path_save_face_image, label_name, position, age, gender, guid, main_color_clothes,label_mask, time_label])
                                    self.list_person_model[index].counting_telegram += 1
                                if label_name is not None:
                                    self.list_person_model[index].role = 2
                                else:
                                    if box_face[2] < 50:
                                        self.list_person_model[index].role = 1
                                    else:
                                        self.list_person_model[index].role = 0
                        if person_image is not None and person_image.shape[0] > 0 and person_image.shape[1] > 0:
                            
                            cv2.imwrite(path_save_person_image, person_image)
                            self.list_person_model[index].person_image = path_save_person_image
                            if path_save_person_image not in self.list_person_model[index].list_image_path:
                                self.list_person_model[index].list_image_path.append(path_save_person_image)
                            if self.list_person_model[index].counting_telegram < 3 and path_save_face_image == "":
                                list_image_label.append([path_save_person_image, label_name, position, age, gender, guid, main_color_clothes,label_mask, time_label])
                                self.list_person_model[index].counting_telegram += 1
                            if extend_face_image is None:
                                self.list_person_model[index].role = 1
                        cv2.imwrite(path_image, image_save)
                        if self.list_person_model[index].counting_telegram < 2:
                            self.telegram_buffer.put([path_image, self.list_person_model[index], self.telegrams])
                          
                        self.list_person_model[index].list_image_path.append(path_image)
            
            # Send data to report
            if self.index_frame % 500 == 0:
                logging.info(f"[analyze_video][index_frame] Send data to report: {self.index_frame}, {len(self.list_person_model)}")
                if len(self.list_person_model) > 0:
                    self.send_report_to_db()
                    self.list_person_model = []
                    self.list_total_id = []
                         
            return frame,list_image_label
        except Exception as e:
            print(f'[{datetime.now().strftime(DATETIME_FORMAT)}][analyze][generate_frames]: {e}')
            logging.exception(f'[analyze][generate_frames]: {e}')
            return image,[]
        
    def telegram_send_img_message(self):
        try:
      # for telegram in telegrams:
            while True:
                if self.is_send_telegram == False:
                    break
                img_path, person_model, telegrams = self.telegram_buffer.get()
                if img_path is None and person_model is None and telegrams is None:
                    continue
                print(f"Telegram send image: {img_path}")
                text_send = f"*Camera: {self.name_video}*\n"
                text_send += f"ID: _{person_model.id}_\n"
      
                if person_model.label_name is not None and person_model.label_name != "":
                    text_send += f"Tên: *{person_model.label_name}*\n"
                else:
                    if person_model.role == 1:
                        text_send += f"Tên: Người không xác định\n"
                    elif person_model.role == 0:
                        text_send += f"Nhân viên: Người lạ\n"

                if person_model.average_check_mask is not None and person_model.average_check_mask == 1:
                    text_send += f"Đeo khẩu trang: _Có_\n"
                elif person_model.average_check_mask is not None and person_model.average_check_mask == 0:
                    text_send += f"Đeo khẩu trang: _Không_\n"
                else:
                    text_send += f"Đeo khẩu trang: _Không xác định_\n"
                if person_model.average_age is not None:
                    if person_model.start_age is None:
                        person_model.start_age = 0
                    if person_model.end_age is None:
                        person_model.end_age = 0
                    text_send += f"Tuổi: _{int(person_model.start_age)}_ - _{int(person_model.end_age)}_\n"
                else:
                    text_send += f"Tuổi: _Không xác định_\n"
                if person_model.average_gender != "" and person_model.average_gender is not None:
                    if person_model.average_gender is not None:
                        gender = person_model.average_gender
                    if gender == "male" or gender[0] == "male":
                        text_send += f"Giới tính: _Nam_\n"
                    elif gender == "female" or gender[0] == "female":
                        text_send += f"Giới tính: _Nữ_\n"
                else:
                    text_send += f"Giới tính: _Không xác định_\n"
                if person_model.name_color != "" and person_model.name_color is not None:
                    text_send += f"Màu trang phục: _{person_model.name_color}_\n"
                else:
                    text_send += f"Màu trang phục: _Không xác định_\n"

                text_send += f"Thời gian nhận diện: _{datetime.fromtimestamp(person_model.time)}_\n"

                for telegram in telegrams:
                    try:
                        time_start = time.time()
                        self.bot.sendPhoto(telegram.chat_id, photo=open(img_path, 'rb'), caption=text_send, parse_mode= 'Markdown')
                        time_end = time.time()
                        logging.info(f"time telegram: {time_end - time_start}s")
                    except Exception as ex:
                        print(f"Exception[send_telegram_message]: {ex}")
                        logging.error(f"Exception[send_telegram_message]: {ex}")
                self.telegram_buffer.task_done()
        except Exception as ex:
            print(f"Exception[telegram_send_img_message]: {ex}")
            logging.error(f"Exception[telegram_send_img_message]: {ex}")
        
    def send_report_to_db(self):
        try:
            for i, person_model in enumerate(self.list_person_model):
                if len(person_model.list_image_path) == []:
                    continue
                if person_model.average_gender is not None:
                    if person_model.average_gender == "male":
                        gender = 1
                    elif person_model.average_gender == "female":
                        gender = 0
                else:
                    gender = 2
                # gender = person_model.average_gender
                if person_model.average_age is not None:
                    age = int(person_model.average_age)
                else: 
                    age = 0
                # person_model_time = datetime.strptime(person_model.time, "%Y-%m-%d %H:%M:%S")
                # Lấy timestamp
                # time_model = person_model_time.timestamp()
                time_model = person_model.time
                # time_model = datetime.timestamp(person_model.time)
                if person_model.average_check_mask == 1:
                    mask = 1
                else:
                    mask = 0
                if person_model.average_check_glasses == True:
                    glasses = 1
                else:
                    glasses = 0
                main_color_clothes = person_model.code_color
                name_color = person_model.name_color
                if person_model.label_name is None or person_model.label_name == "":
                    person_name = f"random_{uuid.uuid4()}"
                else:
                    person_name = person_model.label_name
                if person_model.face_image is not None:
                    person_model.is_front = 1
                add_report_service(self.video_path_report, person_name, age, gender, mask, main_color_clothes, time_model, person_model.list_image_path, person_model.is_front, person_model.real_time)
        except Exception as e:
            print(f'[{datetime.now().strftime(DATETIME_FORMAT)}][analyze][send_report_to_db]: {e}')
                
class CameraWidget(QWidget):
    def __init__(self, path, index, parent=None):
        super(CameraWidget, self).__init__(parent)
        self.path = path
        self.thread_pool = parent.thread_pool
        
        self.list_camera = parent.list_camera
        self.list_camera_screen = parent.list_camera_screen
        self.grid_layout = parent.grid_layout
        self.ref_layout = parent.ref_layout

        self.camera_layout = QVBoxLayout()

        self.camera_label = QLabel(self)
        self.close_button = QPushButton(self)

        self.close_button.setObjectName(u"close_button_{}".format(index))
        self.close_button.setStyleSheet(u"QPushButton {\n"
            "	border: 2px solid rgb(27, 29, 35);\n"
            "	border-radius: 5px;	\n"
            "	background-color: rgb(27, 29, 35);\n"
            "}\n"
            "QPushButton:hover {\n"
            "	background-color: rgb(57, 65, 80);\n"
            "	border: 2px solid rgb(61, 70, 86);\n"
            "}\n"
            "QPushButton:pressed {	\n"
            "	background-color: rgb(35, 40, 49);\n"
            "	border: 2px solid rgb(43, 50, 61);\n"
            "}")
        self.close_button.setIcon(QIcon(u":/16x16/icons/16x16/cil-x.png"))
        self.close_button.setIconSize(QSize(16, 16))
        self.close_button.setFixedSize(30, 30)

        self.camera_layout.addWidget(self.camera_label)
        self.camera_layout.addWidget(self.close_button)

        self.camera_label.setObjectName(u"camera_label_{}".format(index))
        self.camera_label.setStyleSheet("border: 2px solid red;")

        self.close_button.clicked.connect(self.stop_camera)
        self.camera_label.setAlignment(Qt.AlignCenter)

        self.setLayout(self.camera_layout)
        self.start_camera()

    def start_camera(self):
        add_video_service(self.path)
        self.worker = SubCameraAnalyze(self.path)
        self.worker.signals.result.connect(self.display_image)
        self.worker.signals.updateUI.connect(self.update_ui)
        self.worker.signals.finished.connect(self.thread_pool.waitForDone)
        # self.worker.run()
        # Execute the worker in a separate thread from the thread pool
        self.thread_pool.start(self.worker)

    def stop_camera(self):
        if self.worker:
            self.worker.signals.result.disconnect(self.display_image)
            self.worker.signals.updateUI.disconnect(self.update_ui)
            self.worker.stop()
            
        # Stop the camera capture
        self.thread_pool.clear()
        print(f"Length thread pool: {self.thread_pool.activeThreadCount()}")
        self.camera_layout.removeWidget(self.camera_label)
        self.camera_label.deleteLater()
        self.camera_layout.removeWidget(self.close_button)
        self.close_button.deleteLater()
        self.grid_layout.removeWidget(self.list_camera_screen[self.path])
        self.list_camera_screen[self.path].deleteLater()
        del self.camera_label
        del self.close_button
        del self.list_camera_screen[self.path]
        index = self.list_camera.index(str(self.path))
        self.list_camera.remove(str(self.path))
        self.update_camera_layout_positions(index)

    def update_camera_layout_positions(self, removed_index):
        if len(self.list_camera_screen) > 4:
            self.num_col = 3
        elif len(self.list_camera_screen) == 1:
            self.num_col = 1
        else:
            self.num_col = 2
        for i, path in enumerate(self.list_camera):
            if i >= removed_index:
                # Calculate the new row and column for the remaining layouts
                row = i // self.num_col
                col = i % self.num_col

                # Update the position of the layout in the grid_layout
                self.grid_layout.removeWidget(self.list_camera_screen[path])
                self.grid_layout.addWidget(self.list_camera_screen[path], row, col, 1, 1)
                self.list_camera_screen[path].setObjectName(u"camera_label_{}".format(i + 1))

    def display_image(self, frame):
        # Display the captured frame
        if frame is None:
            self.camera_label.setText("No Frame")
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio)
        # check camera_label attribute camerawidget
        if self.camera_label:
            self.camera_label.setPixmap(scaled_pixmap)

    def update_ui(self, list_image_label):
        try:
            if self.ref_layout.count() == 20:
                self.clear_layout(self.ref_layout)

            for i in range(len(list_image_label)):
                h_layout = QHBoxLayout()  # Create a QHBoxLayout for each row
                recognition_image = cv2.imread(list_image_label[i][0])
                if recognition_image.shape[0] >recognition_image.shape[1]:
                    recognition_image = cv2.resize(recognition_image, (128*recognition_image.shape[1]//recognition_image.shape[0], 128))
                else:
                    recognition_image = cv2.resize(recognition_image, (128, 128*recognition_image.shape[0]//recognition_image.shape[1]))
                image = cv2.cvtColor(recognition_image, cv2.COLOR_BGR2RGB)
                # Convert image to QImage
                height, width, channel = image.shape
                bytes_per_line = 3 * width
                q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)

                # Set the image to the QLabel
                pixmap = QPixmap.fromImage(q_image)
                image_label = QLabel(f"Label {i * 2 + 1}")

                if list_image_label[i][1] is not None and list_image_label[i][1] != "":
                    image_label.setStyleSheet("border: 1px solid green; border-radius: 5px; margin-bottom: 5px;")
                else:
                    image_label.setStyleSheet("border: 1px solid red; border-radius: 5px; margin-bottom: 5px;")
                image_label.setPixmap(pixmap)
                # image_label.setScaledContents(True)
                text_label = QLabel(f"Label {i * 2 + 2}")
                text_label.setStyleSheet("border: 1px solid gray; border-radius: 5px; margin-bottom: 5px;")
            
                if len(list_image_label[i]) > 1:
                    text_label.setText(self.update_text(list_image_label[i]))
                else:
                    text_label.setText(f"")
                h_layout.addWidget(image_label)
                h_layout.addWidget(text_label)
                self.ref_layout.insertLayout(0, h_layout)
              
        except Exception as e:
            print(f"[update_ui]: {e}")

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.clear_layout(item.layout())
    
    def update_text(self,label):
        label_text = f"<b>Họ và tên: {label[1]}</b>"
        label_text += f"<br>Đối tượng: {label[2]}"
        label_text += f"<br>Tuổi: {label[3]}"
        label_text += f"<br>Giới tính: {label[4]}"
        if label[7] == 1:
            label_text += f"<br>Đeo khẩu trang"
        label_text += f"<br>Thời gian: {label[8]}"
        
        return label_text

    def resizeEvent(self, event):
        if self.camera_label:
            self.camera_label.setFixedSize(self.size())
        super().resizeEvent(event)

