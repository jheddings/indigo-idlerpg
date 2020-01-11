#!/usr/bin/env python2.7

import logging
import unittest

import irc

# keep logging output to a minumim for testing
logging.basicConfig(level=logging.FATAL)

################################################################################
class ClientTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def test_Connect(self):
        self.client = irc.Client('testbot', 'Unit Testing')
        self.client.connect('irc.freenode.net', 6667)

