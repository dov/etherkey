#!/usr/bin/python

######################################################################
#  A client for a arduino micro pro (like) running the etherkey
#  software and communicating with it over serial.
#
#  Dov Grobgeld <dov.grobgeld@gmail.com>
#  2022-06-07 Tue
######################################################################

import gi
import serial,time
import pdb
import cairo
import time
import argparse
import socket
import urllib3
import re
import json
import random

gi.require_version('PangoCairo', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Gdk, PangoCairo, Pango

debug = False

# mouse wiggle default parameters
wiggle_timeout = 5  # five seconds
wiggle_strength = 5 # five units of maximum movements

def _ctrl(ch):
  '''Control function'''
  return chr(ord(ch.upper())-ord('@')).encode()

class EthClient:
  '''A client to a serial connected ether client'''
  def __init__(self,
               device = '/dev/ttyUSB0',
               baudrate = 57600):
    self.sr = serial.Serial(device, baudrate=baudrate,interCharTimeout=1)
    
    # Switch to command mode
    self.sr.write(_ctrl('q')+b'1') # Initial reset

  def send(self, cmd):
    '''Send a key sequence encoded as an etherkey command'''
    self.sr.write(('send ' + cmd).encode() + _ctrl('m'))

  def mouse_move(self, cmd):
    '''Send a mouse sequence encoded as an etherkey command'''
    self.sr.write(('mouse-move ' + cmd).encode() + _ctrl('m'))

  def mouse_button_press(self, cmd):
    '''Send a mouse sequence encoded as an etherkey command'''
    self.sr.write(('mouse-button-press ' + cmd).encode() + _ctrl('m'))

  def mouse_button_release(self, cmd):
    '''Send a mouse sequence encoded as an etherkey command'''
    self.sr.write(('mouse-button-release ' + cmd).encode() + _ctrl('m'))

  def mouse_wheel(self, cmd):
    '''Send a mouse wheel encoded as an etherkey command'''
    self.sr.write(('mouse-wheel ' + cmd).encode() + _ctrl('m'))

  def char_encode(self, line):
    ret = ''
    for ch in line:
      if ch == ' ':
        ret += '{space}'
      elif ch == '\n':
        ret += '{Enter}'
      elif ch in '!@#$%^&*(){}[]/?=+\'",<.>\\':
        ret += '{'+ch+'}'
      else:
        ret += ch
    return ret
        
  def send_code(self, code):
    '''Send a raw command'''
    self.sr.write(('send ' + code).encode() + _ctrl('m'))
    
  def send_string(self, string):
    '''Upload a file by "typing it" on to the remote computer'''
    max_len = 16 # Max chunk size

    # Split the string into chunks of maximum max_len chars
    chunks = []
    while len(string):
      chunks += [string[0:max_len]]
      string = string[max_len:]

    # Encode and send the chunks one at a time
    for chunk in chunks:
      chunk = self.char_encode(chunk)
      self.sr.write(('send ' + chunk).encode() + _ctrl('m'))
      # Heuristic sleeping between chunks in order not to loose characters. Seems ok
      time.sleep(0.01*len(chunk))

  def upload_file(self, filename):
    with open(filename) as fh:
      data = fh.read()
    print(f'Sending {data=}')
    self.send_string(data)
    

# Reference: https://stackoverflow.com/questions/18160315/write-custom-widget-with-gtk3
class MyWidget(Gtk.Misc):
  __gtype_name__ = 'MyWidget'

  def __init__(self, no_grab = False, *args, **kwds):
    super().__init__(*args, **kwds)

    # Wiggle interaction
    self.reset_wiggle()

    self.set_size_request(300, 300)
    self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    # Need this to get the mouse events!!
    self.set_events(Gdk.EventMask.ALL_EVENTS_MASK
                    | Gdk.EventMask.KEY_PRESS_MASK
                    | Gdk.EventMask.KEY_RELEASE_MASK
                    )

    self.connect('button-press-event', self.on_button_press)
    self.connect('button-release-event', self.on_button_release)
    self.connect('motion-notify-event', self.on_motion_notify)
    self.connect('scroll-event', self.on_scroll)

    self.is_grabbed = False
    self.mouse_x = None
    self.mouse_y = None
    self.mouse_scale_x = 1
    self.mouse_scale_y = 1
    self.right_control = False  # Used for special
    self.no_grab = no_grab

    # Needed for keypress events
    self.set_can_focus(True)
    self.grab_focus()
    self.modifier_keys = {
       37 : ('^', 'Left control'),
       66 : ('^', 'Caps lock'),
       50 : ('+', 'Left Shift'),
       64 : ('!', 'LeftAlt'),
      133 : ('#', 'LeftGui'),
      105 : ('^', 'RightControl'),
       62 : ('+', 'Rightshift'),
      108 : ('!', 'RightAlt'),
      134 : ('#', 'Right GUI'),
      }
    self.special_keys = {
       9 : ('{Escape}', 'Escape'),
      36 : ('{Enter}', 'Enter'),
      22 : ('{BS}', 'Backspace'),
      23 : ('{Tab}', 'Tab'),
      114 : ('{Right}', 'Right arrow'),
      111 : ('{Up}', 'Up arrow'),
      113 : ('{Left}', 'Left arrow'),
      116 : ('{Down}', 'Right arrow'),
      118 : ('{Insert}', 'Insert'),
      110 : ('{Home}', 'Home'),
      112 : ('{PgUp}', 'PgUp'),
      117 : ('{PgDn}', 'PgDn'),
      115 : ('{End}', 'End'),
      119 : ('{Delete}', 'Delete'),
      85 : ('{Right}', 'Right arrow'),
      80 : ('{Up}', 'Up arrow'),
      83 : ('{Left}', 'Left arrow'),
      88 : ('{Down}', 'Right arrow'),
      67 : ('{F1}', 'F1'),
      67 : ('{F1}', 'F1'),
      68 : ('{F2}', 'F2'),
      69 : ('{F3}', 'F3'),
      70 : ('{F4}', 'F4'),
      71 : ('{F5}', 'F5'),
      72 : ('{F6}', 'F6'),
      73 : ('{F7}', 'F7'),
      74 : ('{F8}', 'F8'),
      75 : ('{F9}', 'F9'),
      76 : ('{F10}', 'F10'),
      95 : ('{F11}', 'F11'),
      96 : ('{F12}', 'F12'),
      }

    # mouse mapping
    self.mouse_buttons = { 1:0, 2:2, 3:1}

    # Active modifiers
    self.modifiers = set()
    display = Gdk.Display.get_default()
    self.seat = display.get_default_seat()
    self.set_text('Welcome to\n'
                  'ether-key-\n'
                  'client!')

  def set_text(self, text):
    self.text = text
    self.queue_draw()

  def do_draw(self, cr):
    # paint background
    Gtk.render_background(self.get_style_context(),
                          cr,
                          0,0,
                          self.get_allocated_width(),
                          self.get_allocated_height())
    cr.fill()

    # Can draw something else
    cr.set_source_rgb(0.5, 0, 0)
    cr.set_font_size(56)
    cr.select_font_face("Arial",
                         cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_NORMAL)
    cr.move_to(10,40)

    # Create a Pango context and layout
    layout = PangoCairo.create_layout(cr)
    
    # Set the font and text
    font_desc = Pango.FontDescription("Sans 25")
    layout.set_font_description(font_desc)
    layout.set_markup(self.text)
    
    # Render the text
    cr.set_source_rgb(0, 0, 0)
    PangoCairo.update_layout(cr, layout)
    PangoCairo.show_layout(cr, layout)

    self.grab_focus()

  def encode_modifiers(self):
    return ''.join(
      set(self.modifier_keys[k][0]
          for k in self.modifiers))  # Set for unique

  def on_motion_notify(self, window, event):
    self.reset_wiggle()

    if self.mouse_x is None:
      self.mouse_x = event.x
    if self.mouse_y is None:
      self.mouse_y = event.y
    dx = int(round((event.x - self.mouse_x) * self.mouse_scale_x))
    dy = int(round((event.y - self.mouse_y) * self.mouse_scale_y))
    self.mouse_x += dx
    self.mouse_y += dy
    ec.mouse_move(f'{dx} {dy}')

    # warp pointer. TBD - This is w.r.t. to the window, so we need
    # to get its original position on the screen!
    origin = self.get_window().get_origin()
    screen_x = origin.x
    screen_y = origin.y
    screen = self.get_screen()
    display = Gdk.Display.get_default()
    monitor = display.get_monitor(0)
    geometry = monitor.get_geometry()
    screen_width = geometry.width
    screen_height = geometry.height
    
    if self.is_grabbed and (
      self.mouse_x+screen_x <= 0
      or self.mouse_y+screen_y <=0
      or self.mouse_x+screen_x >= screen_width-1
      or self.mouse_y+screen_y >= screen_height-1
      ):
      self.mouse_x = 1000 + screen_x
      self.mouse_y = 1000 + screen_y
      Gdk.Device.warp(display.get_default_seat().get_pointer(), self.get_window().get_screen(), self.mouse_x, self.mouse_y)


  def on_scroll(self, window, event):
    self.reset_wiggle()

    # gtk and arduino hid has different ideas of scroll direction
    # therefore the minus
    cmd = f'{-event.delta_y:.0f}'
    ec.mouse_wheel(cmd)

  def on_button_press(self, window, event):
    self.reset_wiggle()

    mouse_button = self.mouse_buttons[event.button]
    ec.mouse_button_press(f' {mouse_button}')

  def on_button_release(self, window, event):
    self.reset_wiggle()

    mouse_button = self.mouse_buttons[event.button]
    ec.mouse_button_release(f' {mouse_button}')
    pass

  def do_key_press_event(self, event):
    self.reset_wiggle()

    # Catch right control
    if event.hardware_keycode == 105:
      self.right_control_handled = False
      self.right_control = True
      return

    if self.right_control:
      if event.hardware_keycode in (118, # insert
                                    119, # delete
                                    111, # Up
                                    113, # Left
                                    114, # right
                                    116, # down
                                    ):  
        if event.hardware_keycode in (118,119):
          print('Control Alt Delete')
          ec.send('^!{Delete}')
        elif event.hardware_keycode == 113:
          ec.mouse_move('-100 0')
        elif event.hardware_keycode == 114:
          ec.mouse_move(f'100 0')
        elif event.hardware_keycode == 111:
          ec.mouse_move(f'0 -100')
        elif event.hardware_keycode == 116:
          ec.mouse_move(f'0 100')
          
        self.right_control_handled = True
        return

    if event.hardware_keycode in self.modifier_keys:
      if debug:
        print('Press ' + self.modifier_keys[event.hardware_keycode][1])
      self.modifiers.add(event.hardware_keycode)
      return
    if debug:
      print(f'{event.hardware_keycode=}')

    # Allow uploading a file
    # Look for control f
    if not self.is_grabbed:
      # Control f including on swapped keyboards
      is_control = any(self.modifiers for k in (37,66))
      is_shift = any(self.modifiers for k in (50,62))
      if is_control and chr(event.keyval) == 'f':
        dialog = Gtk.FileChooserDialog(title='Select a file',
                                       parent=self.get_toplevel(),
                                       action = Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(
          Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
          Gtk.STOCK_OK, Gtk.ResponseType.OK)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
          fn = dialog.get_filename()
          ec.upload_file(fn)
        dialog.destroy()
        print('Got control-f!')
        return

      # C-v or S-Insert pastes the clipboard
      if ((is_control and chr(event.keyval) == 'v')
          # shift insert
          or (is_shift and event.hardware_keycode == 118)
          ):
        text = self.clipboard.wait_for_text()
        ec.send_string(text)
        return

    if event.hardware_keycode in self.special_keys:
      if debug:
        print('Got ' + self.special_keys[event.hardware_keycode][1])
      ec.send(self.encode_modifiers() + self.special_keys[event.hardware_keycode][0])
      return

    # Treat shift keys different
    key = chr(event.keyval)
    if key in '+{}[]!@#$%^&*()-_`~\'"<>':
      ec.send(self.encode_modifiers().replace('+','') + '{' + key + '}')
      return

    cmd = self.encode_modifiers() + key
    ec.send(cmd)

  def do_key_release_event(self, event):
    self.reset_wiggle()

    # Catch right control
    if event.hardware_keycode == 105:
      self.right_control = False
      if not self.right_control_handled:
        self.toggle_grab()
      return

    if event.hardware_keycode in self.modifier_keys:
      if debug:
        print('Release ' + self.modifier_keys[event.hardware_keycode][1])
      self.modifiers.remove(event.hardware_keycode)

  def toggle_grab(self):
    self.reset_wiggle()

    if self.no_grab:
      return
    self.is_grabbed = not self.is_grabbed

    if self.is_grabbed:
      self.set_text('<b>Grabbed</b>\nRight Ctrl\nto ungrab')

      print('grabbing')
      self.seat.grab(self.get_window(),
                     Gdk.SeatCapabilities.KEYBOARD
                     | Gdk.SeatCapabilities.POINTER
                     ,
                     True,
                     None, None,
                     None)
    else:
      self.set_text('<b>Ungrabbed</b>\nRight Ctrl\nto grab')
      print('ungrabbing')
      self.seat.ungrab()

  def reset_wiggle(self):
    self.last_interaction = time.time()

  def wiggle_mouse_maybe(self):
    now = time.time()
    if now - self.last_interaction > wiggle_timeout:
      # Random, but don't allow a 0,0 motion
      while True:
        dx,dy = [int(wiggle_strength*2*(random.random()-0.5))
                 for i in range(2)]
        if abs(dx)+abs(dy)!= 0:
          break

      ec.mouse_move(f'{dx} {dy}')
      self.reset_wiggle()

class MyWindow(Gtk.Window):
  def __init__(self, no_grab = False):
    super().__init__(title='EtherKeyClient')

    self.wdg = MyWidget(no_grab = no_grab)
    self.add(self.wdg)
    self.connect('map-event', self.on_map_event)

  def on_map_event(self, window, event):
    print('on_map_event')
    self.wdg.toggle_grab()

  def wiggle_mouse_maybe(self):
    self.wdg.wiggle_mouse_maybe()

class SocketListener:
  def __init__(self, port=8333, eth_client=None):
    self.port = port
    self.ec = eth_client

  def start_socket_listener(self):
    HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
    
    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server_socket.bind((HOST, self.port))
    self.server_socket.listen()
  
    GLib.io_add_watch(self.server_socket.fileno(),
                      GLib.IO_IN,
                      self.handle_connection)
    return True


  def handle_connection(self, fd, flags):
    print('Handle connection')
    conn, addr = self.server_socket.accept()
    with conn:
      print(f"Connected by {addr}")
      while True:
        data = conn.recv(1024)
        if not data:
            break

        resp = ('HTTP/1.1 200 OK\n'
                'Content-Type: application/json\n'
                '\n'
                '{ "res" : "ok" }')

        print(f'Got {data}')
        conn.sendall(resp.encode())
        break

    # Assume we got all the data
    try:
      path, payload = self.decode_request(data)
    except RuntimeError as exc:
      return

    root = json.loads(payload)

    # We support sending either strings or "raw" codes
    action = root.get('action')
    if action == 'string':
      # How do i encode? the keys??
      self.ec.send_string(root.get('string'))
    elif action == 'code':
      self.ec.send_code(root.get('code'))
    elif action == 'file':
      self.ec.upload_file(root.get('filename'))

    conn.close()
    return True
        

  def decode_request(self, data):
    '''A simple http request decoder. Returns path and payload'''
    m = re.search(r'POST (\S+)\s.(?:\S+)\r\n'
                  r'.*'
                  r'\r\n\r\n(.*)'
                  ,
                  data.decode(),
                  re.DOTALL|re.MULTILINE
                  )
    if m:
      return m.group(1), m.group(2)
    raise RuntimeError('Failed matching patch!')

def timeout_function():
  # Here put all periodic activities. Currently we support
  # mouse wiggling.
  if args.mouse_alive:
    win.wiggle_mouse_maybe()
  return 1
  
  
parser = argparse.ArgumentParser(description='Process a file')
parser.add_argument('-u', '--upload',
                    dest='upload',
                    action='store',
                    type=str,
                    default=None,
                    help='Output filename')
parser.add_argument('-d', '--device',
                    dest='device',
                    action='store',
                    type=str,
                    default='/dev/ttyUSB0',
                    help='Output filename')
parser.add_argument('-p', '--port',
                    dest='port',
                    action='store',
                    type=int,
                    default=8333,
                    help='listener port')
parser.add_argument('--no-grab',
                    dest='no_grab',
                    action='store_true',
                    help='Whether to grab')
parser.add_argument('--mouse-alive',
                    dest='mouse_alive',
                    action='store_true',
                    help='Whether to keep alive by moving the mouse')
args = parser.parse_args()

ec = EthClient(device=args.device)
print('Connected!')

sl = SocketListener(port=args.port,
                    eth_client = ec)
sl.start_socket_listener()


if args.upload is not None:
  ec.upload_file(args.upload)
  exit()



# Interactive by default
win = MyWindow(no_grab = args.no_grab)
win.connect('destroy', Gtk.main_quit)
win.show_all()
GLib.timeout_add(500, timeout_function)
Gtk.main()

