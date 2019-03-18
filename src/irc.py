## a very basic socket-level IRC client

# helpful resources:
# https://pythonspot.com/building-an-irc-bot/
# https://stackoverflow.com/questions/2968408/how-do-i-program-a-simple-irc-bot-in-python
# https://stackoverflow.com/a/822788/197772 - socket line buffering
#
# https://github.com/jaraco/irc - full IRC client in Python
# consider using the client or simple bot implementation

import socket
import logging

# XXX should commands like JOIN and PART wait until the server acks before returning?
# would need to worry about error codes, such as 451 if we decide to do this...

# XXX we could provide a "daemon" in this package that helps to process the server
# responses on a separate thread...  that might just overcomplicate things

# XXX should probably protect the receive buffer with a lock in case the caller
# is running multi-threaded (especially communicate() and quit())

# XXX may want to track connection state to help provide meaningful error messages

################################################################################
# the caller must be sure to start listening for server communication soon after
# making the initial connection using either next() or communicate()
class Client:

    sock = None
    logger = None
    nick = None
    name = None

    recvbuf = ''

    #---------------------------------------------------------------------------
    # Client initialization
    #   nick: the nickname used by this client
    #   name: the full name used by this client
    def __init__(self, nick, name):
        self.logger = logging.getLogger('Plugin.idlerpg.IRC.Client')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nick = nick
        self.name = name

    #---------------------------------------------------------------------------
    # iterate over server responses - this iterator will block until data is read
    def __iter__(self): return self

    #---------------------------------------------------------------------------
    # send a message to the connected server followed by a newline
    #   msg: the message to send to the server
    def _send(self, msg):
        self.logger.debug(u'> %s', msg)
        self.sock.sendall("%s\n" % msg)

    #---------------------------------------------------------------------------
    # receive one line of text
    def _recv(self):
        text = None

        # do the newline check first to ensure any new data is processed after receiving

        # XXX this doesn't seem like the most efficient way to read and process
        # new lines...  having to look for a \n twice seems redundant

        # if there are no lines in the buffer, we need more data
        if (not "\n" in self.recvbuf):
            self.logger.debug(u': no lines in buffer; reading data from socket')

            # receive a block of data at a time
            more = self.sock.recv(4096)
            if (more is not None and len(more) > 0):
                self.recvbuf += more

        # if there is a newline in the buffer, we can process the next line
        if ("\n" in self.recvbuf):
            self.logger.debug(u': reading next line from buffer; recvbuf:%d', len(self.recvbuf))

            (text, newbuf) = self.recvbuf.split("\n", 1)
            text = text.strip()
            self.recvbuf = newbuf

            if (len(text) == 0):
                text = None
            else:
                self.logger.debug(u'< %s', text)

        return text

    #---------------------------------------------------------------------------
    # connect this client to the given IRC server
    #   server: the address or hostname of the server
    #   port: the IRC port to connect to (default=6667)
    #   passwd: a password if required to access the server (default=None)
    def connect(self, server, port=6667, passwd=None):
        self.logger.debug(u'connecting to IRC server: %s:%d', server, port)
        self.sock.connect((server, port))

        if (passwd is not None):
            self._send('PASS %s' % passwd)

        self._send('NICK %s' % self.nick)
        self._send('USER %s - - %s' % (self.nick, self.name))

    #---------------------------------------------------------------------------
    # join this client to the given channel
    #   channel: the channel to join
    def join(self, channel):
        self._send('JOIN %s' % channel)

    #---------------------------------------------------------------------------
    # leave the given channel with a parting message
    #   channel: the channel to leave
    #   msg: a parting message
    def part(self, channel, msg):
        self._send('PART %s :%s' % (channel, msg))

    #---------------------------------------------------------------------------
    # send a private message to the intended recipient
    #   recip: the user or channel to receive the message
    #   msg: the text of the message
    def msg(self, recip, msg):
        self._send('PRIVMSG %s :%s' % (recip, msg))

    #---------------------------------------------------------------------------
    # set the mode of the given user or channel
    #   nick: the user nickname or channel name
    #   flags: the flags to set on the target
    def mode(self, nick, flags):
        self._send('MODE %s %s' % (nick, flags))

    #---------------------------------------------------------------------------
    # close the connection to the server and process all remaining server messages
    #   msg: an optional message to provide when quitting (default=None)
    def quit(self, msg=None):
        if (msg is None):
            self._send('QUIT')
        else:
            self._send('QUIT :%s' % msg)

        # read all remaining data from server
        while self.next(): pass

        self.sock.close()
        self.logger.debug(u': connection closed')

    #---------------------------------------------------------------------------
    # this method blocks (handling events) until it sees the welcome message
    def wait_for_welcome(self):
        self.logger.debug(u': waiting for welcome message')
        self.wait_for_reply_code('001')

    #---------------------------------------------------------------------------
    # this method blocks (handling events) until it sees the end of MOTD
    def wait_for_motd(self):
        self.logger.debug(u': waiting for MOTD')
        self.wait_for_reply_code('376', '422')

    #---------------------------------------------------------------------------
    # this method blocks (handling events) until it sees one of the given reply codes
    #   codes: a list of reply codes to consider
    def wait_for_reply_code(self, *codes):
        reply = None

        # TODO handle errors & closed connections

        while (not reply in codes):
            line = self.next()

            if (line is not None and line.startswith(':')):
                reply = line.split(' ', 2)[1]
            else:
                reply = None

        return None

    #---------------------------------------------------------------------------
    # this method is blocking and should usually be called on a separate thread
    # when calling this method, PING will be automatically responded with PONG
    def next(self):
        message = self._recv()

        if (message is None):
            return None

        if (message.startswith(':')):
            self.on_message(message)

        elif (message.startswith('PING')):
            txt = message.split(':', 1)[1]
            self.on_ping(txt)

        elif (message.startswith('ERROR')):
            txt = message.split(':', 1)[1]
            self.on_error(txt)

        else:
            self.logger.warn(u'Unknown message -- %s', message)

        return message

    #---------------------------------------------------------------------------
    # this method is blocking and should usually be called on a separate thread
    # process server messages and generate events as needed until interrupted
    def communicate(self):

        # XXX does it make more sense for this method to deal with all event
        # handlers rather than next()?  just need to make sure that any methods
        # calling next() are okay with that change (especially any methods
        # expecting PING responses or other events to happen - e.g. wait_for_*)

        while (self.next()):
            pass

    #---------------------------------------------------------------------------
    # handle server messages - responses that start with :
    #   msg: the full text of the server message
    def on_message(self, msg):
        pass

    #---------------------------------------------------------------------------
    # handle PING commands
    #   txt: the server challenge text in the PING
    def on_ping(self, txt):
        self._send('PONG :%s' % txt)

    #---------------------------------------------------------------------------
    # handle ERROR commands from the server - NOTE servers send ERROR on QUIT
    #   msg: error message supplied by the server
    def on_error(self, msg):
        self.logger.warn(msg)

