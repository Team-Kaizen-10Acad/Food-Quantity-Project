import sys
from tweet_search import TweetSearch

def main(geoloc, first_case, file_output):
    pass
    keywords = ['#food4all','#fooddemand','#foodsecurity','#foodsupply',
                  '#foodinsecurity','#foodsupply','#foodsupplychain',
                  '#foodservice','#foodconsunption','#UhuruKenyansNeedFood','#FoodShortage']

    filter_keywords = ['food','food4all','fooddemand','foodsecurity',
                    'foodsupply', 'food supply','food insecurity','foodinsecurity',
                    'foodsupplychain', 'food supply chain','food service','foodservice',
                    'foodconsumption', 'food consumption' 'UhuruKenyansNeedFood',
                    'Uhuru Kenyans Need Food','FoodShortage', 'Food Shortage']

    tweet_search = TweetSearch()

    tweet_search.search_store(geoloc=geoloc, begin_date=first_case, end_date=False, keywords=keywords, filter_keywords=filter_keywords, file_output=file_output)

if __name__ == '__main__':

    geoloc = sys.argv[1]
    first_case = sys.argv[2]
    file_output = sys.argv[3]
    print(sys.argv)
    main(geoloc, first_case, file_output)