#! /usr/bin/env python3
# Time-stamp: <2016-05-02 12:20:17 chrplr>

#    Python moddule to communicate with the BlackBox ToolKit v2
#    Copyright (C) 2014-2022  Christophe Pallier <christophe@pallier.org>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses

''' Interface with the Blackbox Toolkit version 2 (BBTKv2) ''' 

import serial
import time
import sys

DEBUG = True
CRLF = '\r\n'
WT = 0.100  # waiting time between writing commands (100 ms)

sensor_thresholds = { 'Mic1':63, 
                      'Mic2':63, 
                      'Sounder1': 63, 
                      'Sounder2':63, 
                      'Opto1':63, 
                      'Opto2':63, 
                      'Opto3':63, 
                      'Opto4':63}

class BlackBoxToolKit:
    def __init__(self):
        # TODO: read parameters from ini file 
        self.bbtk = serial.Serial(port='/dev/ttyACM0',
                                  baudrate=230400,
                                  bytesize=serial.EIGHTBITS, 
                                  parity=serial.PARITY_NONE, 
                                  stopbits=serial.STOPBITS_ONE,
                                  timeout=1,
                                  xonxoff=False, 
                                  rtscts=False,
                                  dsrdtr=False,
                                  writeTimeout=1)
        self.thresholds = sensor_thresholds

    def soft_reset(self):
        self.bbtk.sendBreak()

    def send_command(self, cmd):
        if (DEBUG):
            print('Sending: ' + cmd)
        self.bbtk.write((cmd + CRLF).encode())
        time.sleep(WT) 
        
    def get_response(self):
        time.sleep(WT)
        if (DEBUG):
            print('Waiting for response from BBTK...')
        s = ''
        c = self.bbtk.read()
        if (DEBUG):
            sys.stdout.write(c.decode())
        while c != ';':
            if c != '\n':
                s = s + c.decode()
            c = self.bbtk.read()
            if (DEBUG):
                sys.stdout.write(c.decode())
        if (DEBUG):
                sys.stdout.write('\n')
        return(s)

    def connect(self):
        self.soft_reset()
        self.send_command('CONN')
        resp = self.get_response()
        if resp != 'BBTK':
            raise Exception('Cannot connect to BBTK ')
        time.sleep(1)  # wait for 1 s

    def disconnect(self):
        self.bbtk.close()

    def get_firmware_version(self):
        self.send_command('FIRM')
        return self.get_response()

    def display_info_on_bbtk(self):
        self.send_command('ABOU')
        time.sleep(2)

    def set_smoothing_off(self):
        self.send_command('SMOO')
        self.send_command('00000011')
        self.get_response()

    def set_smoothing_on(self):
        self.send_command('SMOO')
        self.send_command('11111111')
        self.get_response()        

    def set_sensor_thresholds(self, thresholds=None):
        self.send_command("SEPV")
        if thresholds == None:
            thresholds = self.thresholds
        for val in thresholds.values():
            self.send_command(str(val))
        self.get_response()
    
    def is_alive(self):
        self.send_command('ECHO')
        return self.bbtk.read(4) == 'ECHO'
    
    def flush(self):
        self.send_command('FLUS')
        time.sleep(2)

    def get_sensor_thresholds(self):
        self.send_command('GEPV')
        resp = self.get_response()
        vals = map(int, resp.split(','))
        return { 'Mic1': vals[0], 
                 'Mic2': vals[1], 
                 'Sounder1':  vals[2], 
                 'Sounder2': vals[3], 
                 'Opto1': vals[4], 
                 'Opto2': vals[5], 
                 'Opto3': vals[6], 
                 'Opto4': vals[7]}

    def clear_timing_data(self):
        self.send_command('SPIE')
        s1 = self.get_response()
        s2 = self.get_response()
        time.sleep(2)

    def digital_stimulus_capture(self, duration=5):
        self.clear_timing_data()
        self.send_command('DSCM')
        self.send_command('TIML')
        self.send_command(str(duration*1000000))
        self.send_command('RUDS')
        
        s = self.get_response()
        if s != 'SDAT':
            raise Exception('Not receiving data from the BBTK')
        nevents = int(self.get_response())
        runtime = int(self.get_response())
        nsamples = int(self.get_response())
        lines = []
        timestamp = []
        for i in range(nevents):
            ev = self.get_response()
            lines.append(ev[:12])
            timestamp.append(ev[20:])
        return nevents
            
        

def test_acquisition():
    bb = BlackBoxToolKit()
    bb.connect()
    bb.display_info_on_bbtk()
    #bb.set_sensor_thresholds()
    bb.clear_timing_data()
    nevents = bb.digital_stimulus_capture(5)
    print("%d events detected" % nevents )
    bb.disconnect()


if __name__ == '__main__':
    test_acquisition()
    
