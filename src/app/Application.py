# -*- coding: utf-8 -*-  
import sys

from PyQt4.QtGui import QMainWindow, QApplication
from controller.AppController import AppController
from view.MainWindow import Ui_MainWindow


class Application(object):

    def __init__(self, ckey, csec, 
            rtokenurl, atokenurl, authurl):
        self.consumer_key = ckey
        self.consumer_secret = csec
        self.request_token_url = rtokenurl
        self.access_token_url = atokenurl
        self.authorize_url = authurl

    def setupModels(self):
        pass
        
    def setupSlot(self):
        self.ui_MainWindow.addtwitteraccount_btn.clicked.connect(
                self.appctl.startAuthentication)
        self.ui_MainWindow.verifypin_btn.clicked.connect(
                self.appctl.verifyPin)

    def setupCtl(self):
        self.appctl = AppController(self.consumer_key, self.consumer_secret,
                self.request_token_url, self.access_token_url,
                self.authorize_url, self.ui_MainWindow)

    def setupUi(self):
        self.mainWindow = QMainWindow()
        self.ui_MainWindow = Ui_MainWindow()
        self.ui_MainWindow.setupUi(self.mainWindow)
        self.mainWindow.show()

    def run(self):
        self.qtapp = QApplication(sys.argv)
        self.setupUi()
        self.setupModels()
        self.setupCtl()
        self.setupSlot()

        sys.exit(self.qtapp.exec_())
