#!/usr/bin/env python3

import json
import os

FILEPATH = "database.json"


class persistence():
    def load(self):
        self.exists()
        with open(FILEPATH, 'r') as openfile:
            json_object = json.load(openfile)
        array = []
        for key in list(json_object.keys()):
            values = (list(json_object[key].values()))
            values.insert(0, int(key))
            values.append(False)
            array.append(values)
        return array

    # dictionary.update is used for create and edit, so this is used for add and edit
    def addEdit(self, item):
        self.exists()
        with open(FILEPATH, 'r') as openfile:
            json_object = json.load(openfile)

        json_object.update({str(item[0]): {
            "name": item[1],
            "tags": item[2],
            "voltage": item[3],
            "current": item[4],
            "power": item[5]
        }})
        json_write_object = json.dumps(json_object, indent=4)

        with open(FILEPATH, "w") as outfile:
            outfile.write(json_write_object)

    def delete(self, item):
        self.exists()
        with open(FILEPATH, 'r') as openfile:
            json_object = json.load(openfile)
        json_object.pop(str(item[0]))
        json_write_object = json.dumps(json_object, indent=4)

        with open(FILEPATH, "w") as outfile:
            outfile.write(json_write_object)

    def exists(self):
        if os.path.exists(FILEPATH) == False:
            # Data to be written
            dictionary = {}

            # Serializing json
            json_object = json.dumps(dictionary, indent=4)

            # Writing to sample.json
            with open(FILEPATH, "w") as outfile:
                outfile.write(json_object)
