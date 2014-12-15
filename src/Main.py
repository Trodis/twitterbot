from app.Application import Application

CONSUMER_KEY        = "oFnKOZ1a4BJMOMjCkJbb7rv2i"
CONSUMER_SECRET     = "8V6V7w26vy0kUl99vNmZg3Fod8RLl1nLuxslDhh0T0BwhxN6mD"
REQUEST_TOKEN_URL   = "https://api.twitter.com/oauth/request_token"
ACCESS_TOKEN_URL    = "https://api.twitter.com/oauth/access_token"
AUTHORIZE_URL       = "https://api.twitter.com/oauth/authorize"

if __name__ == "__main__":
    app = Application(CONSUMER_KEY,CONSUMER_SECRET, 
            REQUEST_TOKEN_URL, ACCESS_TOKEN_URL, AUTHORIZE_URL)
    app.run()
