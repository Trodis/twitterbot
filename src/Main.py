from app.Application import Application

CONSUMER_KEY        =
CONSUMER_SECRET     =
REQUEST_TOKEN_URL   =
ACCESS_TOKEN_URL    =
AUTHORIZE_URL       =

if __name__ == "__main__":
    app = Application(CONSUMER_KEY,CONSUMER_SECRET, 
            REQUEST_TOKEN_URL, ACCESS_TOKEN_URL, AUTHORIZE_URL)
    app.run()
