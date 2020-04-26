# RaspPi-Character-LCD-Terminal
Allows a character LCD to act as a "window" on the current virtual console

Obviously, the entire console cannot fit on these displays, so this program creates a "window", allowing the LCD to display a portion of the console. The window can be moved around using push buttons, although it should be relatively easy to change this to your needs. To save on pins, this program communicates with the character LCD in 4-bit rather than 8-bit mode.

Requires: python3, RPi.GPIO module

Currently supports 16x2 character LCDs 
