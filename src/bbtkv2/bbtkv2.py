# Time-stamp: <2022-04-19 10:04:14 christophe@pallier.org>

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
"""Interface to the Blackbox Toolkit version 2 (BBTKv2)

The **BlackBox ToolKit v2** is a device that allows psychologists to
accurately measure the timing of audio-visual stimuli (see
https://www.blackboxtoolkit.com/bbtkv2.html).

The device communicates via a serial protocol over USB. The present
module encapsulates (most of) the commands described in the *API
Guide* allowing to control the BBTKv2.

"""

import serial
import time
import sys
import re
import pandas as pd
import toml

##############################################################################

DEFAULT_CONFIG = """
serialport="/dev/ttyACM0"
baudrate=230400
debug=1

[sensor_thresholds]
Mic1=63
Mic2=63
Sounder1=63
Sounder2=63
Opto1=110
Opto2=110
Opto3=110
Opto4=110

[smoothing]
smoothing='11000011'
"""

INPUT_PORT_NAMES = ('Keypad4', 'Keypad3', 'Keypad2', 'Keypad1', 'Opto4',
                    'Opto3', 'Opto2', 'Opto1', 'TTLin2', 'TTLin1', 'Mic2',
                    'Mic1')

OUTPUT_PORT_NAMES = ('ActClose4', 'ActClose3', 'ActClose2', 'ActClose1',
                     'TTLout2', 'TTLout1', 'Sounder2', 'Sounder1')

DSC_LINE_NAMES = ['timestamp'] + \
                 list(INPUT_PORT_NAMES) + \
                 list(OUTPUT_PORT_NAMES)

###############################################################################

CRLF = '\r\n'
WT = 0.05  # waiting time (50 ms) between writes on serial port

###############################################################################

## Fonctions to parse the outputs of the bbtkv2 commands

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


def inp_port_mask12_to_series(mask12):
    assert type(mask12) is str
    assert len(mask12) == 12
    return pd.Series([int(b) for b in mask12], index=INPUT_PORT_NAMES)


def out_port_mask8_to_series(mask8):
    assert type(mask8) is str
    assert len(mask8) == 8
    return pd.Series([int(b) for b in mask8], index=OUTPUT_PORT_NAMES)


def dsc_output_to_dataframe(text):
    """convert the fixed record output format of the DSCM command to a pandas dataframe.

    :param text: string containing ';' separated lines with 32 digits.

    :return: a dataframe with 21 columns: time-stamp (in milliseconds) 
             followed by twenty bit values representing the states of the input/output ports.
    """
    
    all_events = []
    for row in text.split(';'):
        line = row.strip()
        if len(line) == 32:
            time_stamp = int(line[20:]) / 1000.0  # convert to msec
            all_events.append([time_stamp] + [int(b) for b in line[:20]])

    return pd.DataFrame(all_events, columns=DSC_LINE_NAMES)


