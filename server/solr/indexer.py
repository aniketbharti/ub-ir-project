import json
from solr import Solr
import string
import re
import demoji
# from textblob import TextBlob
import glob
import os
import time
from googletrans import Translator

run_config = "../config/solr.config.json"
translator = Translator()


class Indexer:
    def __init__(self) -> None:
        self.run_config = self.read_file(run_config)
        if self.run_config["indexer"] == "BM25":
            self.core = Solr("BM25_CORE", "./configs/config_bm25.json")
        else:
            self.core = Solr("VSM_CORE", "./configs/config_vsm.json")
        if self.run_config["resetindexer"]:
            self.core.replace_indexer_schema(b="0.75", k="1.2")
        if self.run_config["uploaddata"]:
            self.load_data()

    def load_data(self):
        train_data = self.read_file("data/train.json")
        if train_data:
            for idx, data in enumerate(train_data):
                for k, v in data.items():
                    if k in ["text_ru", "text_en", "text_de"]:
                        train_data[idx][k] = self.pre_process(v)
            self.BM25_solr.create_documents(train_data)
            self.VSM_solr.create_documents(train_data)

    def read_file(self, filename):
        data = None
        with open(filename, "r") as json_file:
            data = json.load(json_file)
        return data

    def get_weights(self, lang, model):
        language = {
            "en": [("text_en", (3, 1.5)), ("text_ru", (2.5, 0.2)), ("text_de", (2, 1.2))],
            "de": [("text_de", (3, 1.5)), ("text_en", (2.5, 1.2)), ("text_ru", (2, 0.2))],
            "ru": [("text_ru", (3, 1.5)), ("text_en", (2.5, 1.2)), ("text_de", (2, 0.2))],
        }
        data = language[lang]
        initial = data.pop(0)
        stringdata = initial[0] + '^' + str(initial[1][model])
        for idx, i in enumerate(data):
            stringdata = stringdata + " " + i[0] + "^" + str(i[1][model])
        return stringdata

    def get_search(self, query, lang):
        language = {
            "en": [("text_en", (3, 3), "en"), ("text_ru", (3, 1.5), "ru"), ("text_de", (3, 2), "de")],
            "de": [("text_de", (3, 3), "de"), ("text_en", (3, 2), "en"), ("text_ru", (3, 1.5), "ru")],
            "ru": [("text_ru", (3, 3), "ru"), ("text_en", (3, 2), "en"), ("text_de", (3, 1.5), "de")],
        }
        data = language[lang]
        initial = data.pop(0)
        indata = initial[0] + " : " + str(query)
        for idx, i in enumerate(data):
            try:
                indata = indata + " or " + i[0] + \
                    " : " + str(translator.translate(query, dest=i[2]).text)
            except:
                indata = indata + " or " + i[0] + " : " + str(query)
        return indata


indexer = Indexer()
