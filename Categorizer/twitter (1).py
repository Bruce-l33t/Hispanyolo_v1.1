# Twitter sentiment tool - 5k /mo

import httpx

original_client = httpx.Client

def patched_client(*args, **kwargs):
    kwargs.pop('proxy', None)
    return original_client(*args, **kwargs)

httpx.Client = patched_client

# imports 
from twikit import Client, TooManyRequests
import time 
from datetime import datetime 
import csv 
from random import randint
import dontshare as d 

USERNAME = d.user_name
EMAIL = d.email 
PASSWORD = d.password 
QUERY = "solana"
MINIMUM_TWEETS = 100 
SEARCH_STYLE = 'latest' # top 

# ignore list
IGNORE_LIST = ['t.co', 'discord', 'join', 'telegram', 'discount', 'pay']

client = Client()

# # RUN 1 time to log in and save cookies
# client.login(auth_info_1=USERNAME, auth_info_2=EMAIL, password=PASSWORD)
# client.save_cookies("cookies.json")

# user everytime after - loads in cookies instead of logging in again
client.load_cookies("cookies.json")

# create a csv
with open('tweets.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["tweet_count", "user_name", "text", "created_at", "retweet_count", 'favorite_count', 'reply_count'])

# get tweets function
def get_tweets(tweets):
    if tweets is None:
        print(f'time is {datetime.now()} - getting next tweets')
        time.sleep(randint(2,6))
        tweets = client.search_tweet(QUERY, product=SEARCH_STYLE)
    else:
        print(f'time is {datetime.now()} - getting next tweets')
        time.sleep(randint(5,13))
        tweets = tweets.next()

    return tweets

def should_ignore_tweet(text):
    return any(word.lower() in text.lower() for word in IGNORE_LIST)



tweet_count = 0 
tweets = None

while tweet_count < MINIMUM_TWEETS:
    try:
        tweets = get_tweets(tweets)
    except TooManyRequests as e:
        rate_limit_reset = datetime.fromtime(e.rate_limit_reset)
        print(f'time is {datetime.now()} - rate limit reached, waiting until {rate_limit_reset}')
        wait_time = rate_limit_reset - datetime.now()
        print(f'waiting for {wait_time}')
        time.sleep(wait_time.total_seconds())
        continue 

    if not tweets:
        print(f'time is {datetime.now()} - no more tweets')
        break

    for tweet in tweets:
        if should_ignore_tweet(tweet.text):
            continue

        tweet_count += 1
        tweet_data = [
            tweet_count,
            tweet.user.name,
            tweet.text,
            tweet.created_at,
            tweet.retweet_count,
            tweet.favorite_count,
            tweet.reply_count
        ]
        print(tweet_data)
        with open('tweets.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(tweet_data)

    print(f'time is {datetime.now()} - tweet count is {tweet_count}')