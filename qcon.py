# name=ICON QCON Pro X
# url= https://forum.image-line.com/viewtopic.php?f=1994&t=254916
# supportedDevices=ICON QCON Pro X

import time
import arrangement
import channels
import device
import general
import launchMapPages
import midi
import mixer
import patterns
import playlist
import plugins
import transport
import ui
import utils

MackieCU_KnobOffOnT = [(midi.MIDI_CONTROLCHANGE + (1 << 6)) << 16,
                       midi.MIDI_CONTROLCHANGE + ((0xB + (2 << 4) + (1 << 6)) << 16)]
MackieCU_nFreeTracks = 64

# const
# Select
MackieCUNote_Select1 = 0x18
MackieCUNote_Select2 = 0x19
MackieCUNote_Select3 = 0x1A
MackieCUNote_Select4 = 0x1B
MackieCUNote_Select5 = 0x1C
MackieCUNote_Select6 = 0x1D
MackieCUNote_Select7 = 0x1E
MackieCUNote_Select8 = 0x1F

# F1-F8 buttons
MackieCUNote_F1 = 0x36
MackieCUNote_F2 = 0x37
MackieCUNote_F3 = 0x38
MackieCUNote_F4 = 0x39
MackieCUNote_F5 = 0x3A
MackieCUNote_F6 = 0x3B
MackieCUNote_F7 = 0x3C
MackieCUNote_F8 = 0x3D

# Utility
MackieCUNote_Save = 0x50
MackieCUNote_Undo = 0x51
MackieCUNote_Cancel = 0x52
MackieCUNote_Enter = 0x53

# Modify
MackieCUNote_Shift = 0x46
MackieCUNote_Option = 0x47
MackieCUNote_Control = 0x48
MackieCUNote_Alt = 0x49

# Sections
MackieCUNote_MidiTracks = 0x3E  # Patters
MackieCUNote_Inputs = 0x3F  # Mixer Tracks
MackieCUNote_AudioTracks = 0x40  # Channels
MackieCUNote_AudioInst = 0x41  # TODO
MackieCUNote_Aux = 0x42  # TODO
MackieCUNote_Buses = 0x43  # Sends
MackieCUNote_Outputs = 0x44  # Master
MackieCUNote_User = 0x45  # Browser

# Automation
MackieCUNote_Read = 0x4A  # TODO
MackieCUNote_Write = 0x4B  # TODO
MackieCUNote_Trim = 0x4C  # TODO
MackieCUNote_Touch = 0x4D  # TODO
MackieCUNote_Latch = 0x4E  # TODO
MackieCUNote_Group = 0x4F  # TODO

# Transport
MackieCUNote_Marker = 0x54
MackieCUNote_Nudge = 0x55  # TODO
MackieCUNote_Cycle = 0x56
MackieCUNote_Drop = 0x57
MackieCUNote_Replace = 0x58
MackieCUNote_Click = 0x59
MackieCUNote_Solo = 0x5A
MackieCUNote_Rewind = 0x5B
MackieCUNote_Forward = 0x5C
MackieCUNote_Stop = 0x5D
MackieCUNote_Start = 0x5E
MackieCUNote_Record = 0x5F

# Channels
MackieCUNote_Bank_Previous = 0x2E
MackieCUNote_Bank_Next = 0x2F
MackieCUNote_Channel_Previous = 0x30
MackieCUNote_Channel_Next = 0x31

# Encoder Assign
MackieCUNote_Pan = 0x28
MackieCUNote_Stereo = 0x2A
MackieCUNote_Sends = 0x29
MackieCUNote_FX = 0x2B
MackieCUNote_EQ = 0x2C
MackieCUNote_Free = 0x2D

# Navigation
MackieCUNote_Up = 0x60
MackieCUNote_Down = 0x61
MackieCUNote_Left = 0x62
MackieCUNote_Right = 0x63
MackieCUNote_Zoom = 0x64
MackieCUNote_Scrub = 0x65

# Mackie CU pages
MackieCUPage_Pan = 0
MackieCUPage_Stereo = 1
MackieCUPage_Sends = 2
MackieCUPage_FX = 3
MackieCUPage_EQ = 4
MackieCUPage_Free = 5

ExtenderLeft = 0
ExtenderRight = 1

OffOnStr = ('off', 'on')

MasterPeak = 0

class TMackieCol:
    def __init__(self):
        self.TrackNum = 0
        self.BaseEventID = 0
        self.KnobEventID = 0
        self.KnobPressEventID = 0
        self.KnobResetEventID = 0
        self.KnobResetValue = 0
        self.KnobMode = 0
        self.KnobCenter = 0
        self.SliderEventID = 0
        self.Peak = 0
        self.Tag = 0
        self.SliderName = ""
        self.KnobName = ""
        self.LastValueIndex = 0
        self.ZPeak = False
        self.Dirty = False
        self.KnobHeld = False


