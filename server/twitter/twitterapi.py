import datetime
import tweepy


class TwitterAPI:
    def __init__(self,  consumer_key, consumer_secret, access_token, access_token_secret) -> None:
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(
            self.auth, wait_on_rate_limit=True)
        self.today = datetime.date.today()
        self.since = self.today - datetime.timedelta(days=752)

    def _meet_basic_tweet_requirements(self, tweet, lang=None):
        if (tweet.full_text.lower()).startswith("rt @"):
            return 0
        elif tweet.retweeted is True:
            return 0
        elif lang:
            if lang == tweet.lang:
                return 1
            else:
                return 0
        return 1

    def get_tweets_by_poi_screen_name(self, config):
        return tweepy.Cursor(self.api.user_timeline, screen_name=config['screen_name']).items(700)

    def get_tweets_by_lang_and_keyword(self, config):
        return tweepy.Cursor(self.api.search_tweets, q=config['query'], count=config['count'],
                             since=self.since, until=self.today, tweet_mode='extended', lang=config['lang']).items()

    def get_replies(self, config):
        replies = []
        for page in tweepy.Cursor(self.api.search_tweets, q='to:'+config['name'], result_type='recent').pages(10):
            for tweet in page:
                tweet = tweet._json
                if ('in_reply_to_status_id' in tweet and tweet['in_reply_to_status_id'] == config['tweet_id']):
                    replies.append(tweet)
        return replies
