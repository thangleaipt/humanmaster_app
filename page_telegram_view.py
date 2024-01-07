
from PySide2.QtCore import (QCoreApplication, QMetaObject, QObject, QPoint,
    QRect, QSize, QUrl, Qt, QDateTime, QTime)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QLinearGradient, QPalette, QPainter,QPixmap,QImage,
    QRadialGradient, QDesktopServices)

from PySide2.QtWidgets import *
import requests
from server.telegrams.services import delete_telegram_service, get_list_telegrams_db, create_telegram, update_status_telegram_service
from server.config import API_TELEGRAM


column_ratios = [0.1, 0.15, 0.25, 0.25, 0.25]

class PAGETELEGRAM(QWidget):
        def __init__(self, page_camera):
                super().__init__()
                self.analyzer = None
                self.list_telegrams = []
                self.page_camera = page_camera
                self.setObjectName(u"page_telegram")
                self.set_ui()
                self.retranslateUi()

        def set_ui(self):
                self.verticalLayout_6 = QVBoxLayout(self)
                self.verticalLayout_6.setObjectName(u"verticalLayout_6")

                # Create a group box for the filter controls
                self.filter_groupbox = QGroupBox("Lọc dữ liệu", self)
                self.filter_groupbox.setObjectName(u"filter_groupbox")

                # Create a layout for the filter group box
                self.filter_layout = QHBoxLayout(self.filter_groupbox)
                self.filter_layout.setObjectName(u"filter_layout")
                # Buton Search
                self.connect_button = QPushButton("Kết nối Telegram", self.filter_groupbox)
                self.connect_button.setObjectName(u"search_button")
                self.connect_button.setFixedSize(100, 50)
                self.filter_layout.addWidget(self.connect_button)
                self.connect_button.setStyleSheet(u"QPushButton {\n"
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
                icon3.addFile(u":/16x16/icons/16x16/cil-magnifying-glass.png", QSize(), QIcon.Normal, QIcon.Off)
                self.connect_button.setIcon(icon3)
                self.connect_button.clicked.connect(self.add_telegram)

                self.add_button = QPushButton("Thêm Telegram", self.filter_groupbox)
                self.add_button.setObjectName(u"add_button")
                self.add_button.setFixedSize(100, 50)
                self.filter_layout.addWidget(self.add_button)
                self.add_button.setStyleSheet(u"QPushButton {\n"
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
                icon3.addFile(u":/16x16/icons/16x16/cil-magnifying-glass.png", QSize(), QIcon.Normal, QIcon.Off)
                self.add_button.setIcon(icon3)
                self.add_button.clicked.connect(self.get_user_info)

                # Add the filter group box to the main layout
                self.verticalLayout_6.addWidget(self.filter_groupbox)


                self.frame_3 = QFrame(self)
                self.frame_3.setObjectName(u"frame_3")
                self.frame_3.setMinimumSize(QSize(0, 150))
                self.frame_3.setFrameShape(QFrame.StyledPanel)
                self.frame_3.setFrameShadow(QFrame.Raised)
                self.horizontalLayout_12 = QHBoxLayout(self.frame_3)
                self.horizontalLayout_12.setSpacing(0)
                self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
                self.horizontalLayout_12.setContentsMargins(0, 0, 0, 0)
                self.tableWidget = QTableWidget(self.frame_3)
                if (self.tableWidget.columnCount() < 5):
                        self.tableWidget.setColumnCount(5)
                        __qtablewidgetitem = QTableWidgetItem()
                        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
                        __qtablewidgetitem1 = QTableWidgetItem()
                        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
                        __qtablewidgetitem2 = QTableWidgetItem()
                        self.tableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
                        __qtablewidgetitem3 = QTableWidgetItem()
                        self.tableWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
                        __qtablewidgetitem4 = QTableWidgetItem()
                        self.tableWidget.setHorizontalHeaderItem(4, __qtablewidgetitem4)
                if (self.tableWidget.rowCount() < 10):
                        self.tableWidget.setRowCount(10)
                        font2 = QFont()
                        font2.setFamily(u"Segoe UI")
                        self.tableWidget.setObjectName(u"tableWidget")
                        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                        sizePolicy.setHorizontalStretch(0)
                        sizePolicy.setVerticalStretch(0)
                        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
                        self.tableWidget.setSizePolicy(sizePolicy)
                        palette1 = QPalette()
                        brush6 = QBrush(QColor(210, 210, 210, 255))
                        brush6.setStyle(Qt.SolidPattern)
                        palette1.setBrush(QPalette.Active, QPalette.WindowText, brush6)
                        brush15 = QBrush(QColor(39, 44, 54, 255))
                        brush15.setStyle(Qt.SolidPattern)
                        palette1.setBrush(QPalette.Active, QPalette.Button, brush15)
                        palette1.setBrush(QPalette.Active, QPalette.Text, brush6)
                        palette1.setBrush(QPalette.Active, QPalette.ButtonText, brush6)
                        palette1.setBrush(QPalette.Active, QPalette.Base, brush15)
                        palette1.setBrush(QPalette.Active, QPalette.Window, brush15)
                        brush16 = QBrush(QColor(210, 210, 210, 128))
                        brush16.setStyle(Qt.NoBrush)
                #if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
                        palette1.setBrush(QPalette.Active, QPalette.PlaceholderText, brush16)
                #endif
                        palette1.setBrush(QPalette.Inactive, QPalette.WindowText, brush6)
                        palette1.setBrush(QPalette.Inactive, QPalette.Button, brush15)
                        palette1.setBrush(QPalette.Inactive, QPalette.Text, brush6)
                        palette1.setBrush(QPalette.Inactive, QPalette.ButtonText, brush6)
                        palette1.setBrush(QPalette.Inactive, QPalette.Base, brush15)
                        palette1.setBrush(QPalette.Inactive, QPalette.Window, brush15)
                        brush17 = QBrush(QColor(210, 210, 210, 128))
                        brush17.setStyle(Qt.NoBrush)
                #if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
                        palette1.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush17)
                #endif
                        palette1.setBrush(QPalette.Disabled, QPalette.WindowText, brush6)
                        palette1.setBrush(QPalette.Disabled, QPalette.Button, brush15)
                        palette1.setBrush(QPalette.Disabled, QPalette.Text, brush6)
                        palette1.setBrush(QPalette.Disabled, QPalette.ButtonText, brush6)
                        palette1.setBrush(QPalette.Disabled, QPalette.Base, brush15)
                        palette1.setBrush(QPalette.Disabled, QPalette.Window, brush15)
                        brush18 = QBrush(QColor(210, 210, 210, 128))
                        brush18.setStyle(Qt.NoBrush)
                #if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
                        palette1.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush18)
                #endif
                        self.tableWidget.setPalette(palette1)
                        self.tableWidget.setStyleSheet(u"QTableWidget {	\n"
                "	background-color: rgb(39, 44, 54);\n"
                "	padding: 10px;\n"
                "	border-radius: 5px;\n"
                "	gridline-color: rgb(44, 49, 60);\n"
                "	border-bottom: 1px solid rgb(44, 49, 60);\n"
                "}\n"
                "QTableWidget::item{\n"
                "	border-color: rgb(44, 49, 60);\n"
                "	padding-left: 5px;\n"
                "	padding-right: 5px;\n"
                "	gridline-color: rgb(44, 49, 60);\n"
                "}\n"
                "QTableWidget::item:selected{\n"
                "	background-color: rgb(85, 170, 255);\n"
                "}\n"
                "QScrollBar:horizontal {\n"
                "    border: none;\n"
                "    background: rgb(52, 59, 72);\n"
                "    height: 15px;\n"
                "    margin: 0px 21px 0 21px;\n"
                "	border-radius: 0px;\n"
                "}\n"
                " QScrollBar:vertical {\n"
                "	border: none;\n"
                "    background: rgb(52, 59, 72);\n"
                "    width: 14px;\n"
                "    margin: 21px 0 21px 0;\n"
                "	border-radius: 0px;\n"
                " }\n"
                "QHeaderView::section{\n"
                "	Background-color: rgb(39, 44, 54);\n"
                "	max-width: 30px;\n"
                "	border: 1px solid rgb(44, 49, 60);\n"
                "	border-style: none;\n"
                "    border-bottom: 1px solid rgb(44, 49, 60);\n"
                "    border-right: 1px solid rgb(44, 49, 60);\n"
                "}\n"
                ""
                                        "QTableWidget::horizontalHeader {	\n"
                "	background-color: rgb(81, 255, 0);\n"
                "}\n"
                "QHeaderView::section:horizontal\n"
                "{\n"
                "    border: 1px solid rgb(32, 34, 42);\n"
                "	background-color: rgb(27, 29, 35);\n"
                "	padding: 3px;\n"
                "	border-top-left-radius: 7px;\n"
                "    border-top-right-radius: 7px;\n"
                "}\n"
                "QHeaderView::section:vertical\n"
                "{\n"
                "    border: 1px solid rgb(44, 49, 60);\n"
                "}\n"
                "")
                        self.tableWidget.setFrameShape(QFrame.NoFrame)
                        self.tableWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
                        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
                        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
                        self.tableWidget.setAlternatingRowColors(False)
                        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
                        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
                        self.tableWidget.setShowGrid(True)
                        self.tableWidget.setGridStyle(Qt.SolidLine)
                        self.tableWidget.setSortingEnabled(False)
                        self.tableWidget.horizontalHeader().setVisible(True)
                        self.tableWidget.horizontalHeader().setCascadingSectionResizes(True)
                        self.tableWidget.horizontalHeader().setDefaultSectionSize(200)
                        self.tableWidget.horizontalHeader().setStretchLastSection(True)
                        self.tableWidget.verticalHeader().setVisible(False)
                        self.tableWidget.verticalHeader().setCascadingSectionResizes(False)
                        self.tableWidget.verticalHeader().setHighlightSections(False)
                        self.tableWidget.verticalHeader().setStretchLastSection(True)
                        self.horizontalLayout_12.addWidget(self.tableWidget)
                        self.verticalLayout_6.addWidget(self.frame_3)
                       

        def retranslateUi(self):
                        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
                        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"STT", None));
                        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
                        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Chat ID", None));
                        ___qtablewidgetitem2 = self.tableWidget.horizontalHeaderItem(2)
                        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Họ và tên", None));
                        ___qtablewidgetitem3 = self.tableWidget.horizontalHeaderItem(3)
                        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"Trạng thái", None));
                        ___qtablewidgetitem4 = self.tableWidget.horizontalHeaderItem(4)
                        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Thao tác", None));
                        self.get_list_telegram()

        def get_list_telegram(self):
                self.tableWidget.clearContents()
                self.list_telegrams = get_list_telegrams_db()
                self.page_camera.telegrams = self.list_telegrams
                if len(self.list_telegrams) >= 10:
                        self.tableWidget.setRowCount(len(self.list_telegrams))

                for i, telegram in enumerate(self.list_telegrams):
                        self.tableWidget.setItem(i, 0, QTableWidgetItem(str(i)))
                        self.tableWidget.setItem(i, 1, QTableWidgetItem(str(telegram.chat_id)))
                        self.tableWidget.setItem(i, 2, QTableWidgetItem(str(telegram.name)))
                        self.tableWidget.setItem(i, 3, QTableWidgetItem(str(telegram.status)))

                        # Creating the layout and buttons
                        layout = QHBoxLayout()

                        # Xóa button
                        delete_button = QPushButton('Xóa')
                        delete_button.setStyleSheet(u"QPushButton {\n"
                                "	border: 2px solid rgb(57, 65, 80);\n"
                                "	border-radius: 5px;	\n"
                                "	background-color: rgb(57, 65, 80);\n"
                                "}\n")
                        delete_button.setFixedHeight(25)
                        delete_button.clicked.connect(lambda row=i: self.delete_row(row))  # Connect the button to a delete_row function
                        layout.addWidget(delete_button)

                        # Thay đổi trạng thái button
                        change_status_button = QPushButton('Thay đổi trạng thái')
                        change_status_button.setStyleSheet(u"QPushButton {\n"
                                "	border: 2px solid rgb(57, 65, 80);\n"
                                "	border-radius: 5px;	\n"
                                "	background-color: rgb(57, 65, 80);\n"
                                "}\n")
                        change_status_button.setFixedHeight(25)
                        change_status_button.clicked.connect(lambda row=i: self.change_status(row))  # Connect the button to a change_status function
                        layout.addWidget(change_status_button)

                        # Creating a widget to hold the layout
                        container = QWidget()
                        container.setLayout(layout)

                        # Setting the widget as the item in the fourth column
                        self.tableWidget.setCellWidget(i, 4, container)
        def delete_row(self, row):
                delete_telegram_service(self.list_telegrams[row].chat_id)
                self.get_list_telegram()

        def change_status(self, row):
                update_status_telegram_service(self.list_telegrams[row].chat_id)
                self.get_list_telegram()

        def get_user_info(self):
                try:
                        # Make a request to the Telegram Bot API
                        response = requests.get(API_TELEGRAM)
                        response.raise_for_status()  # Raise an exception for HTTP errors
                        list_telegram_id = []
                        # Parse the JSON response
                        data = response.json()
                        latest_message = max(data['result'], key=lambda x: x['message']['date'])

                        # Extract user_id and name from the latest message
                        chat_id = latest_message['message']['from']['id']
                        name = latest_message['message']['from']['first_name']
                        create_telegram(chat_id, name)
                        self.get_list_telegram()

                except requests.exceptions.RequestException as e:
                        print(f"Error: {e}")
                        

        def add_telegram(self):
                url = QUrl("https://t.me/HumanmasterBot")
                QDesktopServices.openUrl(url)
          
        def resizeEvent(self,event):
                screen_width = event.size().width()
                column_widths = [int(ratio * screen_width) for ratio in column_ratios]
                for i in range(4):
                        self.tableWidget.setColumnWidth(i, column_widths[i])
                row_height = 50
                for row in range(self.tableWidget.rowCount()):
                        self.tableWidget.setRowHeight(row, row_height)
                super().resizeEvent(event)
