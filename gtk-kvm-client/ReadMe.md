# Intro

`ether-key-client` is a client in python gtk to enable using a local keyboard and mouse on a remote computer. 

# Usage

 - Connect the arduino leonardo (I used a micro pro version from Ali Express) to the remote computer, and write it up to a FTI device which is connected to the host computer (with mouse and keyboard to forward).
 - Run `ether-key-client.py`
 - This will popup a small window on the desktop and will grab the mouse and the keyboard and forward all keyboard and mouse events t ograb the mouse 
 - Use mouse and keyboard as if working on the remote computer.
 - To release the grab press the "right control" button
 
# Command line usage

- ether-key-client can be used to upload a file to the remote computer by the `-u` switch.
- The option is also available by doing the following:
  - Exit grab mode
  - Press Ctrl+f
  - Choose file and press ok
  
