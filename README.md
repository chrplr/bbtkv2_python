Python code to communicate with the BlackBox Toolkit v2


The BBTK v2 communicates via a serial protocol over USB.

The commands recognized by the box are described in the _API Guide_. 



# Checking the connection to the Bbtk v2

Before using Python to drive the BBTK v2, it is a good idea to check with an interactive serial communication program that everything s in order.

(These instructions are specific to Linux)


0. Install the Minicom serial communication program

         sudo apt install minicom

1. Power on the Bbtk_v2, then link it through USB cable to your computer

   A usb-storage device `BBTKV2` should be detected and mounted, and a USB ACM device `/dev/ttyACM0`  should have been created.

    Determine the Baud Rate:

        cat /media/*/BBTKV2/BBTK.ini 
        [BaudRate]
        230400

2. Launch Minicom:

	minicom -8 -D /dev/ttyACM0 -b 230400

   The terminal should display:
  
        Welcome to minicom 2.7.1                                                                             
                                                                                                     
        OPTIONS: I18n                                                                                        
        Compiled on Dec 23 2019, 02:06:26.                                                                   
        Port /dev/ttyACM0, 17:31:53                                                                          
                                                                                                     
        Press CTRL-A Z for help on special keys                                                              
 

   Press `CTRL-A Z` and select `Local Echo 'on'`, and `Add Carriage Ret`, and `Send a Break`

3. Run a short acquisition session:


  * Send the command ``CONN``. In return, you should get the messgge ``BBTK;``

  *  Enter the command GEPV read the sensors' thresholds.

  *  Enter ``SEPV`` and 8 times ``63`` to set the sensors' thresholds

  *  Enter ``SPIE`` to erase internal memory. Check the display of the Bbtkv2.

  * To capture events for 10s:
  
      DSCM
      TIML
      10000000
      RUDS


![](bbtkv2_minicom.png)


