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

from alchemidi.sequence import Sequence
from alchemidi.extensions.midi import load_seq, save_seq


def main():
    seq = Sequence()  # Create a sequence object to load the data into
    with open("test.mid", "rb") as midi_file:
        midi_data = memoryview(midi_file.read())
    load_seq(seq, midi_data)  # load the midi file to the sequence object
    with open("test_out.mid", "w+b") as out_file:
        save_seq(seq, out_file)  # Re-save the sequence object to a new midi file


if __name__ == "__main__":
    main()
