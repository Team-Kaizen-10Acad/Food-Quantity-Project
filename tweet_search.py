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
    def __init__(self, cols=None,auth=None):
        #
        if not cols is None:
            self.cols = cols
        else:
            self.cols = ['id', 'created_at', 'source', 'original_text','clean_text', 
                    'sentiment','polarity','subjectivity', 'lang',
                    'favorite_count', 'retweet_count','likes' 'original_author',   
                    'possibly_sensitive', 'hashtags',
                    'user_mentions', 'place', 'place_coord_boundaries']
            
        if auth is None:
            
            #Variables that contains the user credentials to access Twitter API 
            consumer_key = os.environ.get('consumer_key')
            consumer_secret = os.environ.get('consumer_secret')
            access_token = os.environ.get('access_token')
            access_token_secret = os.environ.get('access_token_secret')
            


            #This handles Twitter authetification and the connection to Twitter Streaming API
            auth = OAuthHandler('zzhhovmbdmcnIjt269PeXHLkI', 'T8M22C8VscdByfcC5n55Fs3TsWTj4cPwVB3TZKrIEtL9xdsYJx')
            auth.set_access_token('990262908696387584-UDoYmQkDIIEjhMDOU32eErYQTofDEAi', 'CeHUl9BTdkssuZ4seXiN72jg3xz26RHO41zOguKhHaSqM')
            

           
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
       
    def get_tweets(self, keyword, csvfile=None):
        
        
        df = pd.DataFrame(columns=self.cols)
        
        if not csvfile is None:
            #If the file exists, then read the existing data from the CSV file.
            if os.path.exists(csvfile):
                df = pd.read_csv(csvfile, header=0)
            

        #page attribute in tweepy.cursor and iteration
        for page in tweepy.Cursor(self.api.search, q=keyword,count=500, include_rts=False).pages():

            # the you receive from the Twitter API is in a JSON format and has quite an amount of information attached
            for status in page:
                
                new_entry = []
                status = status._json
                
                #filter by language
                if status['lang'] != 'en':
                    continue

                
                #if this tweet is a retweet update retweet count
                if status['created_at'] in df['created_at'].values:
                    i = df.loc[df['created_at'] == status['created_at']].index[0]
                    #
                    cond1 = status['favorite_count'] != df.at[i, 'favorite_count']
                    cond2 = status['retweet_count'] != df.at[i, 'retweet_count']
                    if cond1 or cond2:
                        df.at[i, 'favorite_count'] = status['favorite_count']
                        df.at[i, 'retweet_count'] = status['retweet_count']
                    continue

                #calculate sentiment
                filtered_tweet = self.clean_tweets(status['text'])
                blob = TextBlob(filtered_tweet)
                Sentiment = blob.sentiment     
                polarity = Sentiment.polarity
                subjectivity = Sentiment.subjectivity

                new_entry += [status['id'], status['created_at'],
                              status['source'], status['text'], filtered_tweet, 
                              Sentiment,polarity,subjectivity, status['lang'],
                              status['favorite_count'], status['retweet_count']]

                new_entry.append(status['user']['screen_name'])

                try:
                    is_sensitive = status['possibly_sensitive']
                except KeyError:
                    is_sensitive = None

                new_entry.append(is_sensitive)

                hashtags = ", ".join([hashtag_item['text'] for hashtag_item in status['entities']['hashtags']])
                new_entry.append(hashtags) #append the hashtags

                #
                mentions = ", ".join([mention['screen_name'] for mention in status['entities']['user_mentions']])
                new_entry.append(mentions) #append the user mentions

                try:
                    xyz = status['place']['bounding_box']['coordinates']
                    coordinates = [coord for loc in xyz for coord in loc]
                except TypeError:
                    coordinates = None
                #
                new_entry.append(coordinates)

                try:
                    location = status['user']['location']
                except TypeError:
                    location = ''
                #
                new_entry.append(location)

                #now append a row to the dataframe
                single_tweet_df = pd.DataFrame([new_entry], columns=self.cols)
                df = df.append(single_tweet_df, ignore_index=True)

        if not csvfile is None:
            #save it to file
            df.to_csv(csvfile, columns=self.cols, index=False, encoding="utf-8")
            
        return df
