# -*- coding: iso-8859-1 -*-
#! /usr/bin/env python

#Class structure and divine inspiration from:
# https://github.com/astroufsc/chimera
# Thanks!

#Things learned about Emerson Digitax Drives:
# --Extended data types are not probably implemented.
# --All values should be sent as a series of Ints
# --Yes, for a parameter of '11.12', the transmitted address should be 1111 (ala, Parameter-1)
# --No matter what the datasheet says, data transmission is 'Little Endian' (at least from pymodbus' view)

import time #for drive 'reset()' support.

Debug = False
#Pymodbus available here:
# https://pypi.python.org/pypi/pymodbus
#Installs easily with 'pip install pymodbus'
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants   import Endian
from pymodbus.payload     import BinaryPayloadDecoder
from pymodbus.payload     import BinaryPayloadBuilder

class STDrv(ModbusTcpClient):
   # You have to have Pymodbus module previously installed for this driver work properly.
    ip = '192.168.1.100'  #change to the corresponding ip number for your network.
    module_codes = {
        0:'No Module Fitted  ',
        101:'SM-Resolver Position Feedback  ',
        102:'SM-Universal Encoder Plus Position Feedback',
        103:'SM-SLM Position Feedback  ',
        104:'SM-Encoder Plus Position Feedback ',
        201:'SM-I/O Plus I/O Expansion ',
        206:'SM-I/O 120V I/O Expansion ',
        208:'SM-I/O 32 I/O Expansion ',
        301:'SM-Applications Applications   ',
        302:'SM-Applications Lite Applications  ',
        303:'SM-EZMotion Applications   ',
        304:'SM-Applications Plus Applications  ',
        401:'reserved Fieldbus   ',
        402:'reserved Fieldbus   ',
        403:'SM-Profibus DP Fieldbus  ',
        404:'SM-INTERBUS Fieldbus   ',
        405:'reserved Fieldbus   ',
        406:'SM-CAN Fieldbus   ',
        407:'SM-DeviceNet Fieldbus   ',
        408:'SM-CANopen Fieldbus   ',
        410:'SM-Ethernet Fieldbus   '
        }
    
    ###################################################
    # Low-Level Functions
    
    def read_param(self, param, type='Int', string_length=1, unit=1):
        global Debug
        if (Debug):
            print("read_param> param: %s, type: %s, sl: %d, unit: %d"%(param, type, string_length, unit))
        #gets a string in the format 'xx.xx' and converts it to a mapped
        #address and returns its contents
        param_menu = param.split('.')[0]
        param_param = param.split('.')[1]
        address = int(param_menu) * 100 + int(param_param) - 1
        if (type=='Int'):
            size = 1
        elif (type=='UInt'):
            size = 1
        elif (type=='Float32'):
            size = 2
        elif (type=='Int32'):
            size = 2
        elif (type=='UInt32'):
            size = 2
        elif (type=='Float64'):
            size = 4
        elif (type=='Int64'):
            size = 4
        elif (type=='UInt64'):
            size = 4
        elif (type=='Int8'):
            size = 1
        elif (type=='UInt8'):
            size = 1
        elif (type=='Bits'):
            size = 1
        elif (type=='String'):
            # Parameters size – The size of the string to decode
            size = string_length
        else :
            print("No implementation available for type of: %s"%type)
            return
        result = self.read_holding_registers(address, size, unit=unit)
        
        decoder = BinaryPayloadDecoder.fromRegisters(result.registers, endian=Endian.Little)
        if type=='Int':
            output = decoder.decode_16bit_int()
        elif type=='UInt':
            output = decoder.decode_16bit_uint()
        elif type=='Float32':
            output = decoder.decode_32bit_float()
        elif type=='Int32':
            output = decoder.decode_32bit_int()
        elif type=='UInt32':
            output = decoder.decode_32bit_uint()
        elif type=='Float64':
            output = decoder.decode_64bit_float()
        elif type=='Int64':
            output = decoder.decode_64bit_int()
        elif type=='UInt64':
            output = decoder.decode_64bit_uint()
        elif type=='Int8':
            output = decoder.decode_8bit_int()
        elif type=='UInt8':
            output = decoder.decode_8bit_uint()
        elif type=='Bits':
            output = decoder.decode_bits()
        # Parameters size – The size of the string to decode
        elif type=='String':
            output = decoder.decode_string(size=string_length)
        else :
            output = "No implementation available for type of: %s"%type
        if (Debug):
            print("read_param> %s"%str(output))
        #return result.registers[0]
        return output

    def write_param(self, param, value, type='Int', unit=1):
        global Debug
        #gets a string in the format 'xx.xx' and converts it to an mapped
        #address and writes the value to it
        param_menu = param.split('.')[0]
        param_param = param.split('.')[1]
        address = int(param_menu) * 100 + int(param_param) - 1
        if (Debug):
                print("write_param> Add: %s, Val: %s, Type: %s, Unit: %s"%(str(address+1), str(value),str(type), str(unit)))
            
        #Different type support available via pymodbus:
        # add_16bit_int(value)
        # add_16bit_uint(value)
        # add_32bit_float(value)
        # add_32bit_int(value)
        # add_32bit_uint(value)
        # add_64bit_float(value)
        # add_64bit_int(value)
        # add_64bit_uint(value)
        # add_8bit_int(value)
        # add_8bit_uint(value)
        # add_bits(values)
        # add_string(value)
        if (type=='Int'):
            #'Int' is native type, no processing needed
            rq = self.write_register(address, value, unit=unit)
        elif (type=='Int32'):
            builder = BinaryPayloadBuilder(endian=Endian.Little)
            builder.add_32bit_int(value)
            payload = builder.to_registers()
            rq = self.write_registers(address, payload, unit=unit)
        else:
            rq = 0
            if (Debug):
                print("write_param> Type: %s not supported by Emerson Digitax, or not supported here yet."%str(type))
        if (Debug):
                print("write_param> rq: %s"%str(rq))
        return rq
        
    ###################################################
    # Potentially useful activities
    
    def Report_Slots(self, unit=1):
        #Slot info are in params 15.01, 16.01, and 17.01
        for idx in range(3):
            my_param = '1'+str(5+idx)+'.01'
            my_slot = idx +1
            code = int(self.read_param(my_param, unit=unit))
            print("Getting Slot %d Code: %d"%(my_slot,code))
            if code in self.module_codes:
                print("Module is: %s"%self.module_codes[code])
            else:
                print("Unknown Module.")
            print
        return
        
    #readlist should be a list of ['parameter', 'name'], where 'parameter' is in the form of '12.23'
    def read_this_parameter_list(self, readlist, unit=1):
        s = ""
        for param in sorted(readlist):
            s = s +"Current Setting for %s (%s): %s\n"%(param, readlist[param], str(self.read_param(param, unit=unit)))
        return s

    def reset(self, unit=1):
        #remotely resets the controller
        if self.write_param('10.33', 1, unit=unit):  # drive reset
            time.sleep(1)  # necessary delay to force logical reset level high during 1 second
            if self.write_param('10.33', 0, unit=unit):
                return True
        return False
