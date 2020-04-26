# NOTE: This program must be run with sudo/root priviliges to access GPIO lines

import RPi.GPIO as GPIO
import time

# All pin numbers use physical pin numbering
# pins for data lines D4-D7 on LCD
DATA = [7, 11, 13, 15]

# EN pin on LCD
ENABLE = 19
# RS pin on LCD
REG_SEL = 21

# pins for screen scroll buttons
UP = 23
DOWN = 24 
LEFT = 26
RIGHT = 22

def lcdSetup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(DATA[3], GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(DATA[2], GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(DATA[1], GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(DATA[0], GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ENABLE, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(REG_SEL, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(UP,GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DOWN,GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LEFT,GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(RIGHT,GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Function Set: 4-bit bus, 2-line display mode, 5x8 dot display mode
    sendCommand(0x28)
    time.sleep(0.01)
    # Display ON/OFF: display on, cursor on, cursor blink on
    sendCommand(0x0F)
    time.sleep(0.01)
    # Clear Dislay
    sendCommand(0x01)
    time.sleep(0.01)
    # Entry Mode Set: cursor moves to right, no display shift
    sendCommand(0x06)
    time.sleep(0.01)

# Sends a command to the LCD display
def sendCommand(command):
    GPIO.output(REG_SEL, False)
    for i,bit in enumerate(format((command & 0xF0) >> 4,'04b')):
        GPIO.output(DATA[3-i], int(bit))
    GPIO.output(ENABLE, True)
    GPIO.output(ENABLE, False)
    for i,bit in enumerate(format(command & 0xF,'04b')):
        GPIO.output(DATA[3-i], int(bit))
    GPIO.output(ENABLE, True)
    GPIO.output(ENABLE, False)

# Print a single character to display
def printChar(data):
    GPIO.output(REG_SEL, True)
    try:
        dataBinary = format(ord(data),'08b')
    except TypeError:
        dataBinary = format(data,'08b')

    for i,bit in enumerate(dataBinary[0:4]):
        GPIO.output(DATA[3-i], int(bit))
    GPIO.output(ENABLE, True)
    GPIO.output(ENABLE, False)
    for i,bit in enumerate(dataBinary[4:]):
        GPIO.output(DATA[3-i], int(bit))
    GPIO.output(ENABLE, True)
    GPIO.output(ENABLE, False)

class Terminal:
    def __init__(self,x,y,consoleStream,consoleAttrStream):
        # position of lcd view relative to the console
        self.viewX = x
        self.viewY = y
        
        self.oldlines = "" # holds lcd data to determine if it needs redrawing
        self.console = open(consoleStream, 'rb')
        
        # read from the vcsa stream to get console height, width, and cursor position
        self.consoleAttrStream = open(consoleAttrStream,'rb')
        self.lines,self.cols,self.cursorX,self.cursorY = self.consoleAttrStream.read(4)
    
    def display(self):
        # read console stream
        self.console.seek(0)
        screen = self.console.read()
        # get byte offset of console data within lcd view
        pos = self.viewY*self.cols+self.viewX
        # read console data within lcd view
        lcdLines = screen[pos:pos+16] + screen[pos+self.cols:pos+self.cols+16]
        
        # check to see if console has changed and lcd needs redrawing
        if lcdLines != self.oldlines:
            sendCommand(0x02) # return cursor to top left of lcd
            time.sleep(0.001)
            
            # push console data to lcd
            for i in range(0,32):
                if i == 16:
                    sendCommand(0xA8) # move cursor to second line of lcd
                    time.sleep(0.01)
                printChar(lcdLines[i])
            
            self.oldlines = lcdLines
        
        # read cursor position
        self.consoleAttrStream.seek(2)
        self.cursorX, self.cursorY = self.consoleAttrStream.read(2)
        
        # check if terminal cursor is within the current lcd view
        if (self.cursorX >= self.viewX and self.cursorX < self.viewX + 16
            and self.cursorY >= self.viewY and self.cursorY < self.viewY+2):
            # turn on cursor
            sendCommand(0x0F)
            lcdCursorAddrX = self.cursorX - self.viewX
            lcdCursorAddrY = self.cursorY - self.viewY
            time.sleep(0.001)
            # move blinking cursor to proper position
            sendCommand(0x80 + lcdCursorAddrY*0x40+lcdCursorAddrX)
        else:
            # turn off cursor
            sendCommand(0x0C)

    # Scroll view based on button presses
    def scroll(self):
        if (getKey(UP) and self.viewY > 0):
            self.viewY -= 1
        elif (getKey(LEFT) and self.viewX > 0):
            self.viewX -= 1
        elif (getKey(DOWN) and self.viewY < self.lines-2):
            self.viewY += 1
        elif (getKey(RIGHT) and self.viewX < self.cols-16):
            self.viewX += 1
        self.display()

# returns if a key is pressed, active low
def getKey(key):
    if not GPIO.input(key):
        # simple debounce code
        time.sleep(0.001)
        if not GPIO.input(key):
            return True
    return False

try:
    lcdSetup()
    terminal = Terminal(0,0,"/dev/vcs", "/dev/vcsa")
    terminal.display()
    while True:
        terminal.scroll()
        time.sleep(0.1)

# On Ctrl-C program exit
finally:
    GPIO.cleanup()   
