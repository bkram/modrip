from struct import unpack

from lib.modtag.tracker import *


class ModuleFormat():
    """Interface for different module formats."""

    @property
    def name(self):
        raise NotImplementedError("module format must have a name")

    @classmethod
    def identify(cls, bytes):
        """Checks if the given bytes are in this very format"""
        raise NotImplementedError("identify must be implemented")

    @classmethod
    def load_module(cls, bytes, options=None):
        """Returns a TrackerSong from file data"""
        raise NotImplementedError("load_module must be implemented")


class ProtrackerFormat(ModuleFormat):
    name = "Protracker"

    @classmethod
    def check_format(cls, modulebytes):
        amigamagic = str(modulebytes[1080:1084], 'ascii')
        if amigamagic == "M.K.":
            return True

        if amigamagic == "8CHN":
            return True

        if amigamagic == "28CH":
            return True

        return False

    @classmethod
    def identify(cls, bytes):
        return ProtrackerFormat.check_format(bytes)

    @classmethod
    def get_protracker_orderlist(cls, songbytes):
        sample_length = 22 + 2 + 1 + 1 + 2 + 2
        songdata_ofs = 20 + sample_length * 31
        orderlist_length = songbytes[songdata_ofs] + 1

        orderlist = []

        for i in range(0, orderlist_length - 1):
            order = songbytes[songdata_ofs + 2 + i]
            orderlist.append(order)

        return orderlist

    @classmethod
    def pitch_note(cls, pitch):
        pitch2note = {
            # Octave 1
            856: 'C-1', 808: 'C#1', 762: 'D-1', 720: 'D#1', 678: 'E-1',
            640: 'F-1',  604: 'F#1', 570: 'G-1', 538: 'G#1 ', 508: 'A-1',
            480: 'A#1', 453: 'B-1',
            # Octave 2
            428: 'C-2', 404: 'C#2', 381: 'D-2', 360: 'D#2', 339: 'E-2',
            320: 'F-2', 302: 'F#2', 285: 'G-2', 269: 'G#2', 254: 'A-2',
            240: 'A#2', 226: 'B-2',
            # Octave 3
            214: 'C-3', 202: 'C#3', 190: 'D-3', 180: 'D#3', 170: 'E-3',
            160: 'F-3', 151: 'F#3', 143: 'G-3', 135: 'G#3', 127: 'A-3',
            120: 'A#3', 113: 'B-3',
        }
        if pitch in pitch2note:
            return pitch2note[pitch]

    @classmethod
    def parse_note(cls, notebytes):
        note = Note()

        a = notebytes[0]
        b = notebytes[1]
        c = notebytes[2]
        d = notebytes[3]

        note.instrument = (a & 0xf0) + (c >> 4)
        effect = ((c & 0xf) << 8) + d
        note.parameters = effect & 0xff
        note.effect = effect >> 8
        note.pitch = ((a & 0xf) << 8) + b
        if note.pitch != 0:
            note.note = ProtrackerFormat.pitch_note(note.pitch)

        return note

    @classmethod
    def parse_pattern(cls, patternbytes, song):
        pattern = Pattern()
        pattern.length = 64

        for i in range(song.num_channels - 1):
            pattern.rows.append([])

        for r in range(0, 63):
            for c in range(song.num_channels - 1):
                ofs = r * song.num_channels * 4 + c * 4
                # pattern.rows[c][i] = cls.parse_note(patternbytes[ofs:ofs+4])
                pattern.rows[c].append(
                    cls.parse_note(patternbytes[ofs:ofs + 4]))

        return pattern

    # TODO add proper channel checks here
    @classmethod
    def get_num_channels(cls, songbytes):
        return 4

    @classmethod
    def load_module(cls, songbytes, options=None):
        # modformat = ProtrackerFormat.detect_module_format(songbytes)

        if not options:
            options = {'verbose': False}

        # if modformat != TrackerSong.PROTRACKER:
        #		return None

        song = TrackerSong()
        # song.fmt = modformat
        # song.name = str(unpack('20s', songbytes[0:20]), 'ascii')
        song.num_channels = cls.get_num_channels(songbytes)
        song.name = str(songbytes[0:20], 'ascii').rstrip('\0')
        sample_length = 22 + 2 + 1 + 1 + 2 + 2

        for i in range(0, 30):
            ofs = (20 + i * sample_length)
            samplechunk = songbytes[ofs:ofs + sample_length]
            fields = unpack('>22sHBBHH', samplechunk)
            sample = Sample()
            sample.name = str(fields[0], 'ascii').rstrip('\0')
            sample.length = fields[1] * 2
            sample.finetune = fields[2]
            sample.volume = fields[3]
            sample.repeat = fields[4] * 2
            sample.repeat_length = fields[5] * 2

            song.instruments.append(Instrument(sample))

            if options['verbose']:
                if (len(sample.name) > 0 or sample.length > 0):
                    print(str(i), " : ", sample.name)
                    print("\tlength: ", str(sample.length))
                    print("\tvolume: ", str(sample.volume))

        songdata_ofs = 20 + sample_length * 31
        song.orderlist = cls.get_protracker_orderlist(songbytes)

        song.num_patterns = max(song.orderlist) + 1
        patterndata_ofs = songdata_ofs + 128 + 4 + 2
        pattern_size = song.num_channels * 64 * 4
        sampledata_ofs = patterndata_ofs + song.num_patterns * pattern_size

        for i in range(0, song.num_patterns - 1):
            ofs = patterndata_ofs + i * pattern_size
            pattern = cls.parse_pattern(
                songbytes[ofs:ofs + pattern_size], song)
            song.patterns.append(pattern)

        # load sample data
        sample_ofs = sampledata_ofs
        for i in range(0, 30):
            s = song.instruments[i].sample

            if s.length == 0:
                continue

            s.data = songbytes[sample_ofs:sample_ofs + s.length]
            sample_ofs += s.length

        if options['verbose']:
            print("orderlist: " + str(song.orderlist))
            print("amount of patterns: " + str(song.num_patterns))

        return song
