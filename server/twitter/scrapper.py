import json
from tweetpreprocessor import TWPreprocessor
from twitterapi import TwitterAPI
from bson import json_util
import time
import pickle

mode = "pois"
is_reply_collect_require = False


class Scrapper:
    def __init__(self) -> None:
        devconfig_details = Scrapper.read_write_json(
            "read", '/Users/omnamhashivaya/Drive Data/Buffalo MS/College Project/IR Projects/Project 4/server/config/twitter.dev.json', None)
        self.config = Scrapper.read_write_json(
            "read", "/Users/omnamhashivaya/Drive Data/Buffalo MS/College Project/IR Projects/Project 4/server/config/scrapper.config.json", None)
        self.twitter = TwitterAPI(devconfig_details['consumer_key'], devconfig_details['consumer_secret'],
                                  devconfig_details['access_token'], devconfig_details['access_token_secret'])

    @staticmethod
    def file_read_write(path, mode, data=None):
        if mode == "wb":
            with open(path, mode) as output_file:
                pickle.dump(data, output_file)
        else:
            with open(path, mode) as output_file:
                data = pickle.load(output_file)
            return data

    @staticmethod
    def read_write_json(operation, filepath, data):
        if operation == 'read':
            with open(filepath, "r", encoding='utf-8') as json_file:
                data = json.load(json_file)
        else:
            with open(filepath, "w",  encoding='utf-8') as json_file:
                json.dump(data, json_file, default=json_util.default,
                          ensure_ascii=False)
        return data

    def start_method(self):
        if mode == 'pois' or mode == 'both':
            for idx, pois in enumerate(self.config['pois']):
                processed_tweet = []
                unprocessed_tweet = []
                processed_reply = {}
                unprocessed_reply = {}
                if pois["count"] > 0:
                    screen_name = pois['screen_name']
                    print("-------poi started-------->", screen_name)
                    poi_tweets = self.twitter.get_tweets_by_poi_screen_name(
                        {'screen_name': screen_name})
                    print("----- api finish ------")
                    tweet_id_list = self.config["pois"][idx]["tweet_id_list"]
                    replies_id_list = self.config["pois"][idx]["replies_id_list"]
                    for tweet in poi_tweets:
                        tweet = tweet._json
                        tweet_id_list.append(tweet['id'])
                        self.config["pois"][idx]["count"] -= 1
                        if ('retweeted' in tweet and tweet['retweeted']) or tweet['text'].lower().startswith("rt @"):
                            self.config["pois"][idx]["retweet_count"] += 1
                        replies_processed_list = []
                        if is_reply_collect_require:
                            replies = self.twitter.get_replies(
                                {'name': screen_name, 'tweet_id': tweet['id']})
                            for reply in replies:
                                replies_processed_list.append(
                                    TWPreprocessor.preprocess(reply, True, pois['country']))
                                replies_id_list.append(reply['id'])
                            if(len(replies) > 0):
                                processed_reply[screen_name + "_" +
                                                str(tweet["id"])] = replies_processed_list
                                unprocessed_reply[screen_name +
                                                  "_" + str(tweet["id"])] = replies
                        processed_tweet.append(
                            TWPreprocessor.preprocess(tweet, True, pois['country']))
                        unprocessed_tweet.append(tweet)
                    self.config["pois"][idx]["tweet_id_list"] = list(
                        set(tweet_id_list))
                    self.config["pois"][idx]["replies_id_list"] = list(
                        set(replies_id_list))
                    Scrapper.read_write_json(
                        'write', './config/scrapper.config.json', self.config)
                    Scrapper.read_write_json(
                        'write', './data/raw/pois_' + screen_name + '.json', unprocessed_tweet)
                    Scrapper.read_write_json(
                        'write', './data/json/pois_' + screen_name + '.json', processed_tweet)
                    Scrapper.file_read_write(
                        './data/pickle/pois_' + screen_name + '.pkl', 'wb', processed_tweet)

                    if is_reply_collect_require:
                        Scrapper.read_write_json(
                            'write', './data/raw/reply_' + screen_name + '.json', unprocessed_reply)
                        Scrapper.read_write_json(
                            'write', './data/json/reply_' + screen_name + '.json', processed_reply)
                        Scrapper.file_read_write(
                            './data/pickle/reply_' + screen_name + '.pkl', 'wb', processed_reply)

                    print("-------poi ended-------->")
                    time.sleep(5)

        if mode == 'keyword' or mode == 'both':
            for idx, keyword in enumerate(self.config['keywords']):
                processed_tweet = []
                unprocessed_tweet = []
                processed_reply = {}
                unprocessed_reply = {}
                if keyword["count"] > 0:
                    name = keyword['name']
                    print("-------keyword started-------->", name)
                    keyword_tweets = self.twitter.get_tweets_by_lang_and_keyword(
                        {'query': name, 'count': keyword['count'], 'lang': keyword['lang']})
                    print("----- api finish ------")
                    for tweet in keyword_tweets:
                        tweet = tweet._json
                        self.config["keywords"][idx]["count"] -= 1
                        if ('retweeted' in tweet and tweet['retweeted']) or tweet['full_text'].lower().startswith("rt @"):
                            self.config["keywords"][idx]["retweet_count"] += 1
                        processed_tweet.append(
                            TWPreprocessor.preprocess(tweet, False))
                        unprocessed_tweet.append(tweet)

                    Scrapper.read_write_json(
                        'write', './config/scrapper.config.json', self.config)
                    Scrapper.read_write_json(
                        'write', './data/raw/keywords_' + name + '.json', unprocessed_tweet)
                    Scrapper.read_write_json(
                        'write', './data/json/keywords_' + name + '.json', processed_tweet)
                    Scrapper.file_read_write(
                        './data/pickle/keywords_' + name + '.pkl', 'wb', processed_tweet)
                    print("-------poi ended-------->")
                    time.sleep(5)


sc = Scrapper()
sc.start_method()
