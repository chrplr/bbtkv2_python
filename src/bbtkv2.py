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
import toml

##############################################################################

DEFAULT_CONFIG = """
serialport="/dev/ttyACM0"
baudrate=230400
debug=1

[sensor_thresholds]
Mic1=0
Mic2=0
Sounder1=0
Sounder2=0
Opto1=110
Opto2=110
Opto3=110
Opto4=110
"""

INPUT_PORT_NAMES = ('Keypad4', 'Keypad3', 'Keypad2', 'Keypad1',
                    'Opto4', 'Opto3', 'Opto2', 'Opto1',
                    'TTLin2', 'TTLin1', 'Mic2', 'Mic1')

OUTPUT_PORT_NAMES = ('ActClose4', 'ActClose3', 'ActClose2', 'ActClose1',
                     'TTLout2', 'TTLout1', 'Sounder2', 'Sounder1')

DSC_LINE_NAMES = ['timestamp'] + \
                 list(INPUT_PORT_NAMES) + \
                 list(OUTPUT_PORT_NAMES)

###############################################################################

CRLF = '\r\n'
WT = 0.05  # waiting time (50 ms) between writes on serial port 

###############################################################################


def inp_port_mask12_to_series(mask12):
    assert type(mask12) is str
    assert len(mask12) == 12
    return pd.Series([int(b) for b in mask12], index=INPUT_PORT_NAMES)


def out_port_mask8_to_series(mask8):
    assert type(mask8) is str
    assert len(mask8) == 8
    return pd.Series([int(b) for b in mask8], index=OUTPUT_PORT_NAMES)


def dsc_mask32_to_list(mask32):
    assert type(mask32) is str
    assert len(mask32) == 32
    # the time-stamp (in microsec) is stored as the last 12 digits
    time_stamp = int(mask32[20:]) / 1000.0  # convert to msec
    return [time_stamp] + [int(b) for b in mask32[:20]]


DSC_OUTPUT_EXAMPLE = """
SDAT;
3;
30000000;
120000;
11001100110001010101000000123456;
01001100110001010101000000234567;
11001100110001010101000000345678;
EDAT;
"""


def dsc_output_to_dataframe(text):
    all_events = []
    for row in text.split(';'):
        line = row.strip()
        if len(line) == 32:
            all_events.append(dsc_mask32_to_list(line))
    df = pd.DataFrame(all_events, columns=DSC_LINE_NAMES)
    return df


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
    def __init__(self, config_file=None, config_string=None):
        """ Read configuration and opens the serial port associated to the bbtk. """
        if config_file is not None:
            self.settings = toml.load(config_file)
        elif config_string is not None:
            self.settings = toml.loads(config_string)
        else:
            self.settings = toml.loads(DEFAULT_CONFIG)

        self.debug = self.settings['debug'] == 1

        if self.debug:
            print("** BBTK Settings:\n\n", toml.dumps(self.settings))

        self.bbtk = serial.Serial(port=self.settings['serialport'],
                                  baudrate=self.settings['baudrate'],
                                  bytesize=serial.EIGHTBITS,
                                  parity=serial.PARITY_NONE,
                                  stopbits=serial.STOPBITS_ONE,
                                  timeout=1,
                                  xonxoff=False,
                                  rtscts=False,
                                  dsrdtr=False,
                                  writeTimeout=1)
      
        self.thresholds = self.settings['sensor_thresholds']
        self.connect()
        self.set_sensor_thresholds()
        
    def get_current_settings(self):
        return self.settings

    def read_thresholds_from_toml_file(self, filename):
        settings = toml.load(filename)
        self.thresholds = settings['sensor_thresholds']

    def soft_reset(self):
        if (self.debug):
            print('Sending a soft break to the BBTK')
        self.bbtk.sendBreak()

    def send_command(self, cmd):
        if self.debug:
            print('Sending: ' + cmd)
        self.bbtk.write((cmd + CRLF).encode())
        time.sleep(WT)

    def get_response(self, timeout=10):
        """ accumulates characters from serial channel.
            Returns the string of characters.
        """
        start_time = time.time()
        data_str = ""
        while (self.bbtk.is_open and ((time.time() - start_time) < timeout)):
            if (self.bbtk.in_waiting > 0):
                chars = self.bbtk.read(self.bbtk.in_waiting).decode('ascii')
                data_str += chars
                if self.debug:
                    print(chars, end='')
            time.sleep(0.05)

        return data_str

    def read_line(self):
        """ accumulates characters from serial channel until a '\n' is reached.
            Returns the string of characters.
        """
        # TODO: this is currenlty blocking on input :(
        time.sleep(WT)
        if (self.debug):
            print('Waiting for response from BBTK...')
        s = ''
        c = self.bbtk.read().decode('ascii')
        if (self.debug):
            sys.stdout.write(c)
        # while c != ';':
        while c != '\n':
            if c != '\n':
                s = s + c
            c = self.bbtk.read().decode()
            if (self.debug):
                sys.stdout.write(c)
        if (self.debug):
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

    def is_alive(self):
        self.send_command('ECHO')
        return self.read_line() == 'ECHO'
        
    def set_smoothing_off(self):
        self.send_command('SMOO')
        self.send_command('00000011')
        return self.is_alive()

    def set_smoothing_on(self):
        self.send_command('SMOO')
        self.send_command('11111111')
        return self.is_alive()
    
    def set_sensor_thresholds(self, thresholds=None):
        self.send_command("SEPV")
        if thresholds is None:
            thresholds = self.thresholds
        for val in thresholds.values():
            self.send_command(str(val))
        return self.is_alive()

    def flush(self):
        self.send_command('FLUS')
        time.sleep(2)

    def get_sensor_thresholds(self):
        self.send_command('GEPV')
        resp = self.read_line()
        vals = [int(s) for s in resp.split(',')]
        return {'Mic1': vals[0],
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
        self.soft_reset()

    def digital_stimulus_capture(self, duration=30):
        self.clear_timing_data()
        self.send_command('DSCM')
        self.send_command('TIML')
        self.send_command(str(duration*1000000))
        self.send_command('RUDS')
        time.sleep(duration)
        text = self.get_response(5)
        return dsc_output_to_dataframe(text)


def test_acquisition():
    bb = BlackBoxToolKit()
    events = bb.digital_stimulus_capture(30)
    print(events)
    bb.disconnect()

    
if __name__ == '__main__':
    test_acquisition()
