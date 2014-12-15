# -*- coding: utf-8 -*-
# coding: utf8
import random
import sys
import os
import string
import time
import pymongo
import md5

import urlparse
import oauth2 as oauth
from twython import Twython, TwythonError, TwythonRateLimitError

class AppController():

    def __init__(db_client, CONSUMER_KEY, CONSUMER_SECRET, REQUEST_TOKEN_URL, 
            ACCESS_TOKEN_URL, AUTHORIZE_URL):
        self.db_client = db_client
        self.CONSUMER_KEY = CONSUMER_KEY
        self.CONSUMER_SECRET = CONSUMER_SECRET
        self.REQUEST_TOKEN_URL = REQUEST_TOKEN_URL
        self.ACCESS_TOKEN_URL = ACCESS_TOKEN_URL
        self.AUTHORIZE_URL = AUTHORIZE_URL

    def main(self, listView):
        db = self.db_client.furkantweet
        listView.append("Hallo Welt")
        collection_names = db.collection_names()
        tweet_collection = db.generaltweets
        twitter_instance = self.getTwitterInstance(db, collection_names)
        self.fireBot(listView, twitter_instance, tweet_collection)

    def fireBot(listView, twitter, tweet_collection):
        print "\n"
        print "********************************************"
        print "Token wurden gefunden! Elhamdulillah!"
        print "Der Bot kann jetzt gestartet werden!"
        print "********************************************"
        start_bot = raw_input('::Bot starten [y/n]?: ')
        if start_bot == 'y':
            hashtag = raw_input('::Hashtag bitte eingeben: ').decode(sys.stdin.encoding)
        else:
            print "Bot wird beendet! Khair Insallah..."
            sys.exit()
        tweet_counter = 1
        tweet_cursor = tweet_collection.find()
        while True:
            try:
                successful_tweets = 0
                failed_tweets = 0
                print "\n==> Für folgende Benutzer wird getweeted:"
                for user in twitter:
                    print " %s" %getAccountName(user)
                print "\n"
                tweet_cursor = shuffleCursor(tweet_cursor)
                for counter, tweet in enumerate(tweet_cursor):
                    listView.append("::Tweet Nr.%i senden...\n '%s'") %(counter+1, tweet['tweet'])
                    text = "%s %s" %(tweet['tweet'], hashtag)
                    success = sendTweet(twitter, text)
                    if success:
                        successful_tweets += 1
                    else:
                        failed_tweets += 1
                        #status = user.get_application_rate_limit_status(resources=['statuses'])
                        #left = status['resources']['statuses']['/statuses/update']['remaining']
                    print "::Kurze Pause..."
                    print " ==> Tweets Insgesamt: %i\n  Erfolgreich: %i\n  Gescheitert: %i" %(counter+1,
                            successful_tweets, failed_tweets)
                    startSleep(random.uniform(5, 20))
                    if counter == 100:
                        print "50 Tweets erreicht lange Pause für ca. 5 min"
                        startSleep(random.randint(120, 190))
            except TwythonError as e:
                print e
                sys.exit()

    def getTwitterInstance(db, collection_names):
        user_collection_exists = True
        user_not_verified = True
        while user_not_verified:
            print "::Am System anmelden"
            username = "twitteruser" 
            if checkUsername(username, collection_names):
                user_collection = db[username]
                print " Benutzer wurde in der Datenbank gefunden!"
                password = "qwertz123!"
                print " Passwort wird geprüft..."
                user_password_from_db = user_collection.find_one({"passwort":password})
                if user_password_from_db:
                    print " Passwort Korrekt!"
                    user_not_verified = False
                else:
                    print " Passwort falsch!"
            else:
                print "::Neuen Benutzer anlegen"
                print " Der Benutzer existiert nicht in der Datenbank," 
                print " der Benutzer muss mit Passwort erst angelegt werden!...\n"
                password = raw_input(" Passwort für diesen Benutzer?: ")
                password2 = raw_input(" Paswort nocheinmal eingeben: ")
                if password == password2:
                    user_collection = db[username]
                    user_collection.insert({"passwort":password})
                    print " Neuer Benutzer wurde angelegt!"
                    user_not_verified = False
                else:
                    print "Passwörter stimmen nicht überein!"
                    continue
            
        user_collection = db[username]
        option = "y"
        while option != "q":
            print "\n"
            print "****Wähle eines der folgenden Optionen****"
            print " [S]Bot starten [H]Account hinzufügen"
            print "******************************************"
            option = raw_input("::Option eingeben [S/H]: ")
            if option == "S":
                tokens = getOAuthToken(user_collection)
                if tokens is not None:
                    twitter = []
                    for token in tokens:
                        if "passwort" not in token:
                            twitter.append(Twython(CONSUMER_KEY, CONSUMER_SECRET,
                                token['oauth_token'], token['oauth_token_secret'] ))
                    return twitter
                else:
                    continue
            elif option == "H":
                refire = True
                while refire:
                    addUserWithToken(raw_input("Twitter Benutzername: "), user_collection)
                    if raw_input("\n::Weiteren hinzufügen?[y/n]:") == "y":
                        refire = True
                    else:
                        refire = False
            else:
                print "Nur S oder H"
        
        sys.exit()

    def shuffleCursor(tweet_cursor):
        for i in range(random.randint(100, 1000)):
            tweet_cursor.next()
        return tweet_cursor

    def sendTweet(twitter, text):
        for user in twitter:
            try:
                user.update_status(status=text)
                time.sleep(2)
            except TwythonError as e:
                print "\n::Fehler beim Senden!\n Status Code: %s" %user._last_call["status_code"]
                print " Betroffener Account: %s" %getAccountName(user)
                print " Tweet Nachricht wird übersprungen...\n"
                return False
        print "\n::Tweet mit allen Accounts gesendet!"

        return True

    def checkUsername(username, collection_names):
        if username in collection_names:
            return True
        else:
            return False


    def getAccountName(twitter):
        try:
            return twitter.verify_credentials()['name']
        except TwythonRateLimitError, e:
            print "\n::Fehler"
            print " Limit Erreicht!"
            print " %s" %e
            print " Schlafen für 15min!"
            startSleep(60*15)
            return

    def startSleep(seconds):
        while seconds > 0:
            print "\r Countdown: %i Sek." %seconds,
            sys.stdout.flush()
            seconds -= 1
            time.sleep(1)
        print "\n"

    def getRequestToken():
        consumer = oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
        client = oauth.Client(consumer)
        response, content = client.request(REQUEST_TOKEN_URL, "GET")
        if response['status'] != '200':
            return None
            raise Exception("Invalid response %s" %response['status'])
        else:
            request_token = dict(urlparse.parse_qsl(content))
            oauth_verifier = getPinFromUser(request_token)
            token = oauth.Token(request_token['oauth_token'],
                request_token['oauth_token_secret'])
            token.set_verifier(oauth_verifier)
            client = oauth.Client(consumer, token)
            response, content = client.request(ACCESS_TOKEN_URL, "POST")
            access_token = dict(urlparse.parse_qsl(content))
            return access_token

    def addUserWithToken(username, user_collection):
        access_token = getRequestToken()
        saveOAuthToken(access_token, username, user_collection)

    def getOAuthToken(user_collection):
        if user_collection.count() > 1:
            return user_collection.find()
        else:
            print "==> Fehler!"
            print " Die Datenbank hat noch keine Twitter Account"
            print " Es muss erst ein Twitter Account hinzugefügt werden"
            return None

    def getPinFromUser(request_token):
        print "*************Du musst diese Anwednung verifizieren*********************"
        print "    Kopiere dazu den unten aufgeführten Link einfach in deinen Browser"
        print "    Autorisiere die App und geb die PIN unten ein"
        print "***********************************************************************"
        print "::Zu kopierender Link\n %s?oauth_token=%s" %(AUTHORIZE_URL,
            request_token['oauth_token'])

        is_not_digit = True
        while is_not_digit: 
            oauth_verifier = raw_input(' Den PIN hier eingeben!: ')
            if oauth_verifier.isdigit():
                print " OK! PIN wird geprüft..."
                is_not_digit = False
            else:
                print "Die PIN kann nur aus Zahlen bestehen, versuchs nocheinmal!"

        return oauth_verifier
        
    def saveOAuthToken(access_token, username, user_collection):
        print "::Benutzer wird gespeichert..."
        try:
            if user_collection.find_one({"username": username}) is None:
                user_collection.insert({"username":username, "oauth_token": access_token['oauth_token'],
                    "oauth_token_secret": access_token['oauth_token_secret']})
                print " Benutzer %s wurde gespeichert!" %username
            else:
                print " Der Benutzer %s existiert bereits in der Datenbank!" %username
        except Exception as e:
            print "==> Fehler!"
            print " Speichern war nicht möglich!"
            print e
