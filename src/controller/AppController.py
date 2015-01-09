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
import configparser
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from twython import Twython, TwythonError, TwythonRateLimitError

class WorkThread(QThread):
    def __init__(self, function):
        QThread.__init__(self)
        self.function = function

    def run(self):
        self.function()
        return
        

class AppController():

    """
    This is the AppController class, this class has all the methods
    which are called if a button from the ui is pressed by the user.
    So the main Stuff is happening in this class
    
    Attributes:
        CONSUMER_KEY: Is the consumer key from Twitter, this has to be set by the 
        developer in the Main.py module
        CONSUMER_SECRET: Is the consumer secret key from Twitter, this has to be set by the
        developer in the Main.py module
        REQUEST_TOKEN_URL: Is the URL to start the authentication (see Twitter API)
        ACCESS_TOKEN_URL: Is the URL to get the access Token for a specific Twitter User
        AUTHORIZE_URL: Is the URL to authorize the User with the PIN (see Twitter API)
        twitter_account_ini_name: Is the name of the ini File which contains all the 
        authenticated Twitter User with related Tokens
    """
    def __init__(self, CONSUMER_KEY, CONSUMER_SECRET, REQUEST_TOKEN_URL, 
            ACCESS_TOKEN_URL, AUTHORIZE_URL, mainWindow):
        
        self.CONSUMER_KEY = CONSUMER_KEY
        self.CONSUMER_SECRET = CONSUMER_SECRET
        self.REQUEST_TOKEN_URL = REQUEST_TOKEN_URL
        self.ACCESS_TOKEN_URL = ACCESS_TOKEN_URL
        self.AUTHORIZE_URL = AUTHORIZE_URL

        self.mainWindow = mainWindow

        """
        Setting the Class Attributes with default settings
        This Attributes will be modified if the user changes the settings
        over the gui except the Section and Option Names 
        """
        # Names of the .ini Files
        self.twitter_account_ini_name = 'TwitterAccounts.ini'
        self.settings_ini_name = 'BotConfig.ini' 
        
        # BotConfig.ini Section Names
        self.bot_ini_mongo_section = 'Mongo'
        self.bot_ini_text_file_section = 'Text File'
        self.bot_ini_tweet_source_section = 'Tweet Source'
        self.bot_ini_timing_section = 'Timing'

        # BotConfig.ini Mongo Section options
        self.bot_ini_uri = 'uri'
        self.bot_ini_database = 'database'
        self.bot_ini_uri_value = ''
        self.bot_ini_database_value = ''

        # BotConfig.ini Text File options
        self.bot_ini_path = 'path'
        self.bot_ini_path_value = ''

        # BotConfig.ini Tweet Source Section options
        self.bot_ini_use_database = 'use_database'
        self.bot_ini_use_textfile = 'use_textfile'
        self.bot_ini_use_database_value = False
        self.bot_ini_use_textfile_value = True

        # BotConfig.ini Timing Section options
        self.bot_ini_delay_accounts = 'delay_accounts'
        self.bot_ini_delay_accounts_value = '0:1'
        self.bot_ini_delay_single_tweet = 'delay_single_tweet'
        self.bot_ini_delay_single_tweet_value = '0:1' 

        self.continue_tweeting = False
        self.tweeting_thread = None        
        # Create the TwitterAccounts.ini file if it doesnt exist
        try:
            if not os.path.isfile(self.twitter_account_ini_name):
                twitter_accounts_file = open(self.twitter_account_ini_name, 'w')
                twitter_accounts_file.close()
            else:
                self.populateAccountList()
        except IOError:
            self.raiseErrorBox("%s could not be created!") %self.twitter_account_ini_name

        #Create the BotConfig.ini if it doesnt exist and set the .ini with default settings
        try:
            if not os.path.isfile(self.settings_ini_name):
                settings_ini_file = open(self.settings_ini_name, 'w')
                settings_ini_file.close()
                self.setIniToDefaultSettings()
            else:
                self.setAttributestoUserSettings()
        except IOError:
            self.raiseErrorBox("%s could not be created!") %self.settings_ini_name
        
    def runBot(self):
        if self.bot_ini_use_textfile_value:
            self.tweeting_thread = WorkThread(self.tweetWithTextFile)
            self.tweeting_thread.start()
        else:
            self.tweeting_thread = WorkThread(self.tweetWithDatabase)
            self.tweeting_thread.start()

    def stopBot(self):
        self.tweeting_thread.terminate()

    def tweetWithTextFile(self):
        twython_user_instances = self.getTwitterUserList()
        hashtag = self.mainWindow.hashtag_lineEdit.text()
        tweets_list = []
        with open(self.bot_ini_path_value, 'r') as tweets_file:
            tweets_list = tweets_file.read().splitlines()
        
        successful_tweets = 0
        failed_tweets = 0
        for counter, tweet in enumerate(tweets_list):
            tweet_text = '%s %s' %(tweet.decode('UTF-8'), hashtag)
            success = self.sendTweet(twython_user_instances, tweet_text, counter+1)
            if success:
                successful_tweets += 1
            else:
                failed_tweets +=1
        self.startSleep("::All Accounts Tweeted sleeping", self.bot_ini_delay_accounts_value)
        log_summary = "::Tweet Nr: %i\nSuccessful send: %i\nFailed to send: %i" %(counter+1,
                successful_tweets, failed_tweets)
        self.mainWindow.logs_textBrowser.append(log_summary)

    def tweetWithDatabase(self):
        twython_user_instances = self.getTwitterUserList()
        hashtag = self.mainWindow.hashtag_lineEdit.text()
        db_client = pymongo.MongoClient(self.bot_ini_uri_value)
        db_name, collection_name = self.bot_ini_database_value.split(':')
        db = db_client[db_name]
        tweet_collection = db[collection_name]
        tweet_collection_cursor = tweet_collection.find()
        
        successful_tweets = 0
        failed_tweets = 0
        for counter, tweet in enumerate(tweet_collection_cursor):
            tweet_text = '%s %s' %(tweet['tweet'], hashtag)
            info = "::Sending Tweet Nr. %i\n%s" %(counter+1, tweet_text)
            self.mainWindow.tweet_textBrowser.append(info)
            success = self.sendTweet(twython_user_instances, tweet_text, counter+1)
            if success:
                successful_tweets += 1
            else:
                failed_tweets += 1

            self.startSleep("::All Accounts Tweeted sleeping", self.bot_ini_delay_accounts_value)
            log_summary = "::Tweet Nr: %i\nSuccessful send: %i\nFailed to send: %i" %(counter+1,
                    successful_tweets, failed_tweets)
            self.mainWindow.logs_textBrowser.append(log_summary)


    def sendTweet(self, twython_user_instances, tweet_text, tweet_number):
        for user in twython_user_instances:
            try:
                user.update_status(status=tweet_text)
            except TwythonError as e:
                log_error = "::Error sending Tweet Nr. %i!\nStatus Code: %s\n Exception: %s" % \
                        (tweet_number, user._last_call['status_code'], e)
                self.mainWindow.logs_textBrowser.append(log_error)
                return False
        return True

    def startSleep(self, message, ttw):
        minutes, seconds = ttw.split(':')
        total_seconds = (int(minutes)*60) + int(seconds)
        log = "%s: %i sec." %(message, total_seconds)
        self.mainWindow.logs_textBrowser.append(log)
        while total_seconds > 0:
            total_seconds -= 1
            time.sleep(1)

    def setIniToDefaultSettings(self):
        """
        If the .ini File is created the first time, we will set the 
        default Settings which we get from the class Attributes specified in __init__
        """
        config_parser = configparser.SafeConfigParser()
        
        # Adding the necessary sections first
        config_parser.add_section(self.bot_ini_mongo_section)
        config_parser.add_section(self.bot_ini_text_file_section)
        config_parser.add_section(self.bot_ini_tweet_source_section)
        config_parser.add_section(self.bot_ini_timing_section)
       
        # Mongo DB Section Options
        config_parser.set(self.bot_ini_mongo_section, self.bot_ini_uri,self.bot_ini_uri_value)
        config_parser.set(self.bot_ini_mongo_section, self.bot_ini_database,
                self.bot_ini_database_value)
        
        # Text File Section Options
        config_parser.set(self.bot_ini_text_file_section, self.bot_ini_path,
                self.bot_ini_path_value)
       
        # Tweet Source Section Options
        config_parser.set(self.bot_ini_tweet_source_section, self.bot_ini_use_textfile,
                str(self.bot_ini_use_textfile_value))
        config_parser.set(self.bot_ini_tweet_source_section, self.bot_ini_use_database,
                str(self.bot_ini_use_database_value))
        
        # Timing Section Options
        config_parser.set(self.bot_ini_timing_section, self.bot_ini_delay_accounts,
                self.bot_ini_delay_accounts_value)
        config_parser.set(self.bot_ini_timing_section, self.bot_ini_delay_single_tweet,
                self.bot_ini_delay_single_tweet_value)

        self.saveIniFile(self.settings_ini_name, config_parser)
        self.setGUISettings()

    def setGUISettings(self):
        # Set Tweet Source GUI Radio Buttons
        self.mainWindow.usedatabase_radio.setChecked(self.bot_ini_use_database_value)
        self.mainWindow.usetextfile_radio.setChecked(self.bot_ini_use_textfile_value)
        
        # Set Timing GUI Values
        delay_accounts_value_min, delay_accounts_value_sec = \
            self.bot_ini_delay_accounts_value.split(':')

        self.mainWindow.delaybetweenaccounts_timeEdit.setTime(QTime(0,
            int(delay_accounts_value_min), int(delay_accounts_value_sec)))

        delay_single_tweet_value_min, delay_single_tweet_value_sec = \
                self.bot_ini_delay_single_tweet_value.split(':')

        self.mainWindow.delayaftertweet_timeEdit.setTime(QTime(0, int(delay_single_tweet_value_min),
                int(delay_single_tweet_value_sec)))

        # Set Database GUI Values
        self.mainWindow.databaseuri_lineEdit.setText(self.bot_ini_uri_value)
        self.mainWindow.database_lineEdit.setText(self.bot_ini_database_value)

        # Set Textfile path GUI Value
        self.mainWindow.filename_lineEdit.setText(self.bot_ini_path_value)

    def setAttributestoUserSettings(self):
        config_parser = configparser.SafeConfigParser()
        config_parser.read(self.settings_ini_name)
        
        # Set Mongo DB Attribute from INI File
        self.bot_ini_uri_value = config_parser.get(self.bot_ini_mongo_section, self.bot_ini_uri)

        self.bot_ini_database_value = config_parser.get(self.bot_ini_mongo_section,
                self.bot_ini_database)

        # Set Tweet Text File Path
        self.bot_ini_path_value = config_parser.get(self.bot_ini_text_file_section,
                self.bot_ini_path)

        # Set Tweet Source Attributes from INI File
        self.bot_ini_use_textfile_value = config_parser.getboolean(self.bot_ini_tweet_source_section,
                self.bot_ini_use_textfile)

        self.bot_ini_use_database_value = config_parser.getboolean(self.bot_ini_tweet_source_section,
                self.bot_ini_use_database)
        
        # Set Timing Attributes from INI File
        self.bot_ini_delay_accounts_value = config_parser.get(self.bot_ini_timing_section,
                self.bot_ini_delay_accounts)

        self.bot_ini_delay_single_tweet_value = config_parser.get(self.bot_ini_timing_section,
                self.bot_ini_delay_single_tweet)
        

        # GUI should always set to the correct settings
        self.setGUISettings()

    def startAuthentication(self):
        self.twitter_account_username = str(self.mainWindow.twitteraccountname_lineEdit.text())
        is_new_user = self.checkUser(self.twitter_account_username)
        if is_new_user:
            self.loadAuthenticationWebview()
        elif is_new_user is None:
            self.raiseErrorBox("Username cannot be empty!")
        else:
            self.raiseErrorBox("Twitter Username: '%s' already exists! Delete it first" %
                    self.twitter_account_username)
    
    def loadAuthenticationWebview(self):
        self.consumer = oauth.Consumer(self.CONSUMER_KEY, self.CONSUMER_SECRET)
        client = oauth.Client(self.consumer)
        response, content = client.request(self.REQUEST_TOKEN_URL, "GET")

        if response['status'] != '200':
            raise Exception("Invalid response %s" %response['status'])
        else:
            self.request_token = dict(urlparse.parse_qsl(content))
            url = "%s?oauth_token=%s" %(self.AUTHORIZE_URL, self.request_token['oauth_token']) 
            self.mainWindow.webView.load(QUrl(url))      

    def verifyPin(self):
        try:
            oauth_verifier_pin = str(self.mainWindow.pin_lineEdit.text())
            try:
                if self.twitter_account_username and oauth_verifier_pin.isdigit():
                    request_token = self.request_token
                    token = oauth.Token(request_token['oauth_token'],
                            request_token['oauth_token_secret'])
                    token.set_verifier(oauth_verifier_pin)
                    client = oauth.Client(self.consumer, token)
                    response, content = client.request(self.ACCESS_TOKEN_URL, 'POST')
                    access_token = dict(urlparse.parse_qsl(content))
                    self.saveOAuthToken(self.twitter_account_username, access_token)
                else:
                    self.raiseErrorBox("No Username specified, or PIN is not digit!")
            except Exception as e:
                self.raiseErrorBox("PIN was not accepted!")
        except Exception:
            self.raiseErrorBox("PIN accepts numbers!")
        
    def saveOAuthToken(self, twitter_account_username, access_token):
        try:
            config_parser = configparser.SafeConfigParser()
            config_parser.read(self.twitter_account_ini_name)
            is_new_user = self.checkUser(twitter_account_username)
            if is_new_user: 
                config_parser.add_section(str(twitter_account_username))
                config_parser.set(str(twitter_account_username), 'oauth_token',
                        access_token['oauth_token'])
                config_parser.set(str(twitter_account_username), 'oauth_token_secret',
                        access_token['oauth_token_secret'])
                self.mainWindow.twitteraccounts_listWidget.addItem(twitter_account_username)
                self.saveIniFile(self.twitter_account_ini_name, config_parser)
                self.raiseInfoBox("OK! Token was saved!")
            else:
                self.raiseErrorBox("Username already Exists! Delete it first")
        except KeyError:
            self.raiseErrorBox("PIN was wrong, or Authentication timed out!")
    
    def populateAccountList(self):
        config_parser = configparser.SafeConfigParser()
        config_parser.read(self.twitter_account_ini_name)
        sections = config_parser.sections()
        if sections:
            for section in sections:
                self.mainWindow.twitteraccounts_listWidget.addItem(section)
        else:
            self.raiseInfoBox("No Twitter Accounts found! You have to add at least one")

    def deleteAccount(self):
        config_parser = configparser.SafeConfigParser()
        config_parser.read(self.twitter_account_ini_name)
        selected_items = self.mainWindow.twitteraccounts_listWidget.selectedItems()
        for item in selected_items:
            current_item = self.mainWindow.twitteraccounts_listWidget.row(item)
            user_name = str(self.mainWindow.twitteraccounts_listWidget.takeItem(current_item).text())
      
            if config_parser.remove_section(user_name):
                self.saveIniFile(self.twitter_account_ini_name, config_parser)
                self.raiseInfoBox("User has been deleted")
            else:
                self.raiseErrorBox("User could not be deleted!")

    def saveIniFile(self, ini_file_name, config_parser):
        with open(ini_file_name, 'w') as configfile:
            config_parser.write(configfile)

    def checkUser(self, twitter_account_username):
        config_parser = configparser.SafeConfigParser()
        config_parser.read(self.twitter_account_ini_name)
        if twitter_account_username:
            if config_parser.has_section(twitter_account_username):
                return False
            else:
                return True
        else:
            return None

    def setiniDatabase(self):
        config_parser = configparser.SafeConfigParser()
        self.bot_ini_uri_value = str(self.mainWindow.databaseuri_lineEdit.text())
        self.bot_ini_database_value = str(self.mainWindow.database_lineEdit.text())
        
        config_parser.read(self.settings_ini_name)
        config_parser.set(self.bot_ini_mongo_section, self.bot_ini_uri, self.bot_ini_uri_value)
        config_parser.set(self.bot_ini_mongo_section, self.bot_ini_database,
                self.bot_ini_database_value)
        self.saveIniFile(self.settings_ini_name, config_parser)
    
    def setTextFilePath(self):
        self.tweets_text_file_name = str(QFileDialog.getOpenFileName(None, 'Open File', ''))
        self.mainWindow.filename_lineEdit.setText(self.tweets_text_file_name)

        config_parser = configparser.SafeConfigParser()
        config_parser.read(self.settings_ini_name)
        config_parser.set(self.bot_ini_text_file_section, self.bot_ini_path,
                self.tweets_text_file_name)
        self.saveIniFile(self.settings_ini_name, config_parser)

    def setiniSource(self):
        self.bot_ini_use_database_value = self.mainWindow.usedatabase_radio.isChecked() 
        self.bot_ini_use_textfile_value = self.mainWindow.usetextfile_radio.isChecked()
        config_parser = configparser.SafeConfigParser()
        config_parser.read(self.settings_ini_name)
        
        config_parser.set(self.bot_ini_tweet_source_section, self.bot_ini_use_textfile,
                str(self.bot_ini_use_textfile_value))
        config_parser.set(self.bot_ini_tweet_source_section, self.bot_ini_use_database,
                str(self.bot_ini_use_database_value))

        self.saveIniFile(self.settings_ini_name, config_parser)

    def setiniTiming(self):
        self.bot_ini_delay_accounts_value = '%s:%s' \
                %(self.mainWindow.delaybetweenaccounts_timeEdit.time().minute(),
                        self.mainWindow.delaybetweenaccounts_timeEdit.time().second())

        self.bot_ini_delay_single_tweet_value = '%s:%s' \
                %(self.mainWindow.delayaftertweet_timeEdit.time().minute(),
                        self.mainWindow.delayaftertweet_timeEdit.time().second())

        config_parser = configparser.SafeConfigParser()
        config_parser.read(self.settings_ini_name)

        config_parser.set(self.bot_ini_timing_section, self.bot_ini_delay_accounts,
                self.bot_ini_delay_accounts_value)
        config_parser.set(self.bot_ini_timing_section, self.bot_ini_delay_single_tweet,
                self.bot_ini_delay_single_tweet_value)

        self.saveIniFile(self.settings_ini_name, config_parser)
    
    def getTwitterUserList(self):
        twitter_user = []
        config_parser = configparser.SafeConfigParser()
        config_parser.read(self.twitter_account_ini_name)
        for section in config_parser.sections():
            twitter_user.append(Twython(self.CONSUMER_KEY, self.CONSUMER_SECRET,
                config_parser.get(section, 'oauth_token'),
                config_parser.get(section, 'oauth_token_secret')))
        
        return twitter_user
    
    def raiseErrorBox(self, text):
        QMessageBox.critical(None, "Error", text, QMessageBox.Ok)

    def raiseInfoBox(self, text):
        QMessageBox.information(None, "Info", text, QMessageBox.Ok)
