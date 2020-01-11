#!/usr/bin/env python2.7

import logging
import unittest

import irc

# keep logging output to a minumim for testing
logging.basicConfig(level=logging.FATAL)

################################################################################
class IrcClientTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        irc_nickname = 'testbot'
        irc_fullname = 'Unit Testing'

        self.client = irc.Client(irc_nickname, irc_fullname, daemon=False)
        self.client.connect('localhost', port=6667)

    #---------------------------------------------------------------------------
    def tearDown(self):
        self.client.quit()

    #---------------------------------------------------------------------------
    def test_LocalConnect(self):
        self.assertTrue(self.client.connected)

