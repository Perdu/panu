#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from getpass import getpass
from argparse import ArgumentParser
import configparser
import slixmpp
import sys
import re

CONFIG_FILE = 'panu.conf'

class Config():
    def __init__(self, c):
        self.server = c.get('Connexion', 'server')
        self.jid = c.get('Connexion', 'jid')
        self.room = c.get('Connexion', 'room')
        self.password = c.get('Connexion', 'pass')
        self.room_jid = self.room + '@' + self.server

        self.joke_points_file = c.get('Paths', 'joke_points_file')
        self.dir_defs = c.get('Paths', 'dir_defs')
        self.dir_quotes = c.get('Paths', 'dir_quotes')
        self.file_philosophy = c.get('Paths', 'file_philosophy')
        self.fifopath = c.get('Paths', 'fifopath')
        self.shortener_url = c.get('Paths', 'shortener_url')
        self.shortener_external_url = c.get('Paths', 'shortener_external_url')
        self.quotes_server_port = c.get('Paths', 'quotes_server_port')
        self.quotes_external_url = c.get('Paths', 'quotes_external_url') + self.quotes_server_port
        self.file_features = c.get('Paths', 'file_features')

        self.db_name = c.get('Database', 'db_name')
        self.db_server = c.get('Database', 'db_server')
        self.db_user = c.get('Database', 'db_user')
        self.db_pass = c.get('Database', 'db_pass')
        self.db_port = c.get('Database', 'db_port')

        self.bot_nick = c.get('Other', 'bot_nick')
        self.admin = c.get('Other', 'admin')
        self.last_author = c.get('Other', 'sentence_no_author')
        self.min_number_for_talking = c.get('Other', 'min_number_for_talking')
        self.min_link_size = c.get('Other', 'min_link_size')
        self.max_title_size = c.get('Other', 'max_title_size')
        self.mechanize_timeout = c.get('Other', 'mechanize_timeout')
        self.mechanize_max_size = c.get('Other', 'mechanize_max_size')
        self.min_word_length = c.get('Other', 'min_word_length')
        self.joke_points_max_display = c.get('Other', 'joke_points_max_display')
        self.nb_prev_msg = c.get('Other', 'nb_prev_msg_for_related')

class Command():
    def __init__(self, description, handler):
        self.description = description
        self.handler = handler

class MUCBot(slixmpp.ClientXMPP):
    
    def __init__(self, jid, password, room, nick):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick
        self.prev_msg = ""
        self.prev_author = ""
        self.cmds = {}
        # Probability of talking.
        # Defaults to 0, gains 0.1 every message. Can be decreased when the bot is told
        # to shut up.
        self.p = 0


        self.re_cmd = re.compile('^!(\w+)( +(.*))?')
        #self.re_cmd_args = re.compile('^!\w+ +(.*)')

        self.add_command('quote',
                         '!quote [add] [<nick>] [recherche]: Citation aléatoire.',
                         self.quote)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("message", self.direct_message)   
        self.add_event_handler("muc::%s::got_online" % self.room,
                               self.muc_online)
        self.add_event_handler("muc::%s::got_offline" % self.room,
                               self.muc_offline)

    def start(self, event):
        """
        Process the session_start event.
        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.
        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].join_muc(self.room, self.nick, wait=True)

    def direct_message(self, msg):
        if msg['mucnick'] != self.nick and msg['type'] == 'chat':
            print('Direct message from', msg['mucnick'] + ':', msg['body'])

    def muc_message(self, msg):
        if msg['mucnick'] == self.nick:
            return
        print(msg['mucnick'] + ": " + msg['body'])
        if msg['body'] == self.prev_msg and msg['mucnick'] != self.prev_author:
            self.msg(msg['body'])
        s = self.re_cmd.search(msg['body'])
        if s:
            cmd_name = s.group(1)
            args = s.group(3)
            if cmd_name in self.cmds:
                self.cmds[cmd_name].handler(args)
            else:
                self.msg("Commande inconnue.")
        self.prev_msg = msg['body']
        self.prev_author = msg['mucnick']

    def muc_online(self, presence):
        if presence['muc']['nick'] != self.nick:
            print("Presence:", presence['muc']['nick'], '(' + presence['muc']['role'] + ')')

    def muc_offline(self, presence):
        if presence['muc']['nick'] == self.nick:
            print('Got kicked, reconnecting...')
            self.plugin['xep_0045'].join_muc(self.room, self.nick, wait=True)

    def msg(self, text):
        self.send_message(mto=config.room_jid, mbody=text, mtype='groupchat')
        print(self.nick + ': ' + text)

    def add_command(self, name, description, handler):
        cmd = Command(description, handler)
        self.cmds[name] = cmd

    def quote(self, args):
        self.msg("coucou ! " + str(args))

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-q", "--quiet", help="set logging to ERROR",
                        action="store_const", dest="loglevel",
                        const=logging.ERROR, default=logging.INFO)
    parser.add_argument("-d", "--debug", help="set logging to DEBUG",
                        action="store_const", dest="loglevel",
                        const=logging.DEBUG, default=logging.INFO)
    parser.add_argument("-j", "--jid", dest="jid", help="JID to use")
    parser.add_argument("-p", "--password", dest="password", help="password to use")
    parser.add_argument("-r", "--room", dest="room", help="MUC room to join")
    parser.add_argument("-n", "--nick", dest="nick", help="MUC nickname")
    args = parser.parse_args()

    c = configparser.RawConfigParser()
    if not c.read(CONFIG_FILE):
        print("Could not find config file %s." % CONFIG_FILE)
        print('Please copy it from %s.example and fill it appropiately.' % CONFIG_FILE)
        sys.exit(1)
    config = Config(c)
        
    # Setup logging.
    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)-8s %(message)s')

    # Setup the MUCBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = MUCBot(config.jid, config.password, config.room + '@' + config.server, config.bot_nick)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0045') # Multi-User Chat
    #xmpp.register_plugin('xep_0199') # XMPP Ping

    xmpp.connect()
    xmpp.process()
