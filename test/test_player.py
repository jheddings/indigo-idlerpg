import logging
import unittest

import idlerpg

# keep logging output to a minumim for testing
logging.basicConfig(level=logging.FATAL)

################################################################################
class IdleRPGPlayerTest(unittest.TestCase):

    #---------------------------------------------------------------------------
    def test_BasicLoadFromXML(self):
        player = idlerpg.PlayerInfo()

        self.assertTrue(player.load_from_file('test/jarvis_31_online.xml'))
        self.assertEqual(player.username, 'jarvis')

    #---------------------------------------------------------------------------
    def test_LoadBadURL(self):
        player = idlerpg.PlayerInfo()

        self.assertFalse(player.load_from_url(None))
        self.assertFalse(player.load_from_url('http:/www.google.com'))
        self.assertFalse(player.load_from_url('https://httpstat.us/404'))

    #---------------------------------------------------------------------------
    def test_LoadBadPath(self):
        player = idlerpg.PlayerInfo()

        self.assertFalse(player.load_from_file(None))
        self.assertFalse(player.load_from_file('no/such/file.xml'))

    #---------------------------------------------------------------------------
    def test_LoadBadXML(self):
        player = idlerpg.PlayerInfo()

        self.assertFalse(player.load_from_file('test/bad_format.xml'))
        self.assertFalse(player.load_from_file('test/bad_schema.xml'))

    #---------------------------------------------------------------------------
    def test_LoadBadData(self):
        player = idlerpg.PlayerInfo()

        self.assertFalse(player.load_from_string(None))
        self.assertFalse(player.load_from_string(''))

    #---------------------------------------------------------------------------
    def test_BasicPlayerInfo(self):
        player = idlerpg.PlayerInfo()

        self.assertTrue(player.load_from_file('test/jarvis_31_online.xml'))
        self.assertTrue(player.isOnline())
        self.assertEqual(player.level, 31)
        self.assertGreater(player.ttl, 0)

    #---------------------------------------------------------------------------
    def test_OfflinePlayerInfo(self):
        player = idlerpg.PlayerInfo()

        self.assertTrue(player.load_from_file('test/jarvis_31_offline.xml'))
        self.assertFalse(player.isOnline())
        self.assertEqual(player.level, 31)
        self.assertGreater(player.ttl, 0)

    #---------------------------------------------------------------------------
    def test_PlayerPosition(self):
        player = idlerpg.PlayerInfo()

        self.assertTrue(player.load_from_file('test/jarvis_31_online.xml'))
        self.assertEqual(player.pos, (275, 19))

