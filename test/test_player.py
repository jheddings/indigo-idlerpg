#!/usr/bin/env python2.7

import logging
import unittest

import idlerpg

# keep logging output to a minumim for testing
logging.basicConfig(level=logging.DEBUG)

################################################################################
class IdleRPGPlayerTest(unittest.TestCase):

    #---------------------------------------------------------------------------
    def test_BasicLoadFromXML(self):
        player = idlerpg.Player()

        self.assertTrue(player.load_from_file("test/jarvis_online.xml"))
        self.assertEqual(player.username, 'jarvis')

    #---------------------------------------------------------------------------
    def test_LoadBadFormatXML(self):
        player = idlerpg.Player()

        self.assertFalse(player.load_from_file("test/bad_xml_player.xml"))

    #---------------------------------------------------------------------------
    def test_CheckOnlineOffline(self):
        player = idlerpg.Player()

        player.load_from_file("test/jarvis_online.xml")
        self.assertTrue(player.isOnline())

        player.load_from_file("test/jarvis_offline.xml")
        self.assertFalse(player.isOnline())

