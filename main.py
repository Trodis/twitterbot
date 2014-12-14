from PyQt4 import QtGui
from gui import *
import sys
from bot_core import *
import pymongo

CONSUMER_KEY        = "oFnKOZ1a4BJMOMjCkJbb7rv2i"
CONSUMER_SECRET     = "8V6V7w26vy0kUl99vNmZg3Fod8RLl1nLuxslDhh0T0BwhxN6mD"
REQUEST_TOKEN_URL   = "https://api.twitter.com/oauth/request_token"
ACCESS_TOKEN_URL    = "https://api.twitter.com/oauth/access_token"
AUTHORIZE_URL       = "https://api.twitter.com/oauth/authorize"

db_client = pymongo.MongoClient('mongodb://trodis:Lgeji8tf@ds057000.mongolab.com:57000/furkantweet')

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    form = Ui_MainWindow()
    form.show()
    sys.exit(app.exec_())
