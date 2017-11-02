import sys
import json
from pprint import pprint


class JSON:
    @staticmethod
    def load(filename):
        try:
            with open(filename) as data_file:
                data = json.load(data_file)
           # pprint(data)
            return data
        except:
            print("Unexpected error:", sys.exc_info()[0])
            # raise
            return None

    @staticmethod
    def save(filename, data):
        try:
            with open(filename, 'w') as data_file:
                json_data = json.dumps(data)
              #  pprint(json_data)
                data_file.write(json_data)
                print("saved: " + filename)
            return True
        except:
            print("Unexpected error:", sys.exc_info()[0])
            # raise
            return False
