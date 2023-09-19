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

The principle of operation is simple. Three pieces of equipement are needed:

#. A stimulation device (typically a computer) 
#. The bbtkv2 with input sensors (photodiodes, sound detectors, TTL
   detectors) attached to the stimulation device.
#. A host computer driving the bbtkv2 (hooked to it via a USB cable).

.. note::
   The stimulation PC and the host PC can be the same computer. As data are recorded asynchronously by the BBTKv2, it is possible for the host PC to switch the BBTKv2 into “capture mode”, perform the stimulations and, when done, download the timing data from the BBTKv2 memory.
   
The BBTKv2 and the host PC communicate via a serial protocol over
USB. The *bbtkv2* Python module provided here encapsulates (some of)
the commands documented in *The BBTKv2 API Guide* sold by the parent
company.

For example, one of the most useful commands, ``capture()``, monitors
the input sensors for a certain time period and records all changes on
any input line (raising or falling closing edges).  Once the capture
period has elapsed, the BBTKv2 sends the list of all the events,
timestamped, to the host computer.



Installing the Python module
----------------------------

Just run::

   pip install bbtkv2

(Note: Should the pip command not work, just copy
`bbtkv2.py <https://github.com/chrplr/bbtkv2_python/blob/main/src/bbtkv2/bbtkv2.py>`__,
and make sure you have the pyserial module installed)

Using the module
----------------

Configuration
~~~~~~~~~~~~~

Two crucial parameters are:

* The name of the serial port associated to the BBTKv2.

  On most Linux system, it will be ``/dev/ttyACM0`` (which can be identified by running the ``dmesg`` command just after plugging the BBTKv2).       

* the baudrate (speed of transmission of information over the the serial connection).

  When you plug the BBTKv2 in, a USB storage device named ``BBTKV2`` is mounted, which contains a file ``BBTK.ini`` specifying this parameter. On my computer::

       $ cat BBTKV2/BBTK.ini 
       [BaudRate]
       57600


       
To avoid having to pass these parameters everytime one uses the BBTKv2, one can create a ``bbtkv2.toml`` configuration file and pass it to the ``BlackBoxToolKit()`` constructor. Here is an example of such a file:

.. code-block:: TOML

   serialport="/dev/ttyACM0"
   baudrate=57600
   debug=1

   [thresholds]
   Mic1=100
   Mic2=0
   Sounder1=63
   Sounder2=63
   Opto1=110
   Opto2=0
   Opto3=0
   Opto4=0

   [smoothing]
   smoothing='11000011'



Using the bbtkv2 module to capture events
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Launch ``ipython`` and type:

.. code-block:: python


   import bbtkv2

   bb = bbtkv2.bbtkv2.BlackBoxToolKit()

   bb.adjust_thresholds()  # adjust the thresholds manually
   bb.clear_timing_data()  # clear the internal memory of the BBTKv2 
   text = bb.capture(30)   # start capturing events for 30sec

   # convert the results into human readable formats:
   df1 = bbtkv2.bbtkv2.capture_output_to_dataframe(text)
   processed_events = bbtkv2.bbtkv2.capture_dataframe_to_events(df1)
   print(processed_events)

   
If things do not seem to work, you may first to test that the link with the bbtk2 works correclty by running an interactive serial communication software. This procedure is described for Windows in *The BBTKv2 API Guide*  using *TeraTerm VT*. In the next chapter, we explain how to perform the same test under Linux,
using *minicom*.

For example, if you notice that the transmission is garbled, you should decrease this speed in the ``BBTK.ini`` file and reboot the BBTKv2 box.


   
.. [1] Nowadays, one can build a “poor man's” Blackboxtoolkit around
       an Arduino or a Raspberry Pi. But it takes quite a bit of time
       to build the right sensors and validate them. If you have a
       BBTKv2 around you, or enough money to acquire one, it will save
       you time. Another alternative, od course, is to use a digital
       oscilloscope, but these beasts can be complicated to use.
