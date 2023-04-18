from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import pause
from datetime import datetime
import json

client = ModbusClient(method='RTU', port='/dev/ttyUSB0', timeout=1, baudrate=9600, stopbits=2, bytesize=8, parity='N')
saveData = []
toggle = True

if not client.connect():
    print("unable to connect")
    exit(-1)

start = datetime.today()

pause.until(datetime(start.year, start.month, start.day, start.hour, start.minute+1, 0))
now = start
# run for 8 hours = 480 minutes = 960 checks
for i in range(0, 960):
    if toggle:
        pause.until(datetime(now.year, now.month, now.day, now.hour, now.minute, now.second+30))
        toggle = False
    else:
        pause.until(datetime(now.year, now.month, now.day, now.hour, now.minute+1, now.second))
        toggle = True

    data = client.read_input_registers(0, 6)
    dataDecoder = BinaryPayloadDecoder.fromRegisters(data.registers, byteorder=Endian.Big, wordorder=Endian.Little)
    voltage = dataDecoder.decode_16bit_int() / 100
    current = dataDecoder.decode_16bit_int() / 100
    power = dataDecoder.decode_32bit_int() / 10
    saveData.append([i, voltage, current, power])
    print("Step "+i+" out of 960 done.")
    now = datetime.today()

json_object = {}
for entry in saveData:
    json_object.update({entry[0]: {
        "voltage": entry[1],
        "current": entry[2],
        "power": entry[3]
    }})
json_write_object = json.dumps(json_object, indent=4)
with open("data.json", "w") as outfile:
    outfile.write(json_write_object)

print("Programm finished, please shut me down.")