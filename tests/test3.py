import json

FILEPATH = "data.json"
startEnergy = 1099

with open(FILEPATH, 'r') as openfile:
    json_object = json.load(openfile)
array = []
for key in list(json_object.keys()):
    values = (list(json_object[key].values()))
    print("("+str(values[0])+","+str(400-(values[3]-startEnergy))+"),")