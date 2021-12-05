import os
import pysolr
import json
import requests

dir = '../BM25/'
dir2 = '../VSM/'

AWS_IP = '18.116.39.248'
run_config = "./configs/run_config.json"


class Solr:
    def __init__(self, core_name, data_schema, ir_model_schema) -> None:
        self.solr_url = f'http://{AWS_IP}:8983/solr/'
        self.core_name = core_name
        self.data_schema = self.read_file(data_schema)
        self.ir_model_schema = self.read_file(ir_model_schema)
        self.run_config = self.read_file(run_config)
        self.connection = pysolr.Solr(
            self.solr_url + core_name, always_commit=True, timeout=5000000)
        self.do_initial_setup()

    def add_fields(self):
        if self.data_schema:
            req = requests.post(self.solr_url +
                                self.core_name + "/schema", json=self.data_schema)
            print("Add Fields : " + self.core_name + " ", req)

    def read_file(self, filename):
        data = None
        with open(filename, "r") as json_file:
            data = json.load(json_file)
        return data

    def do_initial_setup(self) -> None:
        if self.run_config and self.run_config['dropcreatecore']:
            self.delete_core()
            self.create_core()
            self.add_fields()

    def replace_indexer_schema(self, b=None, k=None) -> None:
        if self.ir_model_schema:
            for idx, list_data in enumerate(self.ir_model_schema["replace-field-type"]):
                similarity = list_data["similarity"]
                if similarity and "b" in similarity:
                    self.ir_model_schema["replace-field-type"][idx]["similarity"]["b"] = b
                if similarity and "k1" in similarity:
                    self.ir_model_schema["replace-field-type"][idx]["similarity"]["k1"] = k
            req = requests.post(self.solr_url + self.core_name +
                                "/schema", json=self.ir_model_schema)
            print("Indexer Statergy Change : " + self.core_name + " ", req)

    def create_documents(self, docs):
        print(self.connection.add(docs))

    def search(self, qid, query, lang_boast, model):
        self.run_config["params"]["pf"] = lang_boast
        search = self.connection.search(query, **self.run_config["params"])
        if model == 'bm25':
            filename = dir+str(int(qid)) + '.txt'
        else:
            filename = dir2+str(int(qid)) + '.txt'
        with open(filename, 'w') as f:
            rank = 1
            res = search.raw_response['response']
            for doc in res['docs']:
                f.write(qid + ' ' + 'Q0' + ' ' + str(doc['id']) + ' ' + str(
                    rank) + ' ' + str(doc['score']) + ' ' + model + '\n')
                rank += 1
        self.create_all_model_output(qid, search, model)

    def create_all_model_output(self, qid, search, model):
        if model == 'bm25':
            filename = dir + 'all.txt'
        else:
            filename = dir2 + 'all.txt'
        with open(filename, 'a') as f:
            rank = 1
            res = search.raw_response['response']
            for doc in res['docs']:
                f.write(qid + ' ' + 'Q0' + ' ' + str(doc['id']) + ' ' + str(
                    rank) + ' ' + str(doc['score']) + ' ' + model + '\n')
                rank += 1

    def create_core(self) -> None:
        print(os.system(
            'sudo su - solr -c "/opt/solr/bin/solr create -c {core} -n data_driven_schema_configs"'.format(
                core=self.core_name)))
        self.move_synomyns_file()

    def delete_core(self) -> None:
        print(os.system(
            'sudo su - solr -c "/opt/solr/bin/solr delete -c {core}"'.format(core=self.core_name)))

    def move_synomyns_file(self) -> None:
        if self.core_name == "VSM_CORE":
            print("Synonyms", os.system(
                'sudo cp "./wordnet/synonyms.txt" "/var/solr/data/VSM_CORE/conf"'))
        else:
            print("Synonyms", os.system(
                'sudo cp "./wordnet/synonyms.txt" "/var/solr/data/BM25_CORE/conf"'))
