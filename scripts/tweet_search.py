import numpy as np
import pandas as pd
import re
import os, sys
import string

import tweepy
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API
from tweepy import Cursor
from datetime import datetime, date, time, timedelta
import sys

import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
nltk.download('punkt')

import preprocessor as p

class TweetFilter():
    
    def __init__(self, df):
        self.df = df
    
    def filter_by_date(self, begin_date, end_date):
        return self.df[(self.df.created_at > begin_date) & (self.df.created_at < end_date)]
    
    def filter_by_keyword(self, df, keywords):
        return df[df.text.str.contains('|'.join(keywords), case=False)]
    
    def filter(self, begin_date, end_date, keywords):
        df_filter_by_date = self.filter_by_date(begin_date, end_date)
        return self.filter_by_keyword(df_filter_by_date, keywords)

class TweetSearch():
    '''
    This is a basic class to search and download twitter data.
    You can build up on it to extend the functionalities for more 
    sophisticated analysis
    '''
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):

        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
           
        self.auth = auth
        self.api = tweepy.API(auth, wait_on_rate_limit=True) 
        self.filtered_tweet = ''
            
    def clean_tweets(self, twitter_text):

        #use pre processor
        tweet = p.clean(twitter_text)

         #HappyEmoticons
        emoticons_happy = set([
            ':-)', ':)', ';)', ':o)', ':]', ':3', ':c)', ':>', '=]', '8)', '=)', ':}',
            ':^)', ':-D', ':D', '8-D', '8D', 'x-D', 'xD', 'X-D', 'XD', '=-D', '=D',
            '=-3', '=3', ':-))', ":'-)", ":')", ':*', ':^*', '>:P', ':-P', ':P', 'X-P',
            'x-p', 'xp', 'XP', ':-p', ':p', '=p', ':-b', ':b', '>:)', '>;)', '>:-)',
            '<3'
            ])

        # Sad Emoticons
        emoticons_sad = set([
            ':L', ':-/', '>:/', ':S', '>:[', ':@', ':-(', ':[', ':-||', '=L', ':<',
            ':-[', ':-<', '=\\', '=/', '>:(', ':(', '>.<', ":'-(", ":'(", ':\\', ':-c',
            ':c', ':{', '>:\\', ';('
            ])

        #Emoji patterns
        emoji_pattern = re.compile("["
                 u"\U0001F600-\U0001F64F"  # emoticons
                 u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                 u"\U0001F680-\U0001F6FF"  # transport & map symbols
                 u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                 u"\U00002702-\U000027B0"
                 u"\U000024C2-\U0001F251"
                 "]+", flags=re.UNICODE)

        #combine sad and happy emoticons
        emoticons = emoticons_happy.union(emoticons_sad)

        stop_words = set(stopwords.words('english'))
        word_tokens = nltk.word_tokenize(tweet)
        #after tweepy preprocessing the colon symbol left remain after      
        #removing mentions
        tweet = re.sub(r':', '', tweet)
        tweet = re.sub(r'‚Ä¶', '', tweet)

        #replace consecutive non-ASCII characters with a space
        tweet = re.sub(r'[^\x00-\x7F]+',' ', tweet)

        #remove emojis from tweet
        tweet = emoji_pattern.sub(r'', tweet)

        #filter using NLTK library append it to a string
        filtered_tweet = [w for w in word_tokens if not w in stop_words]

        #looping through conditions
        filtered_tweet = []    
        for w in word_tokens:
        #check tokens against stop words , emoticons and punctuations
            if w not in stop_words and w not in emoticons and w not in string.punctuation:
                filtered_tweet.append(w)

        return ' '.join(filtered_tweet)            
    
    def get_user_tweets(self, screen_name, begin_date, end_date, keywords):
        '''
        Search and return tweets of a user 
        '''
         #auth = tweepy.OAuthHandler('RPFdqfW02zjJBUz4own9u1bbq', 'FeGaoXU3MkKLpEtJW8OYoOlA0yjGVh4Pn3aqkcwWDwuHC9eUsE')
         #auth.set_access_token('1277497429856866305-vcP7taySdn9c8Gl2x13oaOJzWAoDjt', 'N46WpNcZgn6me2DTto0LsXtjPc8aQUu2WrKnPKp27rqZm')
         #api = tweepy.API(auth)

        #initialize a list to hold all the tweepy Tweets
        alltweets = []  

        #make initial request for most recent tweets (200 is the maximum allowed count)
        new_tweets = self.api.user_timeline(screen_name = screen_name, count=200)

        #save most recent tweets
        alltweets.extend(new_tweets)

        #save the id of the oldest tweet minus one
        oldest = alltweets[-1].id - 1

        #keep grabbing tweets until there are no tweets left to grab. 
        # Limit set to around 3k tweets, can be edited to preferred number.
        while len(new_tweets) > 0:
            print("getting tweets before %s" % (oldest))

            #all subsiquent requests use the max_id arg to prevent duplicates
            new_tweets = self.api.user_timeline(screen_name = screen_name,count=200, max_id=oldest)

            #save most recent tweets
            alltweets.extend(new_tweets)

            #update the id of the oldest tweet less one
            oldest = alltweets[-1].id - 1

            print("...%s tweets downloaded so far" % (len(alltweets)))   
        print('finish user')
        #transform the tweets into a 2D array that will populate the csv 
        outtweets = [[tweet.id_str,tweet.created_at,screen_name,tweet.retweet_count,tweet.favorite_count, 
                      self.clean_tweets(tweet.text)] for tweet in alltweets]
        
        # .encode("utf-8")
        
        tweets = pd.DataFrame(outtweets, columns=["id","created_at","screen_name","retweet_count","favorite_count","text"])
        return TweetFilter(tweets).filter(begin_date, end_date, keywords)
#         #write the csv  
#         with open('%s_tweets.csv' % screen_name, 'w') as f:
#             writer = csv.writer(f)
#             writer.writerow(["id","created_at","retweet_count","favorite_count","text"])
#             writer.writerows(outtweets)
        
    def get_usernames(self, geoloc, hashtags):
        '''
        Search for latest tweets that contains a hashtag and return
        tweet holders' username
        '''
        names = []
        for hashtag in hashtags:
            tweets = tweepy.Cursor(self.api.search, q = hashtag ,geocode=geoloc).items(1000000) #"0.0236,37.9062,1000km"
            users = []
            for status in tweets:
                name = status.user.screen_name
                t=status.text
                users.append(name)
            names.append(users)
        return [y for x in names for y in x]
    
    def search_store(self, geoloc, begin_date, end_date, keywords, filter_keywords, file_output):
        
        end_date = '2020-10-01' if(not end_date) else end_date
        begin_date = '2020-01-01' if (not begin_date) else begin_date

        file_output = 'tweets.csv' if(not file_output) else file_output
        
        hashtags=['#food4all','#fooddemand','#foodsecurity','#foodsupply',
                  '#foodinsecurity','#foodsupply','#foodsupplychain',
                  '#foodservice','#foodconsunption','#UhuruKenyansNeedFood','#FoodShortage']
        print('Start')
        user_names = self.get_usernames(geoloc, keywords)
        print('username end')
        
        tweet_output = pd.DataFrame(columns=["id","created_at","screen_name","retweet_count","favorite_count","text"])
        
        for username in list(set(user_names))[0:3]:
            print(username)
            tweet_user = self.get_user_tweets(username, begin_date, end_date, filter_keywords)
            tweet_output = pd.concat([tweet_output, tweet_user])
            tweet_output.to_csv(file_output)