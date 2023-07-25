"""
This file is part of Alchemidi.
Copyright (C) 2023 Alec LaFleur

Alchemidi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from collections import namedtuple


SeqEvent = namedtuple("SeqEvent", ["name",  # Name of the event
                                   "arguments",  # Tuple of arguments for the event
                                   "callback"  # Optional method to call after loading the arguments
                                   ])

SeqArgument = namedtuple("SeqArgument", ["name",  # Name of the argument
                                         "loader",  # Method to load the argument
                                         "writer",  # Method to write the argument
                                         "min",  # Minimum the raw value can be (for scaling)
                                         "max"  # Maximum the raw value can be (for scaling)
                                         ])

SeqEventScale = {
    "NoteOff": {"Key": False,
                "Velocity": True,
                "Length": False},
    "NoteOn": {"Key": False,
               "Velocity": True,
               "Length": False},
    "AfterTouch": {"Key": False,
                   "Velocity": True},
    "ControlChange": {"Controller": False,
                      "Value": True},
    "ProgramChange": {"Program": False},
    "ChannelPressure": {"Pressure": True},
    "PitchWheelChange": {"Pitch": True},
    "SysEx": {"Length": False,
              "Value": False},
    "SysEx7": {"Length": False,
               "Value": False},
    "MetaEvent": {"Type": False,
                  "Length": False,
                  "Value": False},
    "Bank Select": {"Value": True},
    "Modulation wheel": {"Value": True},
    "Breath control": {"Value": True},
    "Foot controller": {"Value": True},
    "PortamentoTime": {"Value": True},
    "PitchBendRange": {"Value": True},
    "Volume": {"Value": True},
    "Balance": {"Value": True},
    "Pan": {"Value": True},
    "Expression": {"Value": True},
    "MasterVolume": {"Value": True},
    "Transpose": {"Value": True},
    "Priority": {"Value": True},
    "Tie": {"Value": True},
    "ModDepth": {"Value": True},
    "ModSpeed": {"Value": True},
    "ModType": {"Value": True},
    "ModRange": {"Value": True},
    "PortamentoOnOff": {"Value": True},
    "PortamentoControl": {"Value": True},
    "Attack": {"Value": True},
    "Decay": {"Value": True},
    "Sustain": {"Value": True},
    "Release": {"Value": True},
    "PolyOnOff": {"Value": False},
    "PolyOn": {"Value": True},
}

class Sequence:
    def __init__(self) -> None:
        self.header = None
        self.tracks = []
        self.offset = 0


class Track:
    def __init__(self, parent:Sequence) -> None:
        self.parent = parent
        self.header = None
        self.events = []
        self.last_event = None
        self.offset = 0
        self.position = 0
        self.id = None


class Event:
    def __init__(self, parent:Track) -> None:
        self.parent = parent
        self.delay = 0
        self.position = None
        self.event = None
        self.args = []
        self.length = 0
        self.offset = 0
    
    def read_arg(self, arg, data:memoryview):
        val = arg.loader(memoryview(data[self.offset:]), self)
        if val is not None:
            self.args.append(val)
            if arg.name == "Length":
                self.length = val
            try:
                if SeqEventScale[self.event.name][arg.name]:
                    if arg.max == arg.min:
                        self.args[-1] = arg.max
                    else:
                        self.args[-1] = (val - arg.min) / (arg.max - arg.min)
            except KeyError:
                pass

    def save_arg(self, i, arg, file):
        try:
            argval = self.args[i]
        except IndexError:
            pass
        else:
            if arg.name == "Length":
                self.length = argval
            try:
                if SeqEventScale[self.event.name][arg.name]:
                    if arg.max == arg.min:
                        argval = arg.max
                    else:
                        argval = (argval * (arg.max - arg.min)) + arg.min
            except KeyError:
                pass
            arg.writer(file, argval, self)

