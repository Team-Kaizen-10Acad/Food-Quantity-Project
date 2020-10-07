import sys
from tweet_search import TweetSearch

def main(geoloc, lockdown_started, lockdown_ended, file_output):
    pass
    keywords = ['#food4all','#fooddemand','#foodsecurity','#foodsupply',
                  '#foodinsecurity','#foodsupply','#foodsupplychain',
                  '#foodservice','#foodconsunption','#UhuruKenyansNeedFood','#FoodShortage']

    filter_keywords = ['food','food4all','fooddemand','foodsecurity',
                    'foodsupply', 'food supply','food insecurity','foodinsecurity',
                    'foodsupplychain', 'food supply chain','food service','foodservice',
                    'foodconsumption', 'food consumption' 'UhuruKenyansNeedFood',
                    'Uhuru Kenyans Need Food','FoodShortage', 'Food Shortage']
    
    consumer_key = 'consumer_key'
    consumer_secret = 'consumer_secret'
    access_token = 'access_token'
    access_token_secret = 'access_token_secret'

    tweet_search = TweetSearch(consumer_key = consumer_key, consumer_secret = consumer_secret, 
        access_token = access_token, access_token_secret = access_token_secret)

    tweet_search.search_store(geoloc=geoloc, begin_date=lockdown_started, end_date=lockdown_ended, keywords=keywords, filter_keywords=filter_keywords, file_output=file_output)

if __name__ == '__main__':

    geoloc = sys.argv[1]
    lockdown_started = sys.argv[2]
    lockdown_ended = sys.argv[3]
    file_output = sys.argv[4]

    main(geoloc, lockdown_started, lockdown_ended, file_output)