class BlackBoxToolKit:
    """Interface to a [BlackBox ToolKit v2 device](https://www.blackboxtoolkit.com/bbtkv2.html).
    """
    def __init__(self, config_file=None, config_string=None):
        """Open the serial port associated to the BBTKv2 and sets the input sensor_thresholds.

        :param config_file: filename of a toml file containing the configuration.

        Example of a ``bbtkv2.toml`` configuration file:

        .. code-block:: TOML
        
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

             [smoothing]
             smoothing='11000011'

        :param config_string: parameters listed in a string respecting toml syntax

        """
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

        self.connect()
        self.set_sensor_thresholds(self.settings['sensor_thresholds'])
        self.set_smoothing(self.settings['smoothing']['smoothing'])
     
    def get_current_settings(self):
        """Get the settings stored in the bbtkv2 object (not on the BBTKv2 device!).
       
        :return: a dist containing the parameters and their values.
        """
        return self.settings

    def set_debug_on(self):
        """When debug is 'on', the input/output messages on the serial port are printed on the console."""
        self.settings['debug'] = 1
       
    def set_debug_off(self):
        """When debug is 'off', keep quiet."""
        self.settings['debug'] = 0

    def read_settings_from_toml_file(self, config_file):
        """Read settings from a file and apply them.

        :param config_file: filename of a toml file containing the configuration.

        Example of a ``bbtkv2.toml`` configuration file:

        .. code-block:: TOML
       
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

             [smoothing]
             smoothing='11000011'
        """
        self.settings = toml.load(config_file)
       
    def connect(self):
        """Initiate a connection to the BBTKv2.
        """
        self.send_break()
        self.send_command('CONN')
        resp = self.read_line()
        if resp != 'BBTK;':
            raise Exception('Cannot connect to BBTK ')
        time.sleep(1)  # wait for 1 s

    def send_break(self):
        """Send a break to the BBTK, requiring it to perform a soft reset.
        """
        if (self.debug):
            print('Sending a break to the BBTK')
        self.bbtk.sendBreak()

    def disconnect(self):
        """Close the serial connection to the BBTKv2.
        """
        self.bbtk.close()

    def is_alive(self):
        """Check if the BBTKv2 is responsive.
        """
        self.send_command('ECHO')
        return self.read_line() == 'ECHO'

    def flush(self):
        """Flush the USB buffer.
        """
        self.send_command('FLUS')
        time.sleep(2)

    def send_command(self, cmd):
        """write ``cmd`` on the serial port, then send a CR+LF.

        :param cmd: command to send
        :type cmd: string
        """
        if self.debug:
            print('Sending: ' + cmd)
        self.bbtk.write((cmd + CRLF).encode())
        time.sleep(WT)

    def get_response(self, timeout=10):
        """Accumulates characters from the serial channel, for a certain duration.

        :param timeout: time during which to wait for messages from the bbtkv2.

        :return:  the text sent by the BBTLv2.
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
        """Read a single line from the bbtkv2 (blocking! No timeout)
      
        :return: the string of characters.
        """
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
        return (s)

    def get_firmware_version(self):
        self.send_command('FIRM')
        return self.read_line()

    def display_info_on_bbtk_display(self):
        self.send_command('ABOU')
        time.sleep(2)

    def set_smoothing(self, mask):
        """Set smoothing to Opto and Mic sensors.
        
        * When smoothin is 'off', you will detect *all* leading edges, e.g.
        each refresh on a CRT.
        * When smoothing is 'on', you need to subtract 20ms from offset times.

        :param mask: a 8 binary mask ``Mic1:Mic2:Opto4:Opto3:Opto2:Opto1:NA:NA``
        
        :type mask: str
        """
        self.send_command('SMOO')
        self.send_command(mask)
        time.sleep(1)
        #return self.is_alive()

    # TODO: implement fine grained manipulation of smoothing bits
    # def set_crt_smoothing(self):
    #     self.smothing
    #     self.send_command('SMOO')
    #     self.send_command('00111111')
    #     return self.is_alive()

    # def unset_crt_smoothing(self):
    #     self.send_command('SMOO')
    #     self.send_command('00000011')
    #     return self.is_alive()

    # def set_mic_smoothing(self):
    #     self.send_command('SMOO')
    #     self.send_command('11000011')
    #     return self.is_alive()

    # def unset_mic_smoothing(self):
    #     self.send_command('SMOO')
    #     self.send_command('00000011')
    #     return self.is_alive()

    def set_sensor_thresholds(self, thresholds=None):
        """Send thresholds to the BBTKv2.

        :param thresholds: dictionary {sensor_name: value (int between 0 and 127)}

        :return: bool (True=the bbtk is alive; False: somehting wrong occurred, check.)
        """
        if thresholds is None:
            thresholds = self.settings['sensor_thresholds']
            
        self.send_command("SEPV")
        self.send_command(str(thresholds['Mic1']))
        self.send_command(str(thresholds['Mic2']))
        self.send_command(str(thresholds['Sounder1']))
        self.send_command(str(thresholds['Sounder2']))
        self.send_command(str(thresholds['Opto1']))
        self.send_command(str(thresholds['Opto2']))
        self.send_command(str(thresholds['Opto3']))
        self.send_command(str(thresholds['Opto4']))
        time.sleep(1)
        return self.is_alive()

    def get_sensor_thresholds(self):
        """Read the values of the 8 input sensor thresholds.

        :return: a dict {sensor_name: value (int between 0 and 127)} 
        """
        self.send_command('GEPV')
        resp = self.read_line()
        vals = [int(x) for x in re.findall('\d+', resp)]
        levels = {
            'Mic1': vals[0],
            'Mic2': vals[1],
            'Sounder1': vals[2],
            'Sounder2': vals[3],
            'Opto1': vals[4],
            'Opto2': vals[5],
            'Opto3': vals[6],
            'Opto4': vals[7]
        }
        self.settings['sensor_thresholds'] = levels
        return levels

    def adjust_sensors_levels(self):
        self.send_command('AJPV')
        response = ''
        while response != 'Done;':
            response = self.read_line()
        self.get_sensor_thresholds()

    def clear_timing_data(self):
        self.send_command('SPIE')
        s1 = self.read_line()
        s2 = self.read_line()
        time.sleep(2)

    def input_line_check(self, duration=5):
        """Detect events on the input line and print them.
        
        :param duration: duration before sending soft break, in s
        :type duration: int

        :return: None
        """
        self.send_break()
        self.send_command('ICHK')
        start_time = time.time()
        while time.time() - start_time < duration:
            resp = self.read_line()
            print(resp)
        self.send_break()

    def output_lines_check(self, mask):
        """Send a pattern to the 8 output lines ('ActClose4', 'ActClose3', 'ActClose2', 'ActClose1',
        'TTLout2', 'TTLout1', 'Sounder2', 'Sounder1').

        :param mask: 8 bits mask
        :type mask: str
        
        :return: None
        
        To interrupt a sounder, set its bit to 0 or call ``send_break()``

        """
        self.send_command('OCHK')
        self.send_command(mask)


    def digital_stimulus_capture(self, duration=30):
        """Launches a digital data capture session.

        :param duration:  duration of acquisition in seconds
        :type duration: int

        :return: a dataframe listing the events
        """
        self.clear_timing_data()
        self.send_command('DSCM')
        self.send_command('TIML')
        self.send_command(str(duration * 1000000))
        self.send_command('RUDS')
        time.sleep(duration)
        text = self.get_response(5)
        return dsc_output_to_dataframe(text)

    def event_generation_pulse_train(self,
                                     timings=[
                                         '100,1000,00000001',
                                         '100,1000,00000000'
                                     ]):
        self.send_break()
        time.sleep(.5)
        self.send_command('PRPT')
        self.send_command('TIML')
        self.send_command('0')
        for row in timings:
            self.send_command(row)

        self.send_command('PCPT')
        self.send_command('RUPT')
        # now the program will run until a break is sent to the bbtkv2


def test_acquisition():
    bb = BlackBoxToolKit()
    time.sleep(1)
    events = bb.digital_stimulus_capture(30)
    print(events)
    events.to_csv('stimulus_capture_test.csv')


if __name__ == '__main__':
    test_acquisition()
