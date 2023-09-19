<p align="center">

![](docs/images/bbtkv2.png)

</p>

The [BlackBox ToolKit v2](https://www.blackboxtoolkit.com/bbtkv2.html) is a device that allows psychologists to accurately measure the timing of audio-visual stimuli.

The BBTKv2 communicates via a serial protocol over USB. The _bbtkv2_ python module provided here encapsualtes (some of) the commands described in the _API Guide_. 
In a nutshell:

    import bbtkv2 

    bb = bbtkv2.BlackBoxToolKit()
    bb.adjust_thresholds()  # adjust the thresholds manually
    bb.clear_timing_data()
    text = bb.capture(10)
    df1 = bbtkv2.capture_output_to_dataframe(text)
    processed_events = bbtkv2.capture_dataframe_to_events(df1)
    print(processed_events)


# Documentation

Check <https://bbtkv2.readthedocs.io/en/latest/intro.html>


# Installation

    pip install bbtkv2==0.1 

---

Christophe@Pallier.org



