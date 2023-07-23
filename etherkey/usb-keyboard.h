#pragma once

#define HWSERIAL Serial1
#include "utils.h"
#include "Keyboard.h"
#include "Mouse.h"

#define MYDEBUG
#define KBD_BUFFSZ 200
#define KEYNAME_BUFFSZ 25
#define PREFIX 17 // CTRL-Q

// Code from https://www.sjoerdlangkemper.nl/2022/11/16/running-etherkey-on-arduino-leonardo/
#ifdef ARDUINO_AVR_LEONARDO

#define KEY_UP KEY_UP_ARROW
#define KEY_DOWN KEY_DOWN_ARROW
#define KEY_RIGHT KEY_RIGHT_ARROW
#define KEY_LEFT KEY_LEFT_ARROW

#define KEYPAD_PLUS KEY_KP_PLUS
#define KEYPAD_0 KEY_KP_0

#define KEY_ENTER KEY_RETURN
#define KEY_SPACE ' '

// Create bitmaps of all the modifier keys
#define MODIFIERKEY_CTRL 0x01
#define MODIFIERKEY_ALT 0x02
#define MODIFIERKEY_SHIFT 0x04
#define MODIFIERKEY_GUI 0x08

#define keyboard_leds 0
#endif


// Util functions
int mode_select(char in_ascii, int oldmode);
uint16_t escape_sequence_to_keycode(char in_ascii);
uint16_t special_char_to_keycode(char in_ascii);
uint16_t keyname_to_keycode(const char* keyname);
void usb_send_key(uint16_t key, uint16_t mod);

// Interactive mode functions
void interactive_mode(char in_ascii);

// Command mode functions
void command_mode(char in_ascii);
void c_parse(char* str);
bool c_parse_ext(char* str, bool send_single, int modifier);
void c_sendraw(char* pch);
void c_send(char* pch);
void c_unicode(char* pch, bool linux);
void c_sleep(int ms);

// Debug mode functions
void debug_mode(char in_ascii);
