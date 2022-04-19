Acquiring timing data using the bbtkv2 python module
====================================================

.. raw:: html

   <p align="center">

.. image:: images/bbtkv2.png

.. raw:: html

   </p>

The **BlackBox ToolKit v2** is a device that allows psychologists to
 measure the timing of audio-visual stimuli with sub-millisecond
 accuracy. It replaces a digital oscilloscope (capturing activity on
 sound and visual sensors, or TTL signals) and a signal generator
 (generating sound or TTL signal. (See
 https://www.blackboxtoolkit.com/bbtkv2.html for more information) [1]_.

The princle of operation is simple. Three pieces of equipement are needed:
#. A stimulation device (Typically a computer) 
#. The bbtkv2 with input sensors (photodiodes, sound detectors, TTL
   detectors) disposed on the stimulation device.
#. A host computer controling the bbtkv2 (hooked to it via a USB cable).

  
The BBTKv2 communicates with the host PC via commands send by a serial
protocol over USB.

For example, one of the most useful commands, “Digital Stimulus
Capture”, monitors the input sensors for a certain time period and
records all events (leading or closing edges) occuring on any line.
Once the period has elapsed, the bbtkv2 sends the list of all events,
along with their timestamps, to the host computer.


The *bbtkv2* python module provided here encapsulates (some of) the
commands described in *The BBTKv2 API Guide* sold by the parent company. 



Installing the python module
----------------------------

Just run::

   pip install bbtkv2

(Note: Should the pip command not work, just copy
`bbtkv2.py <https://github.com/chrplr/bbtkv2_python/blob/main/src/bbtkv2.py>`__,
and make sure you have the pyserial module installed)

Testing
-------

You may first want to test that the link with the bbtk2 works correclty by
running an interactive serial communication software. This procedure is described
in *The BBTKv2 API Guide*  using *TeraTerm VT* under sWindows. In the
next chapter, we explain how to perfom the same operation under Linux,
using *Minicom*.


Using the bbtkv2 module to capture events
-----------------------------------------

Launch `ipython` and type:

.. code-block:: python

   from bbtkv2 import BlackBokToolKit

   bb = BlackBoxToolKit()
   df = bb.digital_stimulus_capture(30)  # run capture for 30s
   print(df)