class TMackieCU():
    def __init__(self):
        self.LastMsgLen = MackieCUNote_F2
        self.TempMsgT = ["", ""]
        self.LastTimeMsg = bytearray(10)

        self.Shift = False
        self.Control = False
        self.Option = False
        self.Alt = False

        self.TempMsgDirty = False
        self.JogSource = 0
        self.TempMsgCount = 0
        self.SliderHoldCount = 0
        self.FirstTrack = 0
        self.FirstTrackT = [0, 0]
        self.ColT = [0 for x in range(9)]
        for x in range(0, 9):
            self.ColT[x] = TMackieCol()

        self.FreeCtrlT = [0 for x in range(
            MackieCU_nFreeTracks - 1 + 2)]  # 64+1 sliders
        self.Clicking = False
        self.Scrub = False
        self.Flip = False
        self.MeterMode = 0
        self.CurMeterMode = 0
        self.Page = 0
        self.SmoothSpeed = 0
        self.MeterMax = 0
        self.ActivityMax = 0

        self.MackieCU_PageNameT = ('Panning                          (press VPOT to reset)', 'Stereo separation                (press VPOT to reset)','Sends for selected track        (press VPOT to enable)',
                                   'Effects for selected track      (turn VPOTS to adjust)', 'EQ for selected track           (press VPOTS to reset)',  '(Free Controls)')
        self.MackieCU_MeterModeNameT = (
            'Horizontal meters mode', 'Vertical meters mode', 'Disabled meters mode')
        self.MackieCU_ExtenderPosT = ('left', 'right')

        self.FreeEventID = 400
        self.ArrowsStr = chr(0x7F) + chr(0x7E) + chr(0x32)
        self.AlphaTrack_SliderMax = round(13072 * 16000 / 12800)
        self.ExtenderPos = ExtenderLeft

        self.CurPluginID = -1
        self.LCD1 = bytearray([0xF0, 0x00, 0x00, 0x66, 0x14, 0x12,0])
        self.LCD2 = bytearray([0xF0, 0x00, 0x00, 0x67, 0x15, 0x13,0])
        self.MasterPeak = 0
        self.Msg1=''
        self.Msg2=''
    def OnInit(self):

        self.FirstTrackT[0] = 1
        self.FirstTrack = 0
        self.SmoothSpeed = 469
        self.Clicking = True

        device.setHasMeters()
        self.LastTimeMsg = bytearray(10)

        for m in range(0, len(self.FreeCtrlT)):
            self.FreeCtrlT[m] = 8192  # default free faders to center
        if device.isAssigned():
            device.midiOutSysex(
                bytes([0xF0, 0x00, 0x00, 0x66, 0x14, 0x0C, 1, 0xF7]))

        self.SetBackLight(2)  # backlight timeout to 2 minutes
        self.UpdateClicking()
        self.UpdateMeterMode()

        self.SetPage(self.Page)
        #self.SendMsg2('Linked to ' + ui.getProgTitle() + ' (' + ui.getVersion() + ')', 2000)
        #print('OnInit ready')

    def OnDeInit(self):

        if device.isAssigned():

            for m in range(0, 8):
                device.midiOutSysex(
                    bytes([0xF0, 0x00, 0x00, 0x66, 0x14, 0x20, m, 0, 0xF7]))
            if ui.isClosing():
                self.SendMsg(ui.getProgTitle() + ' session closed at ' +
                             time.ctime(time.time()), 0)
            else:
                self.SendMsg('')

            self.SendMsg('', 1)
            self.SendTimeMsg('')
            self.SendAssignmentMsg('  ')

       #print('OnDeInit ready')

    def OnDirtyMixerTrack(self, SetTrackNum):
         for m in range(0, len(self.ColT)):
            if (self.ColT[m].TrackNum == SetTrackNum) | (SetTrackNum == -1):
                self.ColT[m].Dirty = True

    def OnRefresh(self, flags):

        if flags & midi.HW_Dirty_Mixer_Sel:
            self.UpdateMixer_Sel()

        if flags & midi.HW_Dirty_Mixer_Display:
            self.UpdateTextDisplay()
            self.UpdateColT()

        if flags & midi.HW_Dirty_Mixer_Controls:
            for n in range(0, len(self.ColT)):
                if self.ColT[n].Dirty:
                    self.UpdateCol(n)

        # LEDs
        if flags & midi.HW_Dirty_LEDs:
            self.UpdateLEDs()

    def TrackSel(self, Index, Step):
        Index = 2 - Index
        device.baseTrackSelect(Index, Step)
        if Index == 0:
            s = channels.getChannelName(channels.channelNumber())
            self.SendMsg2(self.ArrowsStr + 'Channel: ' + s, 500)
        elif Index == 1:
            self.SendMsg2(self.ArrowsStr + 'Mixer track: ' +
                               mixer.getTrackName(mixer.trackNumber()), 500)
        elif Index == 2:
            s = patterns.getPatternName(patterns.patternNumber())
            self.SendMsg2(self.ArrowsStr + 'Pattern: ' + s, 500)

    def Jog(self, event):
        if self.JogSource == 0:
            if self.Scrub:
                # there is no scrub equivalent, it would be great to implement jog at lower scale (not just by bars)
                transport.globalTransport(
                    midi.FPT_Jog2, event.outEv, event.pmeFlags)
            else:
                transport.globalTransport(
                    midi.FPT_Jog, event.outEv, event.pmeFlags)  # relocate
        elif self.JogSource == MackieCUNote_Nudge:
            # TODO implement option to move clips
            transport.globalTransport(
                midi.FPT_MoveJog, event.outEv, event.pmeFlags)
        elif self.JogSource == MackieCUNote_Marker:
            if self.Shift:
                s = 'Marker selection'
            else:
                s = 'Marker jump'
            if event.outEv != 0:
                if transport.globalTransport(midi.FPT_MarkerJumpJog + int(self.Shift), event.outEv, event.pmeFlags) == midi.GT_Global:
                    s = ui.getHintMsg()
            self.SendMsg2(self.ArrowsStr + s, 500)

        elif self.JogSource == MackieCUNote_Undo:
            if event.outEv == 0:
                s = 'Undo history'
            elif transport.globalTransport(midi.FPT_UndoJog, event.outEv, event.pmeFlags) == midi.GT_Global:
                s = ui.GetHintMsg()
            self.SendMsg2(self.ArrowsStr + s + ' (level ' +
                               general.getUndoLevelHint() + ')', 500)

        elif self.JogSource == MackieCUNote_Zoom:
            if event.outEv != 0:
                transport.globalTransport(
                    midi.FPT_HZoomJog + int(self.Shift), event.outEv, event.pmeFlags)

        elif self.JogSource == MackieCUNote_Trim:

            if event.outEv != 0:
                transport.globalTransport(
                    midi.FPT_WindowJog, event.outEv, event.pmeFlags)
            # Application.ProcessMessages
            s = ui.getFocusedFormCaption()
            if s != "":
                self.SendMsg2(
                    self.ArrowsStr + 'Current window: ' + s, 500)

        elif (self.JogSource == MackieCUNote_Inputs) & (event.outEv == 0):
            self.SetFirstTrack(mixer.trackNumber())
            ui.showWindow(midi.widMixer)
            ui.setFocused(midi.widMixer)

        elif (self.JogSource == MackieCUNote_MidiTracks) | (self.JogSource == MackieCUNote_Inputs):
            self.TrackSel(self.JogSource -
                          MackieCUNote_MidiTracks, event.outEv)
            if self.JogSource == MackieCUNote_MidiTracks:
                ui.showWindow(midi.widPlaylist)
                ui.setFocused(midi.widPlaylist)
            elif self.JogSource == MackieCUNote_Inputs:
                ui.showWindow(midi.widMixer)
                ui.setFocused(midi.widMixer)
        elif self.JogSource == MackieCUNote_AudioInst:
            ui.showWindow(midi.widChannelRack)
            ui.setFocused(midi.widChannelRack)
            self.TrackSel(2, event.outEv)

        elif (self.JogSource == MackieCUNote_Outputs):
            ui.showWindow(midi.widMixer)
            ui.setFocused(midi.widMixer)
            self.SetFirstTrack(0 + event.outEv)

        elif (self.JogSource == MackieCUNote_Buses):
            ui.showWindow(midi.widMixer)
            ui.setFocused(midi.widMixer)
            x = 125
            while (x > 0):
                trackName = mixer.getTrackName(x)
                x -= 1
                if trackName.startswith('Insert '):
                    break
            self.SetFirstTrack(x+2)

        elif self.JogSource == MackieCUNote_User:
            ui.showWindow(midi.widBrowser)
            ui.setFocused(midi.widBrowser)

        elif self.JogSource == MackieCUNote_AudioInst:

            if event.outEv != 0:
                channels.processRECEvent(midi.REC_Tempo, channels.incEventValue(midi.REC_Tempo, event.outEv, midi.EKRes),
                                         midi.PME_RECFlagsT[int(event.pmeFlags & midi.PME_LiveInput != 0)] & (not midi.REC_FromMIDI))
            self.SendMsg2(self.ArrowsStr + 'Tempo: ' +
                               mixer.getEventIDValueString(midi.REC_Tempo, mixer.getCurrentTempo()), 500)

        elif self.JogSource in [MackieCUNote_Aux, MackieCUNote_Buses, MackieCUNote_Outputs, MackieCUNote_User]:
            # CC
            event.data1 = 390 + self.JogSource - MackieCUNote_Aux

            if event.outEv != 0:
                event.isIncrement = 1
                s = chr(0x7E + int(event.outEv < 0))
                self.SendMsg2(self.ArrowsStr + 'Free jog ' +
                                   str(event.data1) + ': ' + s, 500)
                device.processMIDICC(event)
                return
            else:
                self.SendMsg2(
                    self.ArrowsStr + 'Free jog ' + str(event.data1), 500)
        self.UpdateLEDs()

    def OnMidiMsg(self, event):

        ArrowStepT = [2, -2, -1, 1]
        CutCopyMsgT = ('Cut', 'Copy', 'Paste', 'Insert',
                       'Delete')  # FPT_Cut..FPT_Delete
        #print(event.midiId, event.data1, event.data2)

        if (event.midiId == midi.MIDI_CONTROLCHANGE):
            if (event.midiChan == 0):
                event.inEv = event.data2
                if event.inEv >= 0x40:
                    event.outEv = -(event.inEv - 0x40)
                else:
                    event.outEv = event.inEv

                if event.data1 == MackieCUNote_F7:
                    self.Jog(event)
                    event.handled = True
                # knobs
                elif event.data1 in [0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17]:
                    r = utils.KnobAccelToRes2(event.outEv)  # todo outev signof
                    Res = r * (1 / (40 * 2.5))
                    if self.Page == MackieCUPage_Free:
                        i = event.data1 - 0x10
                        self.ColT[i].Peak = self.ActivityMax
                        event.data1 = self.ColT[i].BaseEventID + \
                            int(self.ColT[i].KnobHeld)
                        event.isIncrement = 1
                        s = chr(0x7E + int(event.outEv < 0))
                        self.SendMsg2(
                            'Free knob ' + str(event.data1) + ': ' + s, 500)
                        device.processMIDICC(event)
                        device.hardwareRefreshMixerTrack(self.ColT[i].TrackNum)
                    else:
                        self.SetKnobValue(event.data1 - 0x10, event.outEv, Res)
                        event.handled = True
                else:
                    event.handled = False  # for extra CCs in emulators
            else:
                event.handled = False  # for extra CCs in emulators

        elif event.midiId == midi.MIDI_PITCHBEND:  # pitch bend (faders)

            if event.midiChan <= 8:
                event.inEv = event.data1 + (event.data2 << 7)
                event.outEv = (event.inEv << 16) // 16383
                event.inEv -= 0x2000

                if self.Page == MackieCUPage_Free:
                    self.ColT[event.midiChan].Peak = self.ActivityMax
                    self.FreeCtrlT[self.ColT[event.midiChan].TrackNum] = event.data1 + \
                        (event.data2 << 7)
                    device.hardwareRefreshMixerTrack(
                        self.ColT[event.midiChan].TrackNum)
                    event.data1 = self.ColT[event.midiChan].BaseEventID + 7
                    event.midiChan = 0
                    event.midiChanEx = event.midiChanEx & (not 0xF)
                    self.SendMsg2('Free slider ' + str(event.data1) + ': ' +
                                       ui.getHintValue(event.outEv, midi.FromMIDI_Max), 500)
                    device.processMIDICC(event)
                elif self.ColT[event.midiChan].SliderEventID >= 0:
                    # slider (mixer track volume)
                    if self.ColT[event.midiChan].TrackNum >= 0:
                        if mixer.trackNumber != self.ColT[event.midiChan].TrackNum:
                            mixer.setTrackNumber(
                                self.ColT[event.midiChan].TrackNum)

                    event.handled = True
                    mixer.automateEvent(self.ColT[event.midiChan].SliderEventID, self.AlphaTrack_SliderToLevel(
                        event.inEv + 0x2000), midi.REC_MIDIController, self.SmoothSpeed)
                    # hint
                    n = mixer.getAutoSmoothEventValue(
                        self.ColT[event.midiChan].SliderEventID)
                    s = mixer.getEventIDValueString(
                        self.ColT[event.midiChan].SliderEventID, n)
                    if s != '':
                        s = ': ' + s
                    self.SendMsg2(
                        self.ColT[event.midiChan].SliderName + s, 500)

        elif (event.midiId == midi.MIDI_NOTEON) | (event.midiId == midi.MIDI_NOTEOFF):  # NOTE
            if event.midiId == midi.MIDI_NOTEON:
                # slider hold
                if event.data1 in [0x68, 0x69, 0x70]:
                    self.SliderHoldCount += -1 + (int(event.data2 > 0) * 2)

                if (event.pmeFlags & midi.PME_System != 0):
                    # F1..F8
                    if self.Shift & (event.data1 in [MackieCUNote_F1, MackieCUNote_F2, MackieCUNote_F3, MackieCUNote_F4, MackieCUNote_F5, MackieCUNote_F6, MackieCUNote_F7, MackieCUNote_F8]):
                        transport.globalTransport(midi.FPT_F1 - MackieCUNote_F1 +
                                                  event.data1, int(event.data2 > 0) * 2, event.pmeFlags)
                        event.data1 = 0xFF

                    if self.Control & (event.data1 in [MackieCUNote_F1, MackieCUNote_F2, MackieCUNote_F3, MackieCUNote_F4, MackieCUNote_F5, MackieCUNote_F6, MackieCUNote_F7, MackieCUNote_F8]):
                        ui.showWindow(midi.widPlaylist)
                        ui.setFocused(midi.widPlaylist)
                        transport.globalTransport(midi.FPT_Menu, int(
                            event.data2 > 0) * 2, event.pmeFlags)
                        time.sleep(0.1)
                        f = int(1 + event.data1 - MackieCUNote_F1)
                        for x in range(0, f):
                            transport.globalTransport(midi.FPT_Down, int(
                                event.data2 > 0) * 2, event.pmeFlags)
                            time.sleep(0.01)
                        time.sleep(0.1)
                        transport.globalTransport(midi.FPT_Enter, int(
                            event.data2 > 0) * 2, event.pmeFlags)
                        event.data1 = 0xFF

                    if event.data1 == 0x34:  # display mode
                        if event.data2 > 0:
                            if self.Shift:
                                self.ExtenderPos = abs(self.ExtenderPos - 1)
                                self.FirstTrackT[self.FirstTrack] = 1
                                self.SetPage(self.Page)
                                self.SendMsg2(
                                    'Extender on ' + self.MackieCU_ExtenderPosT[self.ExtenderPos], 1500)
                            else:
                                self.MeterMode = (self.MeterMode + 1) % 3
                                self.SendMsg2(
                                    self.MackieCU_MeterModeNameT[self.MeterMode])
                                self.UpdateMeterMode()
                                device.dispatch(0, midi.MIDI_NOTEON +
                                                (event.data1 << 8) + (event.data2 << 16))
                    elif event.data1 == 0x35:  # time format
                        if event.data2 > 0:
                            ui.setTimeDispMin()
                    elif (event.data1 == MackieCUNote_Bank_Previous) | (event.data1 == MackieCUNote_Bank_Next):  # mixer bank
                        if event.data2 > 0:
                            self.SetFirstTrack(
                                self.FirstTrackT[self.FirstTrack] - 8 + int(event.data1 == MackieCUNote_Bank_Next) * 16)
                            device.dispatch(0, midi.MIDI_NOTEON +
                                            (event.data1 << 8) + (event.data2 << 16))

                            if (self.CurPluginID != -1):  # Selected Plugin
                                if (event.data1 == MackieCUNote_Bank_Previous) & (self.PluginParamOffset >= 8):
                                    self.PluginParamOffset -= 8
                                elif (event.data1 == MackieCUNote_Bank_Next) & (self.PluginParamOffset + 8 < plugins.getParamCount(mixer.trackNumber(), self.CurPluginID + self.CurPluginOffset) - 8):
                                    self.PluginParamOffset += 8
                            else:  # No Selected Plugin
                                if (event.data1 == MackieCUNote_Bank_Previous) & (self.CurPluginOffset >= 2):
                                    self.CurPluginOffset -= 2
                                elif (event.data1 == MackieCUNote_Bank_Next) & (self.CurPluginOffset < 2):
                                    self.CurPluginOffset += 2

                    elif (event.data1 == MackieCUNote_Channel_Previous) | (event.data1 == MackieCUNote_Channel_Next):
                        if event.data2 > 0:
                            self.SetFirstTrack(self.FirstTrackT[self.FirstTrack] -
                                               1 + int(event.data1 == MackieCUNote_Channel_Next) * 2)
                            device.dispatch(0, midi.MIDI_NOTEON +
                                            (event.data1 << 8) + (event.data2 << 16))

                            if (self.CurPluginID != -1):  # Selected Plugin
                                if (event.data1 == MackieCUNote_Channel_Previous) & (self.PluginParamOffset > 0):
                                    self.PluginParamOffset -= 1
                                elif (event.data1 == MackieCUNote_Channel_Next) & (self.PluginParamOffset < plugins.getParamCount(mixer.trackNumber(), self.CurPluginID + self.CurPluginOffset) - 8):
                                    self.PluginParamOffset += 1
                            else:  # No Selected Plugin
                                if (event.data1 == MackieCUNote_Channel_Previous) & (self.CurPluginOffset > 0):
                                    self.CurPluginOffset -= 1
                                elif (event.data1 == MackieCUNote_Channel_Next) & (self.CurPluginOffset < 2):
                                    self.CurPluginOffset += 1

                    elif event.data1 == 0x32:  # self.Flip
                        if event.data2 > 0:
                            self.Flip = not self.Flip
                            device.dispatch(0, midi.MIDI_NOTEON +
                                            (event.data1 << 8) + (event.data2 << 16))
                            self.UpdateColT()
                            self.UpdateLEDs()
                    elif event.data1 == 0x33:  # smoothing
                        if event.data2 > 0:
                            self.SmoothSpeed = int(self.SmoothSpeed == 0) * 469
                            self.UpdateLEDs()
                            self.SendMsg2('Control smoothing ' +
                                               OffOnStr[int(self.SmoothSpeed > 0)])
                    elif event.data1 == MackieCUNote_Scrub:  # self.Scrub
                        if event.data2 > 0:
                            self.Scrub = not self.Scrub
                            self.UpdateLEDs()
          # jog sources
                    elif event.data1 in [MackieCUNote_Undo, MackieCUNote_MidiTracks, MackieCUNote_Inputs, MackieCUNote_AudioTracks, MackieCUNote_AudioInst, MackieCUNote_Aux, MackieCUNote_Buses, MackieCUNote_Outputs, MackieCUNote_User, MackieCUNote_Marker, MackieCUNote_Nudge, MackieCUNote_Zoom, MackieCUNote_Trim]:
                        # update jog source
                        self.SliderHoldCount += -1 + (int(event.data2 > 0) * 2)
                        if event.data1 in [MackieCUNote_Zoom, MackieCUNote_Trim]:
                            device.directFeedback(event)
                        if event.data2 == 0:
                            if self.JogSource == event.data1:
                                self.SetJogSource(0)
                        else:
                            self.SetJogSource(event.data1)
                            event.outEv = 0
                            self.Jog(event)  # for visual feedback

                    # arrows
                    elif event.data1 in [MackieCUNote_Up, MackieCUNote_Down, MackieCUNote_Left, MackieCUNote_Right]:
                        if self.JogSource == MackieCUNote_Zoom:
                            if event.data1 == MackieCUNote_Up:
                                transport.globalTransport(
                                    midi.FPT_VZoomJog + int(self.Shift), -1, event.pmeFlags)
                            elif event.data1 == MackieCUNote_Down:
                                transport.globalTransport(
                                    midi.FPT_VZoomJog + int(self.Shift), 1, event.pmeFlags)
                            elif event.data1 == MackieCUNote_Left:
                                transport.globalTransport(
                                    midi.FPT_HZoomJog + int(self.Shift), -1, event.pmeFlags)
                            elif event.data1 == MackieCUNote_Right:
                                transport.globalTransport(
                                    midi.FPT_HZoomJog + int(self.Shift), 1, event.pmeFlags)

                        elif self.JogSource == 0:
                            transport.globalTransport(
                                midi.FPT_Up - MackieCUNote_Up + event.data1, int(event.data2 > 0) * 2, event.pmeFlags)
                        else:
                            if event.data2 > 0:
                                event.inEv = ArrowStepT[event.data1 -
                                                        MackieCUNote_Up]
                                event.outEv = event.inEv
                                self.Jog(event)

                    elif event.data1 in [MackieCUNote_Pan,  MackieCUNote_Stereo, MackieCUNote_Sends, MackieCUNote_FX, MackieCUNote_EQ, MackieCUNote_Free]:  # self.Page
                        self.SliderHoldCount += -1 + (int(event.data2 > 0) * 2)
                        if event.data2 > 0:
                            n = event.data1 - 0x28
                            self.SendMsg2(self.MackieCU_PageNameT[n], 500)
                            self.SetPage(n)
                            device.dispatch(0, midi.MIDI_NOTEON +
                                            (event.data1 << 8) + (event.data2 << 16))

                    elif event.data1 == MackieCUNote_Shift:  # self.Shift
                        self.Shift = event.data2 > 0
                        device.directFeedback(event)

                    elif event.data1 == MackieCUNote_Alt:  # self.Alt
                        self.Alt = event.data2 > 0
                        device.directFeedback(event)

                    elif event.data1 == MackieCUNote_Control:  # self.Control
                        self.Control = event.data2 > 0
                        device.directFeedback(event)

                    elif event.data1 == MackieCUNote_Option:  # self.Option
                        self.Option = event.data2 > 0
                        device.directFeedback(event)

                    elif event.data1 == -1:  # open audio editor in current mixer track
                        device.directFeedback(event)
                        if event.data2 > 0:
                            ui.launchAudioEditor(False, '', mixer.trackNumber(),
                                                 'AudioLoggerTrack.fst', '')
                            self.SendMsg2('Audio editor ready')

                    elif event.data1 == MackieCUNote_Click:  # metronome/button self.Clicking
                        if event.data2 > 0:
                            if self.Shift:
                                self.Clicking = not self.Clicking
                                self.UpdateClicking()
                                self.SendMsg2(
                                    'self.Clicking ' + OffOnStr[self.Clicking])
                            else:
                                transport.globalTransport(
                                    midi.FPT_Metronome, 1, event.pmeFlags)

                    elif event.data1 == -1:  # precount
                        if event.data2 > 0:
                            transport.globalTransport(
                                midi.FPT_CountDown, 1, event.pmeFlags)

                    # cut/copy/paste/insert/delete
                    elif event.data1 in [MackieCUNote_F1, MackieCUNote_F2, MackieCUNote_F3, MackieCUNote_F4, MackieCUNote_F5]:
                        transport.globalTransport(midi.FPT_Cut + event.data1 -
                                                  MackieCUNote_F1, int(event.data2 > 0) * 2, event.pmeFlags)
                        if event.data2 > 0:
                            self.SendMsg2(
                                CutCopyMsgT[midi.FPT_Cut + event.data1 - MackieCUNote_F1 - 50])

                    elif (event.data1 == MackieCUNote_Rewind) | (event.data1 == MackieCUNote_Forward):  # << >>
                        if self.Shift:
                            if event.data2 == 0:
                                v2 = 1
                            elif event.data1 == MackieCUNote_Rewind:
                                v2 = 0.5
                            else:
                                v2 = 2
                            transport.setPlaybackSpeed(v2)
                        else:
                            transport.globalTransport(midi.FPT_Rewind + int(event.data1 ==
                                                                            MackieCUNote_Forward), int(event.data2 > 0) * 2, event.pmeFlags)
                        device.directFeedback(event)

                    elif event.data1 == MackieCUNote_Stop:  # stop
                        transport.globalTransport(midi.FPT_Stop, int(
                            event.data2 > 0) * 2, event.pmeFlags)
                    elif event.data1 == MackieCUNote_Start:  # play
                        transport.globalTransport(midi.FPT_Play, int(
                            event.data2 > 0) * 2, event.pmeFlags)
                    elif event.data1 == MackieCUNote_Record:  # record
                        transport.globalTransport(midi.FPT_Record, int(
                            event.data2 > 0) * 2, event.pmeFlags)
                    elif event.data1 == MackieCUNote_Solo:  # song/loop
                        transport.globalTransport(midi.FPT_Loop, int(
                            event.data2 > 0) * 2, event.pmeFlags)
                    # elif event.data1 == 0x59: # mode
                    #	transport.globalTransport(midi.FPT_Mode, int(event.data2 > 0) * 2, event.pmeFlags)
                    #	device.directFeedback(event)

                    elif event.data1 == MackieCUNote_Latch:  # snap
                        if self.Shift:
                            if event.data2 > 0:
                                transport.globalTransport(
                                    midi.FPT_SnapMode, 1, event.pmeFlags)
                            else:
                                transport.globalTransport(midi.FPT_Snap, int(
                                    event.data2 > 0) * 2, event.pmeFlags)

                    elif event.data1 == MackieCUNote_Cancel:  # ESC
                        transport.globalTransport(
                            midi.FPT_Escape + int(self.Shift) * 2, int(event.data2 > 0) * 2, event.pmeFlags)
                    elif event.data1 == MackieCUNote_Enter:  # ENTER
                        transport.globalTransport(
                            midi.FPT_Enter + int(self.Shift) * 2, int(event.data2 > 0) * 2, event.pmeFlags)
                    # knob reset
                    elif event.data1 in [0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27]:
                        if self.Page == MackieCUPage_Free:
                            i = event.data1 - 0x20
                            self.ColT[i].KnobHeld = event.data2 > 0
                            if event.data2 > 0:
                                self.ColT[i].Peak = self.ActivityMax
                                event.data1 = self.ColT[i].BaseEventID + 2
                                event.outEv = 0
                                event.isIncrement = 2
                                self.SendMsg2(
                                    'Free knob switch ' + str(event.data1), 500)
                                device.processMIDICC(event)
                            device.hardwareRefreshMixerTrack(
                                self.ColT[i].TrackNum)
                            return
                        elif event.data2 > 0:
                            n = event.data1 - 0x20
                            if self.Page == MackieCUPage_Sends:
                                if mixer.setRouteTo(mixer.trackNumber(), self.ColT[n].TrackNum, -1) < 0:
                                    self.SendMsg2(
                                        'Cannot send to this track')
                                else:
                                    mixer.afterRoutingChanged()
                            else:
                                self.SetKnobValue(n, midi.MaxInt)

                    elif (event.data1 >= 0) & (event.data1 <= MackieCUNote_Select8):  # free hold buttons
                        if self.Page == MackieCUPage_Free:
                            i = event.data1 % 8
                            self.ColT[i].Peak = self.ActivityMax
                            event.data1 = self.ColT[i].BaseEventID + \
                                3 + event.data1 // 8
                            event.inEv = event.data2
                            event.outEv = int(event.inEv > 0) * \
                                midi.FromMIDI_Max
                            self.SendMsg2('Free button ' + str(event.data1) +
                                               ': ' + OffOnStr[event.outEv > 0], 500)
                            device.processMIDICC(event)
                            device.hardwareRefreshMixerTrack(
                                self.ColT[i].TrackNum)
                            return

                if (event.pmeFlags & midi.PME_System_Safe != 0):
                    if event.data1 == 0x47:  # link selected channels to current mixer track
                        if event.data2 > 0:
                            if self.Shift:
                                mixer.linkTrackToChannel(
                                    midi.ROUTE_StartingFromThis)
                            else:
                                mixer.linkTrackToChannel(midi.ROUTE_ToThis)
                    elif event.data1 == MackieCUNote_Read:  # focus browser
                        if event.data2 > 0:
                            ui.showWindow(midi.widBrowser)

                    elif event.data1 == MackieCUNote_Write:  # focus step seq
                        if event.data2 > 0:
                            ui.showWindow(midi.widChannelRack)

                    elif event.data1 == MackieCUNote_F8:  # menu
                        transport.globalTransport(midi.FPT_Menu, int(
                            event.data2 > 0) * 2, event.pmeFlags)
                        if event.data2 > 0:
                            self.SendMsg2('Menu', 10)

                    elif event.data1 == MackieCUNote_F6:  # tools
                        transport.globalTransport(midi.FPT_ItemMenu, int(
                            event.data2 > 0) * 2, event.pmeFlags)
                        if event.data2 > 0:
                            self.SendMsg2('Tools', 10)

                    elif event.data1 == MackieCUNote_Undo:  # undo/redo
                        if (transport.globalTransport(midi.FPT_Undo, int(event.data2 > 0) * 2, event.pmeFlags) == midi.GT_Global) & (event.data2 > 0):
                            self.SendMsg2(
                                ui.getHintMsg() + ' (level ' + GetUndoLevelStr + ')')

                    # punch in/punch out/punch
                    elif event.data1 in [MackieCUNote_Cycle, MackieCUNote_Drop, MackieCUNote_Replace]:
                        if event.data1 == MackieCUNote_Cycle:
                            n = midi.FPT_Punch
                        else:
                            n = midi.FPT_PunchIn + event.data1 - MackieCUNote_Drop
                        if event.data1 >= MackieCUNote_Replace:
                            self.SliderHoldCount += -1 + \
                                (int(event.data2 > 0) * 2)
                        if not ((event.data1 == MackieCUNote_Drop) & (event.data2 == 0)):
                            device.directFeedback(event)
                        if (event.data1 >= MackieCUNote_Replace) & (event.data2 >= int(event.data1 == MackieCUNote_Replace)):
                            if device.isAssigned():
                                device.midiOutMsg((MackieCUNote_Drop << 8) +
                                                  midi.TranzPort_OffOnT[False])
                        if transport.globalTransport(n, int(event.data2 > 0) * 2, event.pmeFlags) == midi.GT_Global:
                            t = -1
                            if n == midi.FPT_Punch:
                                if event.data2 != 1:
                                    t = int(event.data2 != 2)
                            elif event.data2 > 0:
                                t = int(n == midi.FPT_PunchOut)
                            if t >= 0:
                                self.SendMsg2(ui.getHintMsg())

                    elif (event.data1 == MackieCUNote_Marker) & (self.Control):  # marker add
                        if (transport.globalTransport(midi.FPT_AddMarker + int(self.Shift), int(event.data2 > 0) * 2, event.pmeFlags) == midi.GT_Global) & (event.data2 > 0):
                            self.SendMsg2(ui.getHintMsg())
                    # select mixer track
                    elif (event.data1 >= MackieCUNote_Select1) & (event.data1 <= MackieCUNote_Select8):
                        if event.data2 > 0:
                            i = event.data1 - MackieCUNote_Select1

                            ui.showWindow(midi.widMixer)
                            ui.setFocused(midi.widMixer)
                            self.UpdateLEDs()
                            mixer.setTrackNumber(
                                self.ColT[i].TrackNum, midi.curfxScrollToMakeVisible | midi.curfxMinimalLatencyUpdate)

                            if self.Control:  # Link channel to track
                                mixer.linkTrackToChannel(midi.ROUTE_ToThis)
                            #Show Full Trackname on second display:
                            SendMsg2(mixer.getTrackName(self.ColT[i].TrackNum))
                    elif (event.data1 >= 0x8) & (event.data1 <= 0xF):  # solo
                        if event.data2 > 0:
                            i = event.data1 - 0x8
                            self.ColT[i].solomode = midi.fxSoloModeWithDestTracks
                            if self.Shift:
                                Include(self.ColT[i].solomode,
                                        midi.fxSoloModeWithSourceTracks)
                            mixer.soloTrack(self.ColT[i].TrackNum,
                                            midi.fxSoloToggle, self.ColT[i].solomode)
                            mixer.setTrackNumber(
                                self.ColT[i].TrackNum, midi.curfxScrollToMakeVisible)

                    elif (event.data1 >= 0x10) & (event.data1 <= 0x17):  # mute
                        if event.data2 > 0:
                            mixer.enableTrack(
                                self.ColT[event.data1 - 0x10].TrackNum)

                    elif (event.data1 >= 0x0) & (event.data1 <= 0x7):  # arm
                        if event.data2 > 0:
                            mixer.armTrack(self.ColT[event.data1].TrackNum)
                            if mixer.isTrackArmed(self.ColT[event.data1].TrackNum):
                                self.SendMsg2(mixer.getTrackName(
                                    self.ColT[event.data1].TrackNum) + ' recording to ' + mixer.getTrackRecordingFileName(self.ColT[event.data1].TrackNum), 2500)
                            else:
                                self.SendMsg2(mixer.getTrackName(
                                    self.ColT[event.data1].TrackNum) + ' unarmed')

                    elif event.data1 == MackieCUNote_Save:  # save/save new
                        transport.globalTransport(
                            midi.FPT_Save + int(self.Shift), int(event.data2 > 0) * 2, event.pmeFlags)

                    event.handled = True
                else:
                    event.handled = False
            else:
                event.handled = False

    def SendMsg(self, Msg, Row = 0,Display=1):
        if Display==1:
            sysex = self.LCD1 + bytearray(Msg, 'utf-8')
            sysex.append(0xF7)
            device.midiOutSysex(bytes(sysex))
        elif Display==2:
            sysex = bytearray([0xF0, 0x00, 0x00, 0x67, 0x15, 0x13, (self.LastMsgLen + 1) * Row]) + bytearray(Msg.ljust(self.LastMsgLen + 1, ' '), 'utf-8')
            sysex.append(0xF7)
            device.midiOutSysex(bytes(sysex))
        elif Display==3:
             ui.setHintMsg(Msg)
 
    def SendMsg2(self, Msg, Duration=1000):
        self.SendMsg('  '+Msg.ljust(54, ' '),0, 2)

   # update the CU time display
    def SendTimeMsg(self, Msg):

        TempMsg = bytearray(10)
        for n in range(0, len(Msg)):
            TempMsg[n] = ord(Msg[n])

        if device.isAssigned():
            # send chars that have changed
            for m in range(0, min(len(self.LastTimeMsg), len(TempMsg))):
                if self.LastTimeMsg[m] != TempMsg[m]:
                    device.midiOutMsg(midi.MIDI_CONTROLCHANGE +
                                      ((0x49 - m) << 8) + ((TempMsg[m]) << 16))

        self.LastTimeMsg = TempMsg

    def SendAssignmentMsg(self, Msg):
        if (len(Msg) < 3):
            Msg = ' ' + Msg

        device.midiOutMsg(midi.MIDI_CONTROLCHANGE +
                          ((0x4B) << 8) + (ord(Msg[1]) << 16))
        device.midiOutMsg(midi.MIDI_CONTROLCHANGE +
                          ((0x4A) << 8) + (ord(Msg[2]) << 16))

    def UpdateTempMsg(self):

        self.SendMsg(self.TempMsgT[int(self.TempMsgCount != 0)])

    def UpdateTextDisplay(self):
        s1 = ''
        s2 = ''
        s3 = '  '
        for m in range(0, len(self.ColT) - 1):
            s = ''
            sa = ''
            sa2 = ''
            if self.Page == MackieCUPage_Free:
                s = '  ' + utils.Zeros(self.ColT[m].TrackNum + 1, 2, ' ')
            else:
                s = mixer.getTrackName(self.ColT[m].TrackNum, 6)
                sa = '   '+str(self.ColT[m].TrackNum)+' '
                if self.ColT[m].TrackNum>99:
                    sa2 = 'C'+str(self.ColT[m].TrackNum).zfill(2)+'  '
                else:
                    sa2 = 'CH'+str(self.ColT[m].TrackNum).zfill(2)+'  '
            for n in range(1, 7 - len(s) + 1):
                s = s + ' '
            for n in range(1, 7 - len(sa) + 1):
                sa = sa + ' '
            s1 = s1 + s
            s2 = s2 + sa
            s3 = s3 + sa2
        self.SendMsg(s1+s2)
        self.SendMsg(s3[0:105]+ 'MASTER ',1,2)

    def OnUpdateBeatIndicator(self, Value):

        SyncLEDMsg = [midi.MIDI_NOTEON + (MackieCUNote_Start << 8), midi.MIDI_NOTEON + (
            MackieCUNote_Start << 8) + (0x7F << 16), midi.MIDI_NOTEON + (MackieCUNote_Start << 8) + (0x7F << 16)]

        if device.isAssigned():
            device.midiOutNewMsg(SyncLEDMsg[Value], 128)


    def UpdateMeterMode(self):
 
        # force vertical (activity) meter mode for free controls self.Page
        if self.Page == MackieCUPage_Free:
            self.CurMeterMode = 1
        else:
            self.CurMeterMode = self.MeterMode

        if device.isAssigned():
            # clear peak indicators
            for m in range(0, len(self.ColT) - 1):
                device.midiOutMsg(midi.MIDI_CHANAFTERTOUCH +
                                  (0xF << 8) + (m << 12))
            # disable all meters
            for m in range(0, 8):
                device.midiOutSysex(bytes([0xF0, 0x00, 0x00, 0x66, 0x14, 0x20, m, 0, 0xF7]))

        # reset stuff
        if self.CurMeterMode > 0:
            self.TempMsgCount = -1
        else:
            self.TempMsgCount = 500 // 48 + 1

        # $D for horizontal, $E for vertical meters
        self.MeterMax = 0xD + int(self.CurMeterMode == 1)
        self.ActivityMax = 0xD - int(self.CurMeterMode == 1) * 6

        # meter split marks
        if self.CurMeterMode == 0:
            s2 = ''
            for m in range(0, len(self.ColT) - 1):
                s2 = s2 + '      .'
            self.SendMsg(s2, 1)
        else:
            self.UpdateTextDisplay()

        if device.isAssigned():
            # horizontal/vertical meter mode
            device.midiOutSysex(
                bytes([0xF0, 0x00, 0x00, 0x66, 0x14, 0x21, int(self.CurMeterMode > 0), 0xF7]))

            # enable all meters
            if self.CurMeterMode == 2:
                n = 1
            else:
                n = 1 + 2
            for m in range(0, 8):
                device.midiOutSysex(bytes([0xF0, 0x00, 0x00, 0x66, 0x14, 0x20, m, n, 0xF7]))
 
    def OnUpdateMeters(self):

        if self.Page != MackieCUPage_Free:
            for m in range(0, len(self.ColT) - 1):
                self.ColT[m].Peak = max(self.ColT[m].Peak, round(mixer.getTrackPeaks(self.ColT[m].TrackNum, midi.PEAK_LR_INV) * self.MeterMax))
            #print(self.ColT[3].Peak)
            n = max(0,round(mixer.getTrackPeaks(MasterPeak, 0) * self.MeterMax))
            device.midiOutSysex(bytes(bytearray([0xd1,n,0xF7])))
            n = max(0,round(mixer.getTrackPeaks(MasterPeak, 1) * self.MeterMax))
            device.midiOutSysex(bytes(bytearray([0xd1,n+16,0xF7])))
 
    def SetPage(self, Value):

        oldPage = self.Page
        self.Page = Value

        self.FirstTrack = int(self.Page == MackieCUPage_Free)
        receiverCount = device.dispatchReceiverCount()
        if receiverCount == 0:
            self.SetFirstTrack(self.FirstTrackT[self.FirstTrack])
        elif self.Page == oldPage:
            if self.ExtenderPos == ExtenderLeft:
                for n in range(0, receiverCount):
                    device.dispatch(n, midi.MIDI_NOTEON + (0x7F << 8) +
                                    (self.FirstTrackT[self.FirstTrack] + (n * 8) << 16))
                self.SetFirstTrack(
                    self.FirstTrackT[self.FirstTrack] + receiverCount * 8)
            elif self.ExtenderPos == ExtenderRight:
                self.SetFirstTrack(self.FirstTrackT[self.FirstTrack])
                for n in range(0, receiverCount):
                    device.dispatch(n, midi.MIDI_NOTEON + (0x7F << 8) +
                                    (self.FirstTrackT[self.FirstTrack] + ((n + 1) * 8) << 16))

        if self.Page == MackieCUPage_Free:

            BaseID = midi.EncodeRemoteControlID(
                device.getPortNumber(), 0, self.FreeEventID + 7)
            for n in range(0,  len(self.FreeCtrlT)):
                d = mixer.remoteFindEventValue(BaseID + n * 8, 1)
                if d >= 0:
                    self.FreeCtrlT[n] = min(round(d * 16384), 16384)

        if (oldPage == MackieCUPage_Free) | (self.Page == MackieCUPage_Free):
            self.UpdateMeterMode()

        self.CurPluginID = -1
        self.CurPluginOffset = 0

        self.UpdateColT()
        self.UpdateLEDs()
        self.UpdateTextDisplay()

    def UpdateMixer_Sel(self):

        if self.Page != MackieCUPage_Free:
            if device.isAssigned():
                for m in range(0, len(self.ColT) - 1):
                    device.midiOutNewMsg(((MackieCUNote_Select1 + m) << 8) +
                                         midi.TranzPort_OffOnT[self.ColT[m].TrackNum == mixer.trackNumber()], self.ColT[m].LastValueIndex + 4)

            if self.Page in [MackieCUPage_Sends, MackieCUPage_FX]:
                self.UpdateColT()

    def UpdateCol(self, Num):

        data1 = 0
        data2 = 0
        baseID = 0
        center = 0
        b = False

        if device.isAssigned():
            if self.Page == MackieCUPage_Free:
                baseID = midi.EncodeRemoteControlID(
                    device.getPortNumber(), 0, self.ColT[Num].BaseEventID)
                # slider
                m = self.FreeCtrlT[self.ColT[Num].TrackNum]
                device.midiOutNewMsg(midi.MIDI_PITCHBEND + Num + ((m & 0x7F)
                                                                  << 8) + ((m >> 7) << 16), self.ColT[Num].LastValueIndex + 5)
                if Num < 8:
                    # ring
                    d = mixer.remoteFindEventValue(
                        baseID + int(self.ColT[Num].KnobHeld))
                    if d >= 0:
                        m = 1 + round(d * 10)
                    else:
                        m = int(self.ColT[Num].KnobHeld) * (11 + (2 << 4))
                    device.midiOutNewMsg(midi.MIDI_CONTROLCHANGE + (
                        (MackieCUNote_Channel_Previous + Num) << 8) + (m << 16), self.ColT[Num].LastValueIndex)
                    # buttons
                    for n in range(0, 4):
                        d = mixer.remoteFindEventValue(baseID + 3 + n)
                        if d >= 0:
                            b = d >= 0.5
                        else:
                            b = False

                        device.midiOutNewMsg(
                            ((n * 8 + Num) << 8) + midi.TranzPort_OffOnT[b], self.ColT[Num].LastValueIndex + 1 + n)
            else:
                sv = mixer.getEventValue(self.ColT[Num].SliderEventID)

                if Num < 8:
                    # V-Pot
                    center = self.ColT[Num].KnobCenter
                    if self.ColT[Num].KnobEventID >= 0:
                        m = mixer.getEventValue(
                            self.ColT[Num].KnobEventID, midi.MaxInt, False)
                        if center < 0:
                            if self.ColT[Num].KnobResetEventID == self.ColT[Num].KnobEventID:
                                center = int(
                                    m != self.ColT[Num].KnobResetValue)
                            else:
                                center = int(
                                    sv != self.ColT[Num].KnobResetValue)

                        if self.ColT[Num].KnobMode < 2:
                            data1 = 1 + round(m * (10 / midi.FromMIDI_Max))
                        else:
                            data1 = round(m * (11 / midi.FromMIDI_Max))
                        if self.ColT[Num].KnobMode > 3:
                            data1 = (center << 6)
                        else:
                            data1 = data1 + \
                                (self.ColT[Num].KnobMode << 4) + (center << 6)
                    else:
                        data1 = 0

                        if self.Page == MackieCUPage_FX:
                            # Plugin Parameter Value
                            paramValue = plugins.getParamValue(int(
                                Num + self.PluginParamOffset), mixer.trackNumber(), int(self.CurPluginID + self.CurPluginOffset))
                            data1 = int(paramValue)
                            # TODO fix when getParamValue starts working

                    device.midiOutNewMsg(midi.MIDI_CONTROLCHANGE + (
                        (MackieCUNote_Channel_Previous + Num) << 8) + (data1 << 16), self.ColT[Num].LastValueIndex)

                    # arm, solo, mute
                    device.midiOutNewMsg(((0x00 + Num) << 8) + midi.TranzPort_OffOnBlinkT[int(mixer.isTrackArmed(
                        self.ColT[Num].TrackNum)) * (1 + int(transport.isRecording()))], self.ColT[Num].LastValueIndex + 1)
                    device.midiOutNewMsg(((0x08 + Num) << 8) + midi.TranzPort_OffOnT[mixer.isTrackSolo(
                        self.ColT[Num].TrackNum)], self.ColT[Num].LastValueIndex + 2)
                    device.midiOutNewMsg(((0x10 + Num) << 8) + midi.TranzPort_OffOnT[not mixer.isTrackEnabled(
                        self.ColT[Num].TrackNum)], self.ColT[Num].LastValueIndex + 3)

                # slider
                data1 = self.AlphaTrack_LevelToSlider(sv)
                data2 = data1 & 127
                data1 = data1 >> 7
                device.midiOutNewMsg(midi.MIDI_PITCHBEND + Num + (data2 << 8) +
                                     (data1 << 16), self.ColT[Num].LastValueIndex + 5)

            Dirty = False

    def AlphaTrack_LevelToSlider(self, Value, Max=midi.FromMIDI_Max):

        return round(Value / Max * self.AlphaTrack_SliderMax)

    def AlphaTrack_SliderToLevel(self, Value, Max=midi.FromMIDI_Max):

        return min(round(Value / self.AlphaTrack_SliderMax * Max), Max)

    def UpdateColT(self):

        f = self.FirstTrackT[self.FirstTrack]
        CurID = mixer.getTrackPluginId(mixer.trackNumber(), 0)

        for m in range(0, len(self.ColT)):
            if self.Page == MackieCUPage_Free:
                # free controls
                if m == 8:
                    self.ColT[m].TrackNum = MackieCU_nFreeTracks
                else:
                    self.ColT[m].TrackNum = (f + m) % MackieCU_nFreeTracks

                self.ColT[m].KnobName = 'Knob ' + \
                    str(self.ColT[m].TrackNum + 1)
                self.ColT[m].SliderName = 'Slider ' + \
                    str(self.ColT[m].TrackNum + 1)

                self.ColT[m].BaseEventID = self.FreeEventID + \
                    self.ColT[m].TrackNum * 8  # first virtual CC
            else:
                self.ColT[m].KnobPressEventID = -1

                # mixer
                if m == 8:
                    self.ColT[m].TrackNum = -2
                    self.ColT[m].BaseEventID = midi.REC_MainVol
                    self.ColT[m].SliderEventID = self.ColT[m].BaseEventID
                    self.ColT[m].SliderName = 'Master Vol'
                else:
                    self.ColT[m].TrackNum = midi.TrackNum_Master + \
                        ((f + m) % mixer.trackCount())
                    self.ColT[m].BaseEventID = mixer.getTrackPluginId(
                        self.ColT[m].TrackNum, 0)
                    self.ColT[m].SliderEventID = self.ColT[m].BaseEventID + \
                        midi.REC_Mixer_Vol
                    s = mixer.getTrackName(self.ColT[m].TrackNum)
                    self.ColT[m].SliderName = s + ' - Vol'

                    self.ColT[m].KnobEventID = -1
                    self.ColT[m].KnobResetEventID = -1
                    self.ColT[m].KnobResetValue = midi.FromMIDI_Max >> 1
                    self.ColT[m].KnobName = ''
                    self.ColT[m].KnobMode = 1  # parameter, pan, volume, off
                    self.ColT[m].KnobCenter = -1

                    self.ColT[m].TrackName = ''

                    if self.Page == MackieCUPage_Pan:
                        self.ColT[m].KnobEventID = self.ColT[m].BaseEventID + \
                            midi.REC_Mixer_Pan
                        self.ColT[m].KnobResetEventID = self.ColT[m].KnobEventID
                        self.ColT[m].KnobName = mixer.getTrackName(
                            self.ColT[m].TrackNum) + ' - ' + 'Pan'
                    elif self.Page == MackieCUPage_Stereo:
                        self.ColT[m].KnobEventID = self.ColT[m].BaseEventID + \
                            midi.REC_Mixer_SS
                        self.ColT[m].KnobResetEventID = self.ColT[m].KnobEventID
                        self.ColT[m].KnobName = mixer.getTrackName(
                            self.ColT[m].TrackNum) + ' - ' + 'Sep'
                    elif self.Page == MackieCUPage_Sends:
                        self.ColT[m].KnobEventID = CurID + \
                            midi.REC_Mixer_Send_First + self.ColT[m].TrackNum
                        s = mixer.getEventIDName(self.ColT[m].KnobEventID)
                        self.ColT[m].KnobName = s
                        self.ColT[m].KnobResetValue = round(
                            12800 * midi.FromMIDI_Max / 16000)
                        self.ColT[m].KnobCenter = mixer.getRouteSendActive(
                            mixer.trackNumber(), self.ColT[m].TrackNum)
                        if self.ColT[m].KnobCenter == 0:
                            self.ColT[m].KnobMode = 4
                        else:
                            self.ColT[m].KnobMode = 2
                    elif self.Page == MackieCUPage_FX:
                        if self.CurPluginID == -1:  # Plugin not selected
                            self.ColT[m].CurID = mixer.getTrackPluginId(
                                mixer.trackNumber(), m + self.CurPluginOffset)
                            self.ColT[m].KnobEventID = self.ColT[m].CurID + \
                                midi.REC_Plug_MixLevel
                            s = mixer.getEventIDName(self.ColT[m].KnobEventID)
                            self.ColT[m].KnobName = s
                            self.ColT[m].KnobResetValue = midi.FromMIDI_Max

                            IsValid = mixer.isTrackPluginValid(
                                mixer.trackNumber(), m + self.CurPluginOffset)
                            IsEnabledAuto = mixer.isTrackAutomationEnabled(
                                mixer.trackNumber(), m + self.CurPluginOffset)
                            if IsValid:
                                self.ColT[m].KnobMode = 2
                                # self.ColT[m].KnobPressEventID = self.ColT[m].CurID + midi.REC_Plug_Mute

                                self.ColT[m].TrackName = plugins.getPluginName(
                                    mixer.trackNumber(), m + self.CurPluginOffset)
                            else:
                                self.ColT[m].KnobMode = 4
                            self.ColT[m].KnobCenter = int(
                                IsValid & IsEnabledAuto)
                        else:  # Plugin selected
                            self.ColT[m].CurID = mixer.getTrackPluginId(
                                mixer.trackNumber(), m + self.CurPluginOffset)
                            if m + self.PluginParamOffset < plugins.getParamCount(mixer.trackNumber(), self.CurPluginID + self.CurPluginOffset):
                                self.ColT[m].TrackName = plugins.getParamName(
                                    m + self.PluginParamOffset, mixer.trackNumber(), self.CurPluginID + self.CurPluginOffset)
                            self.ColT[m].KnobMode = 2
                            self.ColT[m].KnobEventID = -1

                    elif self.Page == MackieCUPage_EQ:
                        if m < 3:
                            # gain & freq
                            self.ColT[m].SliderEventID = CurID + \
                                midi.REC_Mixer_EQ_Gain + m
                            self.ColT[m].KnobResetEventID = self.ColT[m].SliderEventID
                            s = mixer.getEventIDName(
                                self.ColT[m].SliderEventID)
                            self.ColT[m].SliderName = s
                            self.ColT[m].KnobEventID = CurID + \
                                midi.REC_Mixer_EQ_Freq + m
                            s = mixer.getEventIDName(self.ColT[m].KnobEventID)
                            self.ColT[m].KnobName = s
                            self.ColT[m].KnobResetValue = midi.FromMIDI_Max >> 1
                            self.ColT[m].KnobCenter = -2
                            self.ColT[m].KnobMode = 0
                        else:
                            if m < 6:
                                # Q
                                self.ColT[m].SliderEventID = CurID + \
                                    midi.REC_Mixer_EQ_Q + m - 3
                                self.ColT[m].KnobResetEventID = self.ColT[m].SliderEventID
                                s = mixer.getEventIDName(
                                    self.ColT[m].SliderEventID)
                                self.ColT[m].SliderName = s
                                self.ColT[m].KnobEventID = self.ColT[m].SliderEventID
                                self.ColT[m].KnobName = self.ColT[m].SliderName
                                self.ColT[m].KnobResetValue = 17500
                                self.ColT[m].KnobCenter = -1
                                self.ColT[m].KnobMode = 2
                            else:
                                self.ColT[m].SliderEventID = -1
                                self.ColT[m].KnobEventID = -1
                                self.ColT[m].KnobMode = 4

                    # self.Flip knob & slider
                    if self.Flip:
                        self.ColT[m].KnobEventID, self.ColT[m].SliderEventID = utils.SwapInt(
                            self.ColT[m].KnobEventID, self.ColT[m].SliderEventID)
                        s = self.ColT[m].SliderName
                        self.ColT[m].SliderName = self.ColT[m].KnobName
                        self.ColT[m].KnobName = s
                        self.ColT[m].KnobMode = 2
                        if not (self.Page in [MackieCUPage_Sends, MackieCUPage_FX, MackieCUPage_EQ]):
                            self.ColT[m].KnobCenter = -1
                            self.ColT[m].KnobResetValue = round(
                                12800 * midi.FromMIDI_Max / 16000)
                            self.ColT[m].KnobResetEventID = self.ColT[m].KnobEventID

            self.ColT[m].LastValueIndex = 48 + m * 6
            self.ColT[m].Peak = 0
            self.ColT[m].ZPeak = False
            self.UpdateCol(m)

    def SetKnobValue(self, Num, Value, Res=midi.EKRes):

        if (self.ColT[Num].KnobEventID >= 0) & (self.ColT[Num].KnobMode < 4):
            if Value == midi.MaxInt:
                if self.Page == MackieCUPage_FX:
                    # if self.ColT[Num].KnobPressEventID >= 0:
                    #	Value = channels.incEventValue(self.ColT[Num].KnobPressEventID, 0, midi.EKRes)
                    #	channels.processRECEvent(self.ColT[Num].KnobPressEventID, Value, midi.REC_Controller)
                    #	s = mixer.getEventIDName(self.ColT[Num].KnobPressEventID)
                    #	self.SendMsg2(s)
                    self.CurPluginID = Num
                    self.PluginParamOffset = 0
                    self.UpdateColT()
                    self.UpdateLEDs()
                    self.UpdateTextDisplay()
                    return
                else:
                    mixer.automateEvent(
                        self.ColT[Num].KnobResetEventID, self.ColT[Num].KnobResetValue, midi.REC_MIDIController, self.SmoothSpeed)
            else:
                mixer.automateEvent(
                    self.ColT[Num].KnobEventID, Value, midi.REC_Controller, self.SmoothSpeed, 1, Res)

            # hint
            n = mixer.getAutoSmoothEventValue(self.ColT[Num].KnobEventID)
            s = mixer.getEventIDValueString(self.ColT[Num].KnobEventID, n)
            if s != '':
                s = ': ' + s
            self.SendMsg2(self.ColT[Num].KnobName + s)

    def SetFirstTrack(self, Value):

        if self.Page == MackieCUPage_Free:
            self.FirstTrackT[self.FirstTrack] = (
                Value + MackieCU_nFreeTracks) % MackieCU_nFreeTracks
            s = utils.Zeros(self.FirstTrackT[self.FirstTrack] + 1, 2, ' ')
        else:
            self.FirstTrackT[self.FirstTrack] = (
                Value + mixer.trackCount()) % mixer.trackCount()
            s = utils.Zeros(self.FirstTrackT[self.FirstTrack], 2, ' ')
        self.UpdateColT()
        self.SendAssignmentMsg(s)
        device.hardwareRefreshMixerTrack(-1)


    def OnIdle(self):

        # refresh meters
        if device.isAssigned():
            f = self.Page == MackieCUPage_Free
            for m in range(0,  len(self.ColT) - 1):
                self.ColT[m].Tag = utils.Limited(self.ColT[m].Peak, 0, self.MeterMax)
                self.ColT[m].Peak = 0
                if self.ColT[m].Tag == 0:
                    if self.ColT[m].ZPeak:
                        continue
                    else:
                        self.ColT[m].ZPeak = True
                else:
                    self.ColT[m].ZPeak = f
                device.midiOutMsg(midi.MIDI_CHANAFTERTOUCH +
                                  (self.ColT[m].Tag << 8) + (m << 12))
        # time display
        if ui.getTimeDispMin():
            # HHH.MM.SS.CC_
            if playlist.getVisTimeBar() == -midi.MaxInt:
                s = '-   0'
            else:
                n = abs(playlist.getVisTimeBar())
                h, m = utils.DivModU(n, 60)
                # todo sign of...
                s = utils.Zeros_Strict(
                    (h * 100 + m) * utils.SignOf(playlist.getVisTimeBar()), 5, ' ')

            s = s + utils.Zeros_Strict(abs(playlist.getVisTimeStep()), 2) + \
                utils.Zeros_Strict(playlist.getVisTimeTick(), 2) + ' '
        else:
            # BBB.BB.__.TTT
            s = utils.Zeros_Strict(playlist.getVisTimeBar(), 3, ' ') + utils.Zeros_Strict(abs(
                playlist.getVisTimeStep()), 2) + '  ' + utils.Zeros_Strict(playlist.getVisTimeTick(), 3)

        self.SendTimeMsg(s)

        # temp message
        if self.TempMsgDirty:
            self.UpdateTempMsg()
            self.TempMsgDirty = False

        if (self.TempMsgCount > 0) & (self.SliderHoldCount <= 0) & (not ui.isInPopupMenu()):
            self.TempMsgCount -= 1
            if self.TempMsgCount == 0:
                self.UpdateTempMsg()

    def UpdateLEDs(self):

        if device.isAssigned():
            # stop
            device.midiOutNewMsg(
                (MackieCUNote_Stop << 8) + midi.TranzPort_OffOnT[transport.isPlaying() == midi.PM_Stopped], 0)
            # loop
            device.midiOutNewMsg(
                (MackieCUNote_Solo << 8) + midi.TranzPort_OffOnT[transport.getLoopMode() == midi.SM_Pat], 1)
            # record
            r = transport.isRecording()
            device.midiOutNewMsg(
                (MackieCUNote_Record << 8) + midi.TranzPort_OffOnT[r], 2)
            # SMPTE/BEATS
            device.midiOutNewMsg(
                (0x71 << 8) + midi.TranzPort_OffOnT[ui.getTimeDispMin()], 3)
            device.midiOutNewMsg(
                (0x72 << 8) + midi.TranzPort_OffOnT[not ui.getTimeDispMin()], 4)
            # self.Page
            for m in range(0,  6):
                device.midiOutNewMsg(
                    ((0x28 + m) << 8) + midi.TranzPort_OffOnT[m == self.Page], 5 + m)
            # changed flag
            device.midiOutNewMsg(
                (MackieCUNote_Save << 8) + midi.TranzPort_OffOnT[general.getChangedFlag() > 0], 11)
            # metronome
            device.midiOutNewMsg(
                (MackieCUNote_Click << 8) + midi.TranzPort_OffOnT[general.getUseMetronome()], 12)
            # rec precount
            # device.midiOutNewMsg((0x58 << 8) + midi.TranzPort_OffOnT[general.getPrecount()], 13)
            # self.Scrub
            device.midiOutNewMsg((MackieCUNote_Scrub << 8) +
                                 midi.TranzPort_OffOnT[self.Scrub], 15)
            # use RUDE SOLO to show if any track is armed for recording
            b = 0
            for m in range(0,  mixer.trackCount()):
                if mixer.isTrackArmed(m):
                    b = 1 + int(r)
                    break

            device.midiOutNewMsg(
                (0x73 << 8) + midi.TranzPort_OffOnBlinkT[b], 16)
            # smoothing
            device.midiOutNewMsg(
                (0x33 << 8) + midi.TranzPort_OffOnT[self.SmoothSpeed > 0], 17)
            # self.Flip
            device.midiOutNewMsg(
                (0x32 << 8) + midi.TranzPort_OffOnT[self.Flip], 18)
            # focused windows
            device.midiOutNewMsg(
                (MackieCUNote_User << 8) + midi.TranzPort_OffOnT[ui.getFocused(midi.widBrowser)], 20)
            device.midiOutNewMsg((MackieCUNote_MidiTracks << 8) +
                                 midi.TranzPort_OffOnT[ui.getFocused(midi.widPlaylist)], 21)
            BusLed = ui.getFocused(midi.widMixer) & (
                self.ColT[0].TrackNum >= 100)
            OutputLed = ui.getFocused(midi.widMixer) & (
                self.ColT[0].TrackNum >= 0) & (self.ColT[0].TrackNum <= 1)
            InputLed = ui.getFocused(midi.widMixer) & (
                not OutputLed) & (not BusLed)
            device.midiOutNewMsg((MackieCUNote_Inputs << 8) +
                                 midi.TranzPort_OffOnT[InputLed], 22)
            device.midiOutNewMsg((MackieCUNote_AudioInst << 8) +
                                 midi.TranzPort_OffOnT[ui.getFocused(midi.widChannelRack)], 23)
            device.midiOutNewMsg((MackieCUNote_Buses << 8) +
                                 midi.TranzPort_OffOnT[BusLed], 24)
            device.midiOutNewMsg(
                (MackieCUNote_Outputs << 8) + midi.TranzPort_OffOnT[OutputLed], 25)

            # device.midiOutNewMsg((MackieCUNote_Write << 8) + midi.TranzPort_OffOnT[ui.getFocused(midi.widChannelRack)], 21)

    def SetJogSource(self, Value):

        self.JogSource = Value

    def OnWaitingForInput(self):

        self.SendTimeMsg('..........')

    def UpdateClicking(self):  # switch self.Clicking for transport buttons

        if device.isAssigned():
            device.midiOutSysex(
                bytes([0xF0, 0x00, 0x00, 0x66, 0x14, 0x0A, int(self.Clicking), 0xF7]))

    # set backlight timeout (0 should switch off immediately, but doesn't really work well)
    def SetBackLight(self, Minutes):

        if device.isAssigned():
            device.midiOutSysex(
                bytes([0xF0, 0x00, 0x00, 0x66, 0x14, 0x0B, Minutes, 0xF7]))


