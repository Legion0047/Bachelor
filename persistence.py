import json
import os

FILEPATH = "database.json"
class persistence():
    def load(self):
        self.exists()
        with open(FILEPATH, 'r') as openfile:
            json_object = json.load(openfile)

    def add(self, item):
        self.exists()
        print("add: " + str(item[1]))

    def edit(self, item):
        self.exists()
        print("edit: " + str(item[1]))

    def delete(self, item):
        self.exists()
        print("delete: " + str(item[1]))

    def exists(self):
        if os.path.exists(FILEPATH) == False:
            # Data to be written
            dictionary = {
                "items": {
                    "id": -1,
                    "name": "existence",
                    "tags": "none",
                    "voltage": 50,
                    "current": 0.5,
                    "power": 25
                }
            }

            # Serializing json
            json_object = json.dumps(dictionary, indent=4)

            # Writing to sample.json
            with open(FILEPATH, "w") as outfile:
                outfile.write(json_object)
