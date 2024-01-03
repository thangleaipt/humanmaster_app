import math
import os
import threading
from PySide2.QtCore import (QSize,QThreadPool)
from PySide2.QtGui import (QIcon)

from PySide2.QtWidgets import *
import cv2
import moviepy.editor as mp
from PySide2.QtGui import (QPixmap,QImage)
import numpy as np
import torch

from controller.mivolo.predictor import Predictor
from scipy.optimize import linear_sum_assignment
from ultralytics.yolo.utils.plotting import Annotator
from unidecode import unidecode

class PAGEIMAGE(QWidget):
    def __init__(self):
        super().__init__()
        self.new_size = 0
        self.list_camera_screen = {}
        self.scroll_area = None
        self.list_image = []
        self.thread_pool = QThreadPool()
        self.set_ui()
        self.setObjectName(u"page_image")
        self.face_analyzer = None
        self.predictor = Predictor()

    def set_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.control_layout = QVBoxLayout()
        self.add_button_layout = QHBoxLayout()
        self.grid_layout = QGridLayout()
        self.grid_layout.setObjectName(u"gridLayout")
        self.list_camera_labels = {}
        self.list_camera_layout = {}
        self.list_close_button = {}
       
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.ref_layout = QVBoxLayout(scroll_content)
         # Set the content widget for the scroll area
        self.scroll_area.setWidget(scroll_content)
    
        # Add video button
        self.add_image_button = QPushButton("Thêm ảnh")
        self.add_image_button.setStyleSheet(u"QPushButton {\n"
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
        icon3 = QIcon()
        icon3.addFile(u":/16x16/icons/16x16/cil-folder-open.png", QSize(), QIcon.Normal, QIcon.Off)
        self.add_image_button.setIcon(icon3)
        self.add_image_button.clicked.connect(self.show_dialog_image)
        self.add_button_layout.addWidget(self.add_image_button)

        self.delete_image_button = QPushButton("Xóa Ảnh")
        icon3 = QIcon()
        icon3.addFile(u":/16x16/icons/16x16/cil-remove.png", QSize(), QIcon.Normal, QIcon.Off)
        self.delete_image_button.setIcon(icon3)
        self.delete_image_button.clicked.connect(self.delete_image)
        self.add_button_layout.addWidget(self.delete_image_button)
        # disable delete button
        if len(self.list_image) == 0:
            self.delete_image_button.setEnabled(False)
            self.delete_image_button.setStyleSheet(u"QPushButton {\n"
                "	border: 2px solid rgb(57, 65, 80);\n"
                "	border-radius: 5px;	\n"
                "	background-color: rgb(57, 65, 80);\n"
                "}\n")


        # Thêm grid_layout và QScrollArea vào main_layout
        self.control_layout.addLayout(self.grid_layout)
        self.control_layout.addLayout(self.add_button_layout)
        self.main_layout.addLayout( self.control_layout)
        self.main_layout.addWidget(self.scroll_area)

    def delete_image(self):
        for key in self.list_camera_screen.keys():
            self.grid_layout.removeWidget(self.list_camera_screen[key])
            self.list_camera_screen[key].deleteLater()

        torch.cuda.empty_cache()

        self.list_camera_screen = {}
        self.list_image = []  

    def init_camera(self):
        if len(self.list_image) >4 :
            num_col = 3
        elif len(self.list_image) == 1:
            num_col = 1
        else:
            num_col = 2
        self.thread_pool.setMaxThreadCount(len(self.list_image))
        for i,path in enumerate(self.list_image):
            if path not in self.list_camera_screen.keys():
                image = cv2.imread(path)
                frame = image.copy()
                output_frame = self.analyze_frame(frame)

                frame = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

                pixmap = QPixmap.fromImage(q_image)
                self.image_label_1 = QLabel()
                self.image_label_1.setPixmap(QPixmap(pixmap))
                self.image_label_1.setScaledContents(True)
                self.grid_layout.addWidget(self.image_label_1, i // num_col, i % num_col, 1, 1)
                self.list_camera_screen[path] = self.image_label_1

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
    def calculate_iou(self,box1, box2):
          try:
              x1, y1, w1, h1 = box1[0], box1[1], box1[2]-box1[0], box1[3]-box1[1]
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
    
    def analyze_frame(self, frame):
        result_predict = self.predictor.analyze_predict_frame(frame)
        list_recognition_insightface = self.face_analyzer.analyze_insightface_frame(frame)
        list_recognition_insightface_merge = self.get_matched_pairs(result_predict, list_recognition_insightface)

        image = frame.copy()
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
            face_image = None
            
            label = ""

            label_name = None
            label_mask = None

            guid = None
            age = None
            gender = None
            main_color_clothes = None

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
                box_face_plot = [box_face[0], box_face[1], box_face[2], box_face[3]]
                
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
            
            if d is not None and len(d) > 0:
                box_person = d[0][0:4]
                main_color_clothes = d[1]
                name_color = d[2]
                if main_color_clothes is not None:
                    color_person = main_color_clothes
                    color_text = (255, 255, 255)
                annotator.box_label(box_person, label, color=color_person,txt_color=color_text)
                annotator_save.box_label(box_person, "", color=color_person,txt_color=color_text)

        return annotator.result()


    def resizeEvent(self, event):
        # Override the resizeEvent to handle window resize
        self.new_size = event.size()
        self.scroll_area.setFixedSize(int(self.new_size.width()/10* 2), self.new_size.height())
        self.add_image_button.setFixedSize(int(self.new_size.width()/10* 2), 50)
        self.delete_image_button.setFixedSize(int(self.new_size.width()/10* 2), 50)
        for key in self.list_camera_screen.keys():
            self.list_camera_screen[key].setScaledContents(True)
        # Call the base class implementation
        super().resizeEvent(event)

    def show_dialog_image(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Image files (*.jpeg *.jpg *.png)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setViewMode(QFileDialog.Detail)

        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()
            if file_path:
                print("Selected file:", file_path[0])
                self.list_image.append(file_path[0])
                if len(self.list_image) > 0:
                        self.delete_image_button.setEnabled(True)
                        self.delete_image_button.setStyleSheet(u"QPushButton {\n"
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
                self.init_camera()
       

            