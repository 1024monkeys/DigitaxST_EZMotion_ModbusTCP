#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

#  Purpose: Prove that we're able to control an Emerson drive via Ethernet using only
#python and pymodbus.  
#  The controller must be set to absolute positioning mode using pwoeTool Pro.  
#Other setting are required via PowerTools Pro as well, but you have to figure those
#settings out for yourself.  PowerTools Pro is a free download from Emerson. 
#
#When properly configured, this code accomplishes:
#--A postion of 100 will command the motor to turn in the 'positive' direction as if 
#to move 100 inches.  
#--A next command of 75 will command the motor to turn in the 'negative' direction as if 
#to move backwards 25 inches, to a position of 75 inches.
#--You are also able to specify the velocity and accellerations used.

# Setup:
#  Modify the default Drive setup as needed using PowerTools Pro.
#  Make a note of any base parameters that you want access to (this is unusual, look
#    these up in the User Guide).
#  Also in PowerTools Pro, setup Network->Parameter Access to include any EZ Motion 
#   parameters that you wish to access/modify.
#  Any paraeters that you wish to use/access must also be properly defined below.
#  You also need to know the 'Type' of parameter.  For base parameters, look in the manual.
#   For EZ Motion parametrs, look in Network->Parameter Access, and infer if each parameter is
#   16 or 32 bits.  32 bit paramters take up 2 Modbus address slots (and PowerTools Pro knows 
#   this when assigning in Network->Parameter Access).
#  Some parameters are floats, and are configured in PowerTools Pro for the number of implied decimal
#    places.  You can find these settings for Dist, Vel, Accel/Decel in Setup->User Units.

#Tested with a cleverly designed demo unit, from Emerson, constructed from a DS1201 drive with 
#EZMotion and SM-Ethernet Fieldbus options.  On Windows 10.

#Gripes:
# Emerson does not make available a spreadsheet with all of the modbus parameters.

#Please note:
#This code is designed to break, rather harshly, upon errors.  This may include, but is not limited to, 
# input from the user, broken communications, broken code.  Use this in an isolated testing environment only.
#If you use this code for actual machinery, then you are being really, really stupid.  People may get hurt.
# It will be your fault.

import os, time

Debug=False

from stdrv import STDrv
MY_DEFAULT_DRIVE_IP = '192.168.1.100'

#  'base' Paramters (Defined in the hardware of the Digitax ST Drive, see user guide).
#There are oodles of these.  Below is a subset of the ones that I want to access.
#  In addtion, EZ parameters are listed here as defined in PowerTools Pro.  These need 
#not be EZMotion paramaters, however this is the only way to expose EZMotion parameters 
#to the Ethernet Interface.
st_params = {
    'base':{
        'DriveEncoderRevolutionCounter':{'param':'03.28', 'type':'UInt'},
        'DriveEncoderPosition':         {'param':'03.29', 'type':'UInt'},
        'DriveEncoderFinePosition':     {'param':'03.30', 'type':'UInt'}
        },   #End of base parameters.  EZ Motion parameters below.
    #Grouped by section in PowerTools Pro
    'Index':{
        'IndexAnyCommandComplete':{'param':'18.02', 'type':'Int'}
        },
    'Index0':{
        'CommandComplete':  {'param':'18.03', 'type':'Int'},
        'CommandInProgress':{'param':'18.04', 'type':'Int'},
        'Dist':             {'param':'18.11', 'type':'Int32'},  #Drive setup so 1 rev = 1.0000 Inches in PowerTools {Inches]
        'Vel':              {'param':'18.13', 'type':'Int32'},  # [Inch/Minute]
        'Accel':            {'param':'18.15', 'type':'Int32'},  # [Inch/Minute/Second]
        'Decel':            {'param':'18.17', 'type':'Int32'},  # [Inch/Minute/Second]
        'Initiate':         {'param':'18.19', 'type':'Int'}
        },
    'Index1':{
        'CommandComplete':  {'param':'19.03', 'type':'Int'},
        'CommandInProgress':{'param':'19.04', 'type':'Int'},
        'Dist':             {'param':'19.11', 'type':'Int32'},  #Drive setup so 1 rev = 1.0000 Inches in PowerTools
        'Vel':              {'param':'19.13', 'type':'Int32'},
        'Accel':            {'param':'19.15', 'type':'Int32'},
        'Decel':            {'param':'19.17', 'type':'Int32'},
        'Initiate':         {'param':'19.19', 'type':'Int'}
        }
    }

#############################
# Low Level Functions
def write_myparam(drive, category, entry, value):
    return drive.write_param(st_params[category][entry]['param'], value, type=st_params[category][entry]['type'])
    
