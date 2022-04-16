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
import pandas as pd

DEBUG = True
CRLF = '\r\n'
WT = 0.100  # waiting time between writing commands (100 ms)

sensor_thresholds = {'Mic1': 63,
                     'Mic2': 63,
                     'Sounder1': 63,
                     'Sounder2': 63,
                     'Opto1': 63,
                     'Opto2': 63,
                     'Opto3': 63,
                     'Opto4': 63}


input_port_names = ('Keypad4', 'Keypad3', 'Keypad2', 'Keypad4',
                    'Opto4', 'Opto3', 'Opto2', 'Opto1',
                    'TTLin2', 'TTLin1', 'Mic2', 'Mic1')

output_port_names = ('ActClose4', 'ActClose3', 'ActClose2', 'ActClose1',
                     'TTLout2', 'TTLout1', 'Sounder2', 'Sounder1')


def inp_port_mask12_to_series(mask12):
    assert type(mask12) is str
    assert len(mask12) == 12
    return pd.Series([int(b) for b in mask12], index=input_port_names)


def out_port_mask8_to_series(mask8):
    assert type(mask8) is str
    assert len(mask8) == 8
    return pd.Series([int(b) for b in mask8], index=output_port_names)


def dsc_mask32_to_series(mask32):
    assert type(mask32) is str
    assert len(mask32) == 32

    inputs = mask32[:12]
    outputs = mask32[12:20]
    time_stamp = int(mask32[20:]) / 1000.0
    #TODO: make it a pd.Series!
    return [time_stamp, inp_port_mask12_to_series(inputs), out_port_mask8_to_series(outputs)]

# a = '11001100110001010101000123456789'
# bbtkv2.dsc_mask32_to_series(a)

# [123456.789,
#  Keypad4    1
#  Keypad3    1
#  Keypad2    0
#  Keypad4    0
#  Opto4      1
#  Opto3      1
#  Opto2      0
#  Opto1      0
#  TTLin2     1
#  TTLin1     1
#  Mic2       0
#  Mic1       0
#  dtype: int64,
#  ActClose4    0
#  ActClose3    1
#  ActClose2    0
#  ActClose1    1
#  TTLout2      0
#  TTLout1      1
#  Sounder2     0
#  Sounder1     1
#  dtype: int64]


class BlackBoxToolKit:
    def __init__(self, port='/dev/ttyACM0', baudrate=230400):
        # TODO: read parameters from ini file
        self.bbtk = serial.Serial(port=port,
                                  baudrate=baudrate,
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

    def getresponse(self):   # does not stop !!!
        while (self.bbtk.is_open):
            # Check if incoming bytes are waiting to be read from the serial input
            # buffer.
            if (self.bbtk.in_waiting > 0):
                # read the bytes and convert from binary array to ASCII
                data_str = self.bbtk.read(self.bbtk.in_waiting).decode('ascii')
                # print the incoming string without putting a new-line
                # ('\n') automatically after every print()
                print(data_str, end='')

            # Put the rest of your code you want here

            # Optional, but recommended: sleep 10 ms (0.01 sec) once per loop to let
            # other thr
            time.sleep(0.01)


    def read_line(self):
        """ accumulates characters from serial channel until a '\n' is reached.
            Returns the string of characters.
        """
        # TODO: this is currenlty blocking on input :(
        time.sleep(WT)
        if (DEBUG):
            print('Waiting for response from BBTK...')
        s = ''
        c = self.bbtk.read().decode('ascii')
        if (DEBUG):
            sys.stdout.write(c)
        # while c != ';':
        while c != '\n':
            if c != '\n':
                s = s + c
            c = self.bbtk.read().decode()
            if (DEBUG):
                sys.stdout.write(c)
        if (DEBUG):
            sys.stdout.write('\n')
        return(s)

    def connect(self):
        self.soft_reset()
        self.send_command('CONN')
        resp = self.read_line()
        if resp != 'BBTK;':
            raise Exception('Cannot connect to BBTK ')
        time.sleep(1)  # wait for 1 s

    def disconnect(self):
        self.bbtk.close()

    def get_firmware_version(self):
        self.send_command('FIRM')
        return self.read_line()

    def display_info_on_bbtk(self):
        self.send_command('ABOU')
        time.sleep(2)

    def set_smoothing_off(self):
        self.send_command('SMOO')
        self.send_command('00000011')
        self.read_line()

    def set_smoothing_on(self):
        self.send_command('SMOO')
        self.send_command('11111111')
        self.read_line()

    def set_sensor_thresholds(self, thresholds=None):
        self.send_command("SEPV")
        if thresholds is None:
            thresholds = self.thresholds
        for val in thresholds.values():
            self.send_command(str(val))
        self.read_line()

    def is_alive(self):
        self.send_command('ECHO')
        return self.bbtk.read(4) == 'ECHO'

    def flush(self):
        self.send_command('FLUS')
        time.sleep(2)

    def get_sensor_thresholds(self):
        self.send_command('GEPV')
        resp = self.read_line()
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
        s1 = self.read_line()
        s2 = self.read_line()
        time.sleep(2)

    def input_line_check(self, duration=5):
        self.soft_reset()
        self.send_command('ICHK')
        start_time = time.time()
        while time.time() - start_time < duration:
            resp = self.read_line()
            print(resp)
        self.soft_reset()

    def digital_stimulus_capture(self, duration=5):
        self.clear_timing_data()
        self.send_command('DSCM')
        self.send_command('TIML')
        self.send_command(str(duration*1000000))
        self.send_command('RUDS')

        s = self.read_line()
        if s != 'SDAT':
            raise Exception('Not receiving data from the BBTK')
        nevents = int(self.read_line())
        runtime = int(self.read_line())
        nsamples = int(self.read_line())
        lines = []
        timestamp = []
        for i in range(nevents):
            ev = self.read_line()
            lines.append(ev[:12])
            timestamp.append(ev[20:])
        return nevents



def test_acquisition():
    bb = BlackBoxToolKit()
    bb.connect()
    bb.display_info_on_bbtk()
    bb.set_sensor_thresholds()
    bb.clear_timing_data()
    nevents = bb.digital_stimulus_capture(5)
    print("%d events detected" % nevents )
    bb.disconnect()


if __name__ == '__main__':
    test_acquisition()
