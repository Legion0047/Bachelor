import json
import os

FILEPATH = "database.json"
class persistence():
    def load(self):
        self.exists()
        with open(FILEPATH, 'r') as openfile:
            json_object = json.load(openfile)
            json_object.pop('-1')
            json_object.update({0:{
                    "name": "Lamp",
                    "tags": ["Kitchen", "Living Room"],
                    "voltage": 230,
                    "current": 23,
                    "power": 10.5
                }})
            json_object.update({1:{
                    "name": "Blender",
                    "tags": ["Kitchen"],
                    "voltage": 220,
                    "current": 2.2,
                    "power": 600
                }})
        array = []
        for key in list(json_object.keys()):
            values = (list(json_object[key].values()))
            values.insert(0, key)
            values.append(False)
            array.append(values)
        return array

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
                -1: {
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
