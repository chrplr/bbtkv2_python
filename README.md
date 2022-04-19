<p align="center">

![](docs/images/bbtkv2.png)

</p>

The [BlackBox ToolKit v2](https://www.blackboxtoolkit.com/bbtkv2.html) is a device that allows psychologists to accurately measure the timing of audio-visual stimuli.

The BBTKv2 communicates via a serial protocol over USB. The _bbtkv2_ python module provided here encapsualtes (some of) the commands described in the _API Guide_. 
In a nutshell:

    from bbtkv2 import BlackBokToolKit

    bb = BlackBoxToolKit()
    df = bb.digital_stimulus_capture(30)  # run capture for 30s
    print(df)  # print a dataframe containing all recorded events


# Documentation

Check <https://bbtkv2.readthedocs.io/en/latest/intro.html>


# Installation

    pip install bbtkv2

---

Christophe@Pallier.org



