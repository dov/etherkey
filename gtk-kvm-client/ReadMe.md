# Intro

`ether-key-client` is a client in python gtk to enable using a local keyboard and mouse on a remote computer. 

# Usage

 - Connect the arduino leonardo (I used a micro pro version from Ali Express) to the remote computer, and write it up to a FTI device which is connected to the host computer (with mouse and keyboard to forward).
 - Run `ether-key-client.py`
 - This will popup a small window on the desktop and will grab the mouse and the keyboard and forward all keyboard and mouse events t ograb the mouse 
 - Use mouse and keyboard as if working on the remote computer.
 - To release the grab press the "right control" button. To grab again, focus the mouse in the ether-key-client.py window and press right-control again.
 
# Command line usage

- ether-key-client.py can be used to upload a file to the remote computer by the `-u` switch.
- The option is also available by doing the following:
  - Exit grab mode
  - Press Ctrl+f
  - Choose file and press ok
  
# json rpc server

ether-key-client.py is also listening to commands on on json rpc. 

Here is an example of sending a few codes by `wget` to the remote client.

```
wget -O - -q --post-data '{"action":"code","code":"{Escape}:(g2){Enter}"}' http://localhost:8333
```

Longer strings may be sent by the 'send' actions:

```
wget -O - -q --post-data '{"action":"string","string":"The quick brown..." }' http://localhost:8333
```

Entire files may be sent by the 'file' action:

```
wget -O - -q --post-data '{"action":"file","filename":"/path/to/file" }' http://localhost:8333
```
