# name=Mixer Control Script
# url=https://forum.image-line.com/viewtopic.php?p=1483607#p1483607

# This import section is loading the back-end code required to execute the script. You may not need all modules that are available for all scripts.

import transport
import mixer
import ui
import midi
import device
import channels
import playlist
import patterns
import arrangement
import plugins
import general
import launchMapPages

# The next two variables are constants defined up here so you don't need tp go hunting in the script to find them later. Good habit.
# You can name these as you like, so long as you use them in the script below as written ...

Faders_UpNote = 48  # All faders up midi note number
Faders_DownNote = 50  # All faders midi down note number


class TSimple():

    def OnRefresh(flags):
        print('working')
        print(device.getName())
        device.midiOutSysex(
            bytes([0xF0, 0x00, 0x00, 0x66, 0x14, 0x0C, 1, 0xF7]))

        #device.midiOutSysex('0xE0, 0x03, 0x04, 0xF7')



def sendMidiBytes(byte1, byte2, byte3):
    msg = byte1 + (byte2 << 8) + (byte3 << 16)
    #print(device.getName)
    device.midiOutMsg(msg)


Simple = TSimple()


def OnUpdateMeters():
    # sendMidiBytes(0x00,0x00,0x00)
    for n in range(0, 48):
        # print(bytes([10]))
        p = mixer.getTrackPeaks(n, 2)
        p = int(p * 127)
        if (p > 0):
            # sendMidiBytes(bytes([n]), bytes([p]), bytes([1])
            a = n
            b = p
            c = 1
            # device.midiOutMsg(264193)
            #sendMidiBytes(a, b, c)
        # sendMidiBytes(format(a, 'x'),format(b, 'x'),format(c, 'x'))

        # print(p)


def OnInit():
    device.setHasMeters()


def OnMidiMsg(event):
    Simple.OnMidiMsg(event)


def OnRefresh(long):
    Simple.OnRefresh()