def read_myparam(drive, category, entry):
    return drive.read_param(st_params[category][entry]['param'], type=st_params[category][entry]['type'])


#############################
# Utilities
def convert_st_int_to_float(num, dec_places=4):
    num = float(num)/pow(10.0, dec_places)
    return num
    
def convert_float_to_st_int(num, dec_places=4):
    num = num * pow(10.0, dec_places)
    return int(num)

#############################
# Drive I/O Routines
def Start_Index(drive, idx_num=0):
    write_myparam(drive, 'Index'+str(idx_num), 'Initiate', 1)
    return
    
def Is_Index_Complete(drive, idx_num=0):
    result = read_myparam(drive, 'Index'+str(idx_num),'CommandComplete')  
    return result
    
def Get_Last_Move(drive, idx_num=0):
    global Debug
    dist=read_myparam(drive, 'Index'+str(idx_num),'Dist')
    if Debug:
        print("Get_Last_Move> Got from Controller dist=%s"%str(dist))
    dist = convert_st_int_to_float(dist)
    if Debug:
        print("Get_Last_Move> post convert dist=%s"%str(dist))
    
    vel=read_myparam(drive, 'Index'+str(idx_num),'Vel')
    #vel = convert_st_int_to_float(vel)
    
    accel=read_myparam(drive, 'Index'+str(idx_num),'Accel')
    #accel = convert_st_int_to_float(accel)
    return (dist, vel, accel)
    
def Set_Next_Move(drive, dist, vel, accel, idx_num=0):
    dist=write_myparam(drive, 'Index'+str(idx_num), 'Dist', convert_float_to_st_int(dist))
    vel=write_myparam(drive, 'Index'+str(idx_num), 'Vel', vel)
    #hardwiring decel = accel.  Probably a bad idea.  Deal with it later.
    decel=write_myparam(drive, 'Index'+str(idx_num), 'Decel', accel)
    accel=write_myparam(drive, 'Index'+str(idx_num), 'Accel', accel)
    return (dist, vel, accel)
    
def Wait_For_Index_Complete(drive, idx_num=0):
    ticker = "|/-\\"
    ticker_idx = 0
    print("Waiting for move complete...")
    while not Is_Index_Complete(drive, idx_num):
        print("\r%.4f [%s]"%(Get_Encoder_Postion(drive),ticker[ticker_idx])),
        ticker_idx = ticker_idx+1
        if ticker_idx > 3:
            ticker_idx = 0
        time.sleep(0.5)
    print("Move complete.")
    return
    
    #Returns new values for (Dist, Vel, Accel), or current values if skipped.
def Get_New_Pos_From_Input(drive, idx_num=0):
    (dist, vel, accel) = Get_Last_Move(drive, idx_num=idx_num)
    print("Last Position and Settings: Dist:%.4f, Vel:%d, Accel:%d"%(dist, vel, accel))
    ndist=raw_input("Enter new position, (or nothing to skip): ")
    if ndist:
        dist = float(ndist)
    nvel=raw_input("Enter new vel, (or nothing to skip): ")
    if nvel:
        vel = int(nvel)
    naccel=raw_input("Enter new accel, (or nothing to skip): ")
    if naccel:
        accel = int(naccel)
    return (dist, vel, accel)
    
    #Read in the revs counter, and add the fine position counter.  Results (at 1 Inch/rev, cheating here. see top) are in inches.
def Get_Encoder_Postion(drive):
    revs = read_myparam(drive, 'base','DriveEncoderRevolutionCounter')
    pos = read_myparam(drive, 'base','DriveEncoderPosition')
    pos = float(revs) + float(pos)/65535.0
    if Debug:
        print("Get_Encoder_Postion> revs: %s, pos: %s"%(str(revs), str(pos)))
    return pos

    
# main 
def main():
    data = 0
    x_axis = STDrv()
    x_axis.ip = MY_DEFAULT_DRIVE_IP
    print("Connecting to device at: %s"%str(x_axis.ip))
    
    x_axis.host = x_axis.ip
    x_axis.connect()
    x_axis.reset()
    while 1:
        print
        curr_pos = Get_Encoder_Postion(x_axis)
        #'AutoScan' is a separate device I was using to check positioning.  Ignore it.
        print("Current Position: %.2f (%d AutoScan Counts)"%(curr_pos, int(curr_pos*4000)))
        (dist, vel, accel) = Get_New_Pos_From_Input(x_axis)
        Set_Next_Move(x_axis, dist, vel, accel)

        print("Current Position: %.2f (%d AutoScan Counts)"%(curr_pos, int(curr_pos*4000)))
        Start_Index(x_axis)
        Wait_For_Index_Complete(x_axis)
        # Finished move.
    x_axis.close()
    del x_axis
    exit()

if __name__ == "__main__":
    main()