MackieCU = TMackieCU()


def OnInit():
    MackieCU.OnInit()


def OnDeInit():
    MackieCU.OnDeInit()


def OnDirtyMixerTrack(SetTrackNum):
    MackieCU.OnDirtyMixerTrack(SetTrackNum)


def OnRefresh(Flags):
    MackieCU.OnRefresh(Flags)


def OnMidiMsg(event):
    MackieCU.OnMidiMsg(event)


def SendMsg2(Msg, Duration=1000):
    MackieCU.SendMsg2(Msg, Duration)


def OnUpdateBeatIndicator(Value):
    MackieCU.OnUpdateBeatIndicator(Value)


def OnUpdateMeters():
    MackieCU.OnUpdateMeters()


def OnIdle():
    MackieCU.OnIdle()


def OnWaitingForInput():
    MackieCU.OnWaitingForInput()

# Display shortened name to fit to 7 characters (e.g., Fruity Chorus = FChorus, EQ Enhancer = EQEnhan)


def DisplayName(name):
    if name == '':
        return ''

    words = name.split()
    if len(words) == 0:
        return ''

    shortName = ''

    for w in words:
        first = True
        for c in w:
            if c.isupper():
                shortName += c
            elif first:
                shortName += c
            else:
                break
            first = False

    lastWord = words[len(words)-1]
    shortName += lastWord[1:]

    return shortName[0:7]
