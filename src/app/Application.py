# -*- coding: utf-8 -*-  
import sys

from PyQt4.QtGui import QMainWindow, QApplication
from controller.AppController import AppController
from view.MainWindow import Ui_MainWindow

class Application(object):

    def __init__(self):
        pass

    def setupModels(self):
        pass

    def setupSlot(self):
        pass

    def setupCtl(self):
        #self.appctl = AppController(self)
        pass

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
