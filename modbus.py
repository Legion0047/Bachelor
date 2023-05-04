from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import pause
from datetime import datetime
import json

class modbus():

    def connect(self):
        client = ModbusClient(method='RTU', port='/dev/ttyUSB0', timeout=1, baudrate=9600, stopbits=2, bytesize=8,
                              parity='N')

        if not client.connect():
            print("unable to connect")
            exit(-1)
        return client

    def readCharge(self, client):

        data = client.read_input_registers(0, 6)
        dataDecoder = BinaryPayloadDecoder.fromRegisters(data.registers, byteorder=Endian.Big,
                                                         wordorder=Endian.Little)
        voltage = dataDecoder.decode_16bit_int() / 100
        current = dataDecoder.decode_16bit_int() / 100
        power = dataDecoder.decode_32bit_int() / 10
        return [voltage, current, power]