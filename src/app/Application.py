# -*- coding: utf-8 -*-  
import sys
from PyQt4.QtGui import QMainWindow, QApplication, QMessageBox
from controller.AppController import AppController
from view.MainWindow import Ui_MainWindow
from PyQt4.QtCore import *


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
        self.ui_MainWindow.actionQuit.triggered.connect(
                self.closeEvent)
        # Main Tab in GUI
        self.ui_MainWindow.start_btn.clicked.connect(
                self.appctl.runBot)
        
        self.ui_MainWindow.stop_btn.clicked.connect(
                self.appctl.stopBot)

        self.ui_MainWindow.addtwitteraccount_btn.clicked.connect(
                self.appctl.startAuthentication)

        self.ui_MainWindow.verifypin_btn.clicked.connect(
                self.appctl.verifyPin)
       
        self.ui_MainWindow.savedatabase_btn.clicked.connect(
                self.appctl.setiniDatabase)
        
        self.ui_MainWindow.openfile_btn.clicked.connect(
                self.appctl.setTextFilePath)

        self.ui_MainWindow.savesource_btn.clicked.connect(
                self.appctl.setiniSource)

        self.ui_MainWindow.savetiming_btn.clicked.connect(
                self.appctl.setiniTiming)

        #Twitter Account ListWidget
        self.ui_MainWindow.remove_btn.clicked.connect(
                self.appctl.deleteAccount)

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

    def closeEvent(self, event):
        result = QMessageBox.question(None, "Confirm Exit...",
                "Are you sure you want to exit ?", 
                QMessageBox.Yes, QMessageBox.No)
        
        if result == QMessageBox.Yes:
            QApplication.quit()
