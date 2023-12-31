################################################################################
##
## BY: WANDERSON M.PIMENTA
## PROJECT MADE WITH: Qt Designer and PySide2
## V: 1.0.0
##
## This project can be used freely for all uses, as long as they maintain the
## respective credits only in the Python scripts, any information in the visual
## interface (GUI) can be modified without any implication.
##
## There are limitations on Qt licenses if you want to use your products
## commercially, I recommend reading them on the official website:
## https://doc.qt.io/qtforpython/licenses.html
##
################################################################################

import sys
import platform
from datetime import datetime
import time
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import (QCoreApplication, QPropertyAnimation, QDate, QDateTime, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt, QEvent)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,QKeyEvent, QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter, QPixmap, QRadialGradient)
from PySide2.QtWidgets import *
from ui_Formlogin import Login
# GUI FILE
from app_modules import *
from check_user import verify_authorization, verify_login
from server import create_db

class LoginWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Login()
        self.ui.setupUi(self)

        # REMOVE TITLE BAR
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # CREATE DROP SHADOW EFFECT
        self.shadow = self.set_drop_shadow()

        # SET DROP SHADOW EFFECT IN FRAME
        self.ui.frame_Shadow.setGraphicsEffect(self.shadow)

        # SET FUNCTION CLICK IN BUTTONS
        self.ui.pushButton_Exit.clicked.connect(self.click_exit)
        self.ui.pushButton_Login.clicked.connect(self.click_login)

        # ENABLE MODE PASSWORD IN LINE EDIT
        self.ui.lineEdit_Password.setEchoMode(QLineEdit.Password)

        # SET MOVE WINDOW
        def move_window(event):
            # IF LEFT CLICK MOVE WINDOW
            if event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.globalPos() - self.drag_pos)
                self.drag_pos = event.globalPos()
                event.accept()

        # ENABLE MOUSE MOVE FORM
        self.ui.frame_TopBar.mouseMoveEvent = move_window
        self.ui.frame_Shadow.mouseMoveEvent = move_window
        
        # SHOW FORM
        self.show()
        
    def set_drop_shadow(self):
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        return self.shadow

    def click_exit(self):
        print("click button close")
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.click_login()
    def click_login(self):
        print("click button login")
        user = self.ui.lineEdit_Login.text()
        password = self.ui.lineEdit_Password.text()
        response = verify_login(user, password)
        verify = response['verify_status']
        message = response['message']
        target_date = datetime(2024, 1, 13, 0, 0, 0)
        target_timestamp = target_date.timestamp()
        current_timestamp = time.time()
        if current_timestamp < target_timestamp:
            if verify is True:
            # Hide login
                self.close()
                window = MainWindow()
                window.show()
            else:
                QMessageBox.warning(self, "Lỗi đăng nhập", f"{message}", QMessageBox.Ok)
        else: 
            QMessageBox.warning(self, "Hết hạn đăng nhập", "Vui lòng liên hệ AIPT AI để được hỗ trợ!", QMessageBox.Ok)
        

    def mousePressEvent(self, event):
        self.drag_pos = event.globalPos()

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        print('System: ' + platform.system())
        print('Version: ' +platform.release())

        ## REMOVE ==> STANDARD TITLE BAR
        UIFunctions.removeTitleBar(True)
        ## ==> END ##

        UIFunctions.userIcon(self, "WM", r"icons\img\logoweb-1024x1024.png", True)

        ## SET ==> WINDOW TITLE
        self.setWindowTitle('HumanMaster')
        UIFunctions.labelTitle(self, 'HumanMaster')
        UIFunctions.labelDescription(self, 'AIPT GROUP')
        ## ==> END ##

        ## WINDOW SIZE ==> DEFAULT SIZE
        startSize = QSize(1280, 720)
        self.resize(startSize)
        self.setMinimumSize(startSize)
        ## ==> END ##

        ## ==> TOGGLE MENU SIZE
        self.ui.btn_toggle_menu.clicked.connect(lambda: UIFunctions.toggleMenu(self, 220, True))
        ## ==> END ##

        ## ==> ADD CUSTOM MENUS
        self.ui.stackedWidget.setMinimumWidth(30)
        UIFunctions.addNewMenu(self, "CAMERA", "btn_camera", "url(:/16x16/icons/16x16/cil-camera.png)", True)
        # UIFunctions.addNewMenu(self, "VIDEO", "btn_video", "url(:/16x16/icons/16x16/cil-movie.png)", True)
        UIFunctions.addNewMenu(self, "ẢNH", "btn_image", "url(:/16x16/icons/16x16/cil-image1.png)", True)
        UIFunctions.addNewMenu(self, "XÁC MINH", "btn_similarity", "url(:/16x16/icons/16x16/cil-people.png)", True)
        UIFunctions.addNewMenu(self, "ĐỐI TƯỢNG", "btn_new_user", "url(:/16x16/icons/16x16/cil-user-follow.png)", True)
        UIFunctions.addNewMenu(self, "TELEGRAM", "btn_telegram", "url(:/16x16/icons/16x16/cil-chart-pie.png)", True)
        UIFunctions.addNewMenu(self, "BÁO CÁO", "btn_report", "url(:/16x16/icons/16x16/cil-equalizer.png)", False)
        ## ==> END ##

        # START MENU => SELECTION
        UIFunctions.selectStandardMenu(self, "btn_camera")
        ## ==> END ##

        ## ==> START PAGE
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_camera)
        ## ==> END ##

        ## USER ICON ==> SHOW HIDE
        UIFunctions.userIcon(self, "AIPT", "", True)
        ## ==> END ##


        ## ==> MOVE WINDOW / MAXIMIZE / RESTORE
        ########################################################################
        def moveWindow(event):
            # IF MAXIMIZED CHANGE TO NORMAL
            if UIFunctions.returStatus() == 1:
                UIFunctions.maximize_restore(self)

            # MOVE WINDOW
            if event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.globalPos() - self.dragPos)
                self.dragPos = event.globalPos()
                event.accept()

        # WIDGET TO MOVE
        self.ui.frame_label_top_btns.mouseMoveEvent = moveWindow
        ## ==> END ##

        ## ==> LOAD DEFINITIONS
        ########################################################################
        UIFunctions.uiDefinitions(self)
        ## ==> END ##

        ########################################################################
        ## END - WINDOW ATTRIBUTES
        ############################## ---/--/--- ##############################




        ########################################################################
        #                                                                      #
        ## START -------------- WIDGETS FUNCTIONS/PARAMETERS ---------------- ##
        #                                                                      #
        ## ==> USER CODES BELLOW                                              ##
        ########################################################################



        ## ==> QTableWidget RARAMETERS
        ########################################################################
        # self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        ## ==> END ##



        ########################################################################
        #                                                                      #
        ## END --------------- WIDGETS FUNCTIONS/PARAMETERS ----------------- ##
        #                                                                      #
        ############################## ---/--/--- ##############################


        ## SHOW ==> MAIN WINDOW
        ########################################################################
        self.show()
        ## ==> END ##

    ########################################################################
    ## MENUS ==> DYNAMIC MENUS FUNCTIONS
    ########################################################################
    def Button(self):
        # GET BT CLICKED
        btnWidget = self.sender()

        # PAGE HOME
        if btnWidget.objectName() == "btn_camera":
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_camera)
            UIFunctions.resetStyle(self, "btn_camera")
            UIFunctions.labelPage(self, "camera")
            btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

        # if btnWidget.objectName() == "btn_video":
        #     self.ui.stackedWidget.setCurrentWidget(self.ui.page_video)
        #     UIFunctions.resetStyle(self, "btn_video")
        #     UIFunctions.labelPage(self, "video")
        #     btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

        if btnWidget.objectName() == "btn_image":
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_image)
            UIFunctions.resetStyle(self, "btn_image")
            UIFunctions.labelPage(self, "ẢNH")
            btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

        if btnWidget.objectName() == "btn_similarity":
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_similarity)
            UIFunctions.resetStyle(self, "btn_similarity")
            UIFunctions.labelPage(self, "XÁC MINH")
            btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

        # PAGE NEW USER
        if btnWidget.objectName() == "btn_new_user":
            self.ui.stackedWidget.setCurrentWidget(self.ui.add_user)
            UIFunctions.resetStyle(self, "btn_new_user")
            UIFunctions.labelPage(self, "ĐỐI TƯỢNG")
            btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))
  
        # PAGE WIDGETS
        if btnWidget.objectName() == "btn_report":
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_widgets)
            UIFunctions.resetStyle(self, "btn_report")
            UIFunctions.labelPage(self, "BÁO CÁO")
            btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

        if btnWidget.objectName() == "btn_telegram":
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_telegram)
            UIFunctions.resetStyle(self, "btn_telegram")
            UIFunctions.labelPage(self, "TELEGRAM")
            btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

    ## ==> END ##

    ########################################################################
    ## START ==> APP EVENTS
    ########################################################################

    ## EVENT ==> MOUSE DOUBLE CLICK
    ########################################################################
    def eventFilter(self, watched, event):
        if watched == self.le and event.type() == QtCore.QEvent.MouseButtonDblClick:
            print("pos: ", event.pos())
    ## ==> END ##

    ## EVENT ==> MOUSE CLICK
    ########################################################################
    def mousePressEvent(self, event):
        self.dragPos = event.globalPos()
        if event.buttons() == Qt.LeftButton:
            print('Mouse click: LEFT CLICK')
        if event.buttons() == Qt.RightButton:
            print('Mouse click: RIGHT CLICK')
        if event.buttons() == Qt.MidButton:
            print('Mouse click: MIDDLE BUTTON')
    ## ==> END ##

    ## EVENT ==> KEY PRESSED
    ########################################################################
    def keyPressEvent(self, event):
        print('Key: ' + str(event.key()) + ' | Text Press: ' + str(event.text()))
    ## ==> END ##

    ## EVENT ==> RESIZE EVENT
    ########################################################################
    def resizeEvent(self, event):
        self.resizeFunction()
        
        return super(MainWindow, self).resizeEvent(event)

    def resizeFunction(self):
        print('Height: ' + str(self.height()) + ' | Width: ' + str(self.width()))
    ## ==> END ##

    ########################################################################
    ## END ==> APP EVENTS
    ############################## ---/--/--- ##############################
    def closeEvent(self, event):
        QCoreApplication.quit()  # Tắt ứng dụng
        event.accept()


def init_app():
    app = QApplication(sys.argv)
    QtGui.QFontDatabase.addApplicationFont('fonts/segoeui.ttf')
    QtGui.QFontDatabase.addApplicationFont('fonts/segoeuib.ttf')
    create_db()
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    init_app()
    