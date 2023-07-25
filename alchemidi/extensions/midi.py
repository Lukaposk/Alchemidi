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
from struct import calcsize, pack, unpack_from

from alchemidi.sequence import Event, Track, SeqArgument, SeqEvent

MidiHeader = namedtuple("MidiHeader", ["chunk_type",
                                       "length",
                                       "format",
                                       "num_tracks",
                                       "division"])

MidiTrackHeader = namedtuple("MidiTrackHeader", ["chunk_type",
                                                 "length"])


def load_byte(data:memoryview, parent):
    parent.offset += 1
    return unpack_from(">B", data)[0]


def write_byte(midi_file, val, parent):
    midi_file.write(int(val).to_bytes(1, byteorder='big'))


def load_short(data:memoryview, parent):
    parent.offset += 2
    b1, b2 = unpack_from(">2B", data)
    return (b2 << 7) + b1


def write_short(midi_file, val, parent):
    b2 = int(val) >> 7
    b1 = int(val) & 0x7F
    midi_file.write(((b1 << 8) + b2).to_bytes(2, byteorder='big'))


def load_n_bytes(data:memoryview, parent):
    if not parent.length:
        return None
    parent.offset += parent.length
    return unpack_from(f">{parent.length}s", data)[0]


def write_n_bytes(midi_file, val, parent):
    if not parent.length:
        return
    midi_file.write(val)


def note_on_callback(seq_event:Event, loading):
    if loading:
        seq_event.parent.active_notes.append(seq_event)
    else:
        seq_event.parent.active_notes.append(seq_event)


def note_off_callback(seq_event:Event, loading):
    if loading:
        for note in seq_event.parent.active_notes:
            if note.args[0] == seq_event.args[0]:
                note.args.append(seq_event.position - note.position)
        seq_event.parent.active_notes = list(note for note in seq_event.parent.active_notes if note.args[0] != seq_event.args[0])


def end_all_notes(seq_event:Event, loading):
    if loading:
        for note in seq_event.parent.active_notes:
            note.args.append(seq_event.position - note.position)
        seq_event.parent.active_notes = []

