#!/usr/bin/python
import unittest

from pytracker.modtag import load_module, get_pattern_string
from pytracker.tracker import TrackerSong


class TestSequence(unittest.TestCase):
    def setUp(self):
        self.a = 0

    def load_test_module(self):
        f = open("./testmodules/hyperbased.mod", "rb")
        chunk = f.read()
        f.close()
        return chunk

    def get_test_module(self):
        songbytes = self.load_test_module()
        mod = load_module(songbytes)
        return mod

    def test_song_default(self):
        mod = TrackerSong()

    # self.assertTrue(mod.fmt == TrackerSong.PROTRACKER)

    def test_load_4chan(self):
        songbytes = self.load_test_module()
        print("type: " + str(type(songbytes)))
        mod = load_module(songbytes, {'verbose': True})
        self.assertEqual(mod.name, "hyperbased")

    def test_notedata(self):
        mod = self.get_test_module()
        self.assertEqual(mod.num_patterns, 45)
        s = get_pattern_string(mod, 0)
        print(s)


if __name__ == '__main__':
    unittest.main()
