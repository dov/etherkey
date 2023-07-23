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

gi.require_version('PangoCairo', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, PangoCairo, Pango

debug = False

def _ctrl(ch):
  '''Control function'''
  return chr(ord(ch.upper())-ord('@')).encode()

class EthClient:
  '''A client to a serial connected ether client'''
  def __init__(self,
               port = '/dev/ttyUSB0',
               baudrate = 57600):
    self.sr = serial.Serial(port, baudrate=baudrate,interCharTimeout=1)
    
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

ec  = EthClient()
print('Connected!')

def press_key(key):
  url_get(f'{key_host}/press/{key}')

# Meanwhile we (etherclient) doesn't support this
def release_key(key):
  url_get(f'{key_host}/release/{key}')

# Reference: https://stackoverflow.com/questions/18160315/write-custom-widget-with-gtk3
class MyWidget(Gtk.Misc):
  __gtype_name__ = 'MyWidget'

  def __init__(self, *args, **kwds):
    super().__init__(*args, **kwds)
    self.set_size_request(300, 300)

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
    self.mouse_scale_x = 0.5
    self.mouse_scale_y = 0.5

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
    
    if self.is_grabbed and (
      self.mouse_x+screen_x <= 0
      or self.mouse_y+screen_y <=0
      or self.mouse_x+screen_x >= screen.get_width()-1
      or self.mouse_y+screen_y >= screen.get_height()-1
      ):
      self.mouse_x = 1000 + screen_x
      self.mouse_y = 1000 + screen_y
      Gdk.Device.warp(Gdk.Display.get_default().get_default_seat().get_pointer(), self.get_window().get_screen(), self.mouse_x, self.mouse_y)


  def on_scroll(self, window, event):
    # gtk and arduino hid has different ideas of scroll direction
    # therefore the minus
    cmd = f'{-event.delta_y:.0f}'
    ec.mouse_wheel(cmd)

  def on_button_press(self, window, event):
    ec.mouse_button_press(f' {event.button-1}')

  def on_button_release(self, window, event):
    ec.mouse_button_release(f' {event.button-1}')
    pass

  def do_key_press_event(self, event):
    # Catch right control
    if event.hardware_keycode == 105:
      self.toggle_grab()
      return

    if event.hardware_keycode in self.modifier_keys:
      if debug:
        print('Press ' + self.modifier_keys[event.hardware_keycode][1])
      self.modifiers.add(event.hardware_keycode)
      return
    if debug:
      print(f'{event.hardware_keycode=}')

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
    # Catch right control
    if event.hardware_keycode == 105:
      return
    if event.hardware_keycode in self.modifier_keys:
      if debug:
        print('Release ' + self.modifier_keys[event.hardware_keycode][1])
      self.modifiers.remove(event.hardware_keycode)

  def toggle_grab(self):
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

class MyWindow(Gtk.Window):
  def __init__(self):
    super().__init__(title='EtherKeyClient')

    self.wdg = MyWidget()
    self.add(self.wdg)
    self.connect('map-event', self.on_map_event)

  def on_map_event(self, window, event):
    print('on_map_event')
    self.wdg.toggle_grab()


win = MyWindow()
win.connect('destroy', Gtk.main_quit)
win.show_all()
Gtk.main()
