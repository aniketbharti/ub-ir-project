import regex
import datetime
import preprocessor as p
import json
import pydash
import emoji
import demoji


class TWPreprocessor:
    @staticmethod
    def read_solr_fields_config():
        data = None
        with open("/Users/omnamhashivaya/Drive Data/Buffalo MS/College Project/IR Projects/Project 4/server/config/twitter.solor.mapping.json") as json_file:
            data = json.load(json_file)
        return data

    @staticmethod
    def format_date(tweet_date):
        t = datetime.datetime.strptime(
            str(tweet_date), '%a %b %d %H:%M:%S +0000 %Y')
        return TWPreprocessor._hour_rounder(t).strftime('%Y-%m-%dT%H:%M:%SZ')

    @staticmethod
    def _hour_rounder(t):
        c = (t.replace(second=0, microsecond=0, minute=0, hour=t.hour)
             + datetime.timedelta(hours=t.minute//30))
        return c

    @staticmethod
    def get_emoji_list(text):
        emoji_list = []
        data = regex.findall(r'\X', text)
        for word in data:
            if any(char in emoji.UNICODE_EMOJI['en'] for char in word):
                emoji_list.append(word)
        return emoji_list

    @staticmethod
    def _text_cleaner(text):
        emojis = TWPreprocessor.get_emoji_list(text)
        p.set_options(p.OPT.URL, p.OPT.HASHTAG)
        clean_text = p.clean(text)
        clean_text = demoji.replace(clean_text, '')
        return clean_text, emojis

    @classmethod
    def preprocess(cls, tweet, is_poi, country=None):
        config = TWPreprocessor.read_solr_fields_config()
        if is_poi:
            config = config["pois"]
        else:
            config = config["keywords"]
        processing_req_fields_list = [
            "poi_name", "poi_id", "tweet_lang", "tweet_text", "hashtags", "mentions", "tweet_urls", "tweet_date", "geolocation"]
        processed_tweets = {}
        if config != None:
            for key, value in config.items():
                fieldValue = pydash.get(tweet, value)
                if fieldValue != None:
                    if key in processing_req_fields_list:
                        if key in ["poi_name", "poi_id"] and is_poi:
                            processed_tweets[key] = fieldValue
                        elif key == 'tweet_lang':
                            tweet_lan = fieldValue if fieldValue in [
                                'en', 'hi', 'es'] else 'en'
                            processed_tweets[key] = tweet_lan
                            if country:
                                processed_tweets['country'] = country
                            else:
                                if tweet_lan == 'en':
                                    processed_tweets['country'] = 'USA'
                                elif tweet_lan == 'hi':
                                    processed_tweets['country'] = 'India'
                                else:
                                    processed_tweets['country'] = 'Mexico'
                        elif key == 'tweet_text':
                            processed_tweets[key] = fieldValue
                            tweet_lan = tweet["lang"] if tweet["lang"] in [
                                'en', 'hi', 'es'] else 'en'
                            preprocessortext, emoticonlist = TWPreprocessor._text_cleaner(
                                fieldValue)
                            processed_tweets["text_" +
                                             tweet_lan] = preprocessortext
                            if len(emoticonlist) > 0:
                                processed_tweets["tweet_emoticons"] = emoticonlist
                            if 'replied_to_tweet_id' in processed_tweets:
                                processed_tweets["reply_text"] = preprocessortext
                        elif key == 'mentions' and len(fieldValue) > 0:
                            processed_tweets[key] = list(
                                map(lambda x: x['screen_name'], fieldValue))
                        elif key == 'hashtags' and len(fieldValue) > 0:
                            processed_tweets[key] = list(
                                map(lambda x: x['text'], fieldValue))
                        elif key == 'tweet_urls' and len(fieldValue) > 0:
                            processed_tweets[key] = list(
                                map(lambda x: x['expanded_url'], fieldValue))
                        elif key == "tweet_date":
                            processed_tweets[key] = TWPreprocessor.format_date(
                                fieldValue)
                    else:
                        processed_tweets[key] = fieldValue
        return processed_tweets