MidiEvents = {
    0x80: SeqEvent("NoteOff", tuple([SeqArgument("Key", load_byte, write_byte, 0, 127),
                                     SeqArgument("Velocity", load_byte, write_byte, 0, 127)]), note_off_callback),
    0x90: SeqEvent("NoteOn", tuple([SeqArgument("Key", load_byte, write_byte, 0, 127),
                                    SeqArgument("Velocity", load_byte, write_byte, 0, 127)]), note_on_callback),
    0xA0: SeqEvent("AfterTouch", tuple([SeqArgument("Key", load_byte, write_byte, 0, 127),
                                        SeqArgument("Velocity", load_byte, write_byte, 0, 127)]), False),
    0xB0: SeqEvent("ControlChange", tuple([SeqArgument("Controller", load_byte, write_byte, 0, 127),
                                           SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xC0: SeqEvent("ProgramChange", tuple([SeqArgument("Program", load_byte, write_byte, 0, 127)]), False),
    0xD0: SeqEvent("ChannelPressure", tuple([SeqArgument("Pressure", load_byte, write_byte, 0, 127)]), False),
    0xE0: SeqEvent("PitchWheelChange", tuple([SeqArgument("Pitch", load_short, write_short, 0, 0x3FFF)]), False),
    0xF0: SeqEvent("SysEx", tuple([SeqArgument("Length", load_byte, write_byte, 0, 127),
                                   SeqArgument("Value", load_n_bytes, write_n_bytes, 0, 127)]), False),
    0xF7: SeqEvent("SysEx7", tuple([SeqArgument("Length", load_byte, write_byte, 0, 127),
                                    SeqArgument("Value", load_n_bytes, write_n_bytes, 0, 127)]), False),
    0xFF: SeqEvent("MetaEvent", tuple([SeqArgument("Type", load_byte, write_byte, 0, 127),
                                       SeqArgument("Length", load_byte, write_byte, 0, 127),
                                       SeqArgument("Value", load_n_bytes, write_n_bytes, 0, 127)]), False),
    0xB000: SeqEvent("Bank Select", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB001: SeqEvent("Modulation wheel", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB002: SeqEvent("Breath control", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB004: SeqEvent("Foot controller", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB005: SeqEvent("PortamentoTime", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB006: SeqEvent("PitchBendRange", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB007: SeqEvent("Volume", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB008: SeqEvent("Balance", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB00A: SeqEvent("Pan", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB00B: SeqEvent("Expression", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB014: SeqEvent("MasterVolume", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB015: SeqEvent("Transpose", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB016: SeqEvent("Priority", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB017: SeqEvent("Tie", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB018: SeqEvent("ModDepth", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB019: SeqEvent("ModSpeed", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB01A: SeqEvent("ModType", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB01B: SeqEvent("ModRange", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    # 0xB020 - 0xB03F is the same as 0xB000 - 0xB01F, but for the LSB
    0xB041: SeqEvent("PortamentoOnOff", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB054: SeqEvent("PortamentoControl", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB055: SeqEvent("Attack", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB056: SeqEvent("Decay", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB057: SeqEvent("Sustain", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB058: SeqEvent("Release", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False),
    0xB07E: SeqEvent("PolyOnOff", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), end_all_notes),
    0xB07F: SeqEvent("PolyOn", tuple([SeqArgument("Value", load_byte, write_byte, 0, 0)]), end_all_notes),
    0xFF2F: SeqEvent("End", tuple([SeqArgument("Length", load_byte, write_byte, 0, 127),
                                   SeqArgument("Value", load_n_bytes, write_n_bytes, 0, 127)]), end_all_notes),
    0xFF51: SeqEvent("Tempo", tuple([SeqArgument("Length", load_byte, write_byte, 0, 127),
                                     SeqArgument("Value", load_n_bytes, write_n_bytes, 0, 127)]), False),
}


def read_variable_length(seq_event, data:memoryview) -> int:
    retVal = unpack_from(">B", data, seq_event.offset)[0] & 0x7F
    while True:
        if (unpack_from(">B", data, seq_event.offset)[0] & 0x80):
            seq_event.offset += 1
            retVal = (retVal << 7) + (unpack_from(">B", data, seq_event.offset)[0] & 0x7F)
        else:
            break
    seq_event.offset += 1
    return retVal


def write_variable_length(length) -> int:
    commandSize = 1
    out = 0
    while True:
        if length > 0x7F:
            out += (length & 0x7F)
            out <<= 8
            out |= 0x80
            length >>= 7
            commandSize += 1
        else:
            break
    out += (length & 0x7F)
    return out, commandSize


def load_event(seq_event, data:memoryview):
    seq_event.delay = read_variable_length(seq_event, data)
    seq_event.position = seq_event.parent.position = seq_event.delay + seq_event.parent.position
    cmd = unpack_from(">B", data, seq_event.offset)[0]
    # If the command byte does not have it's most significant bit set, it's a repeat of the previous command
    if cmd < 0x80:
        cmd = seq_event.parent.last_event
    else:
        if cmd < 0xF0:
            seq_event.parent.id = cmd & 0x0F
            cmd &= 0xF0  # only commands 0xF0 and higher use the low nibble for command types
        seq_event.parent.last_event = cmd
        seq_event.offset += 1
    if cmd in (0xB0, 0xFF):
        cmd = (cmd << 8) + unpack_from(">B", data, seq_event.offset)[0]
        seq_event.offset += 1
    try:
        seq_event.event = MidiEvents[cmd]
    except KeyError:
        if cmd > 0xFF:
            seq_event.event = MidiEvents[cmd >> 8]
            seq_event.offset -= 1
        else:
            seq_event.event = SeqEvent(f"Midi_0x{cmd:04x}", tuple([SeqArgument("Value", load_byte, write_byte, 0, 127)]), False)
    for arg in seq_event.event.arguments:
        seq_event.read_arg(arg, data)
    if seq_event.event.callback:
        seq_event.event.callback(seq_event, True)
    seq_event.parent.offset += seq_event.offset


def save_event(seq_event, file):
    if seq_event.event.name == "NoteOff":  # Skip note off commands. They will be calculated by length
        return
    try:
        cmd = list(MidiEvents.keys())[list(i.name for i in MidiEvents.values()).index(seq_event.event.name)]
    except ValueError:
        pass
    else:
        next_delay = min_delay = seq_event.position - seq_event.parent.position
        while next_delay:
            min_delay = next_delay
            try:
                min_delay = min(note.args[2] for note in seq_event.parent.active_notes)
            except ValueError:
                pass
            if min_delay <= next_delay:
                for note in seq_event.parent.active_notes:
                    note.args[2] -= min_delay
                next_delay -= min_delay
                for note in seq_event.parent.active_notes:
                    if note.args[2] == 0:
                        delay, size = write_variable_length(min_delay)
                        file.write(delay.to_bytes(size, byteorder='little'))
                        min_delay = 0
                        cmd_off = 0x80
                        if seq_event.parent.id:
                            cmd_off += seq_event.parent.id
                        file.write(cmd_off.to_bytes(1, byteorder='big'))
                        seq_event.parent.last_event = cmd_off
                        for i, arg in enumerate(note.event.arguments):
                            note.save_arg(i, arg, file)
                seq_event.parent.active_notes = list(note for note in seq_event.parent.active_notes if note.args[2] > 0)
            else:
                min_delay = next_delay
                for note in seq_event.parent.active_notes:
                    note.args[2] -= min_delay
                break
        delay, size = write_variable_length(min_delay)
        file.write(delay.to_bytes(size, byteorder='little'))
        seq_event.parent.position = seq_event.position
        if cmd >= 0xB000:
            if cmd < 0xF000:
                if seq_event.parent.id:
                    cmd += seq_event.parent.id << 8
            file.write(cmd.to_bytes(2, byteorder='big'))
            cmd >>= 8
        else:
            if cmd < 0xF0 and seq_event.parent.id:
                cmd += seq_event.parent.id
            file.write(cmd.to_bytes(1, byteorder='big'))
        seq_event.parent.last_event = cmd
        for i, arg in enumerate(seq_event.event.arguments):
            seq_event.save_arg(i, arg, file)
        if seq_event.event.callback:
            seq_event.event.callback(seq_event, False)


def load_track(seq_track, data:memoryview):
    seq_track.position = 0
    seq_track.active_notes = []
    seq_track.header = MidiTrackHeader(*unpack_from(">4sL", data))
    data = memoryview(data[calcsize(">4sL"):])
    seq_track.parent.offset += calcsize(">4sL")
    while seq_track.offset < seq_track.header.length:
        seq_track.events.append(Event(seq_track))
        load_event(seq_track.events[-1], memoryview(data[seq_track.offset:]))
    seq_track.parent.offset += seq_track.offset


def save_track(seq_track, file):
    seq_track.position = 0
    seq_track.active_notes = []
    file.write(b'MTrk')
    header_length = file.tell()
    file.write((0).to_bytes(4, byteorder='big')) # temporarily write the size as 0
    for event in seq_track.events:
        save_event(event, file)
    # Update the length of the track
    header_end = file.tell()
    file.seek(header_length)
    file.write((header_end - (header_length + 4)).to_bytes(4, byteorder='big'))
    file.seek(header_end)


def load_seq(seq, data:memoryview):
    seq.header = MidiHeader(*unpack_from(">4sL3H", data))
    seq.offset = calcsize(">4sL3H")
    for track in range(seq.header.num_tracks):
        seq.tracks.append(Track(seq))
        load_track(seq.tracks[-1], memoryview(data[seq.offset:]))


def save_seq(seq, file):
    file.write(pack(">4sL3H", b"MThd", 6, 1, seq.header.num_tracks, 0x30))
    for track in seq.tracks:
        save_track(track, file)
