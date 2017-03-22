#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from getpass import getpass
from argparse import ArgumentParser
import configparser
import slixmpp
import sys
import re
import random
import base64

import urllib3
import lxml.html

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from  sqlalchemy.sql.expression import func

# Dependencies:
# python3-sqlalchemy
# python3-mysqldb
# python3-urllib3

CONFIG_FILE = 'panu.conf'
Base = declarative_base()
db = None
http = urllib3.PoolManager()

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
        self.min_number_for_talking = c.getint('Other', 'min_number_for_talking')
        self.min_link_size = c.getint('Other', 'min_link_size')
        self.max_title_size = c.getint('Other', 'max_title_size')
        self.url_shortener_timeout = c.getfloat('Other', 'url_shortener_timeout')
        self.url_shortener_max_size = c.getint('Other', 'url_shortener_max_size')
        self.min_word_length = c.getint('Other', 'min_word_length')
        self.joke_points_max_display = c.getint('Other', 'joke_points_max_display')
        self.nb_prev_msg = c.getint('Other', 'nb_prev_msg_for_related')

class Command():
    def __init__(self, description, handler):
        self.description = description
        self.handler = handler

class Quote(Base):
    __tablename__ = "quotes"
    quote_id = Column(Integer, primary_key=True)
    author = Column(String(100))
    details = Column(String(1000))
    quote = Column(String(10000))

    def __init__(self, author, details, quote=None):
        self.author = author
        self.details = details
        self.quote = quote

class Definition(Base):
    __tablename__ = "definitions"
    def_id = Column(Integer, primary_key=True)
    name = Column(String(100))
    definition = Column(String(10000))

class JokePoints(Base):
    __tablename__ = "jokepoints"
    jokepoints_id = Column(Integer, primary_key=True)
    joker = Column(String(100))
    laugher = Column(String(100))
    nb_points = Column(Integer)
    date = Column(DateTime)

class MUCBot(slixmpp.ClientXMPP):
    
    def __init__(self, jid, password, room, nick):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.userlist = set()
        self.room = room
        self.nick = nick
        self.prev_msg = ""
        self.prev_author = ""
        self.prev_quote = Quote(None, None)
        self.prev_related_quote_word = ""
        self.cmds = {}
        self.quiet = False
        self.prev_msgs = []
        self.cyber_proba = 0
        self.supplementary_doc = []
        # Probability of talking.
        # Defaults to 0, gains 0.1 every message. Can be decreased when the bot is told
        # to shut up.
        self.p = 0
        self.prev_joker = None

        self.re_cmd = re.compile('^!(\w+)( +(.*))?')
        self.re_ans = re.compile('^' + self.nick + '\s*[:,]')
        self.re_quote_add = re.compile('add\s+([^\s]+)\s+([^|]+)(\s*\|\s*(.*))?$')
        self.re_link = re.compile('(http(s)?:\/\/[^ ]+)')
        self.re_def = re.compile('^!!\s*([-_\w\'’ ]+?)\s*=\s*(.*)\s*$')
        self.re_show_def = re.compile('\?\?\s*([-_\w\'’ ]+?)\s*$')
        self.re_get_words = re.compile('(\w{' + str(config.min_word_length) + ',})(?:[ ,\.\-\']|$)')
        self.re_jokepoints = re.compile('^[:xX]([Dd]+)')

        self.add_command('battle',
                         '!battle : sélectionne un choix au hasard',
                         self.cmd_battle)
        self.add_command('cyber',
                         '!cyber [<proba>] : Active le cyber-mode cyber.',
                         self.cmd_cyber)
        self.add_command('quote',
                         '!quote [add] [<nick>] [recherche] : Citation aléatoire.',
                         self.cmd_quote)
        self.add_command('quiet',
                         '!quiet : Rendre le bot silencieux.',
                         self.cmd_quiet)
        self.add_command('help',
                         '!help : affiche les commandes disponibles',
                         self.cmd_help)
        self.add_command('isit',
                         '!isit <nick> : Deviner de qui est la citation précédente.',
                         self.cmd_isit)
        self.add_command('related',
                         '!related : Donne une citation en rapport.',
                         self.cmd_related)
        self.add_command('speak',
                         '!speak [less|more|<nombre>] : diminue/augmente la fréquence des citations aléatoires.',
                         self.cmd_speak)
        self.add_command('who',
                         '!who : Indique de qui est la citation précédente.',
                         self.cmd_who)
        self.add_command('why',
                         '!why : Indique ce qui a provoqué la citation précédente.',
                         self.cmd_why)
        self.supplementary_doc.append('!! <nom> = <def> : ajouter une définition')
        self.supplementary_doc.append('?? <nom> : lire une définition')
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

    def test_regexps(self, msg):
        res_re_jokepoints = self.re_jokepoints.match(msg['body'])
        if res_re_jokepoints:
            self.add_jokepoints(self.prev_joker, msg['mucnick'], len(res_re_jokepoints.group(1)))
            return True
        res_re_cmd = self.re_cmd.search(msg['body'])
        if res_re_cmd:
            cmd_name = res_re_cmd.group(1)
            args = res_re_cmd.group(3)
            if cmd_name in self.cmds:
                self.cmds[cmd_name].handler(args, msg)
            else:
                self.msg("Commande inconnue.")
            return True
        res_re_ans = self.re_ans.match(msg['body'])
        if res_re_ans:
            self.answer(msg)
            self.prev_joker = self.nick
            return True
        res_re_def = self.re_def.match(msg['body'])
        if res_re_def:
            self.add_def(res_re_def.group(1), res_re_def.group(2))
            return True
        res_re_show_def = self.re_show_def.match(msg['body'])
        if res_re_show_def:
            self.show_def(res_re_show_def.group(1))
            return True
        self.prev_joker = msg['mucnick']
        res_re_link = self.re_link.search(msg['body'])
        if res_re_link:
            self.shortener(res_re_link.group(1))
            return True
        return False

    def update_prev_msgs_list(self, msg, prev_msgs):
        prev_msgs.append(msg)
        if len(prev_msgs) > config.nb_prev_msg:
            prev_msgs.pop(0)
        return prev_msgs

    def search_and_answer_related_quote(self, msg):
        related_quote, word = self.find_related_quote(self.prev_msgs)
        if related_quote != None:
            self.msg(self.convert_quote(related_quote.quote, msg['mucnick']))
            self.prev_quote.author = related_quote.author
            self.prev_related_quote_word = word
            self.prev_joker = related_quote.author
            return True
        return False

    def random_quote(self, msg, answer=False):
        random_quote = db.query(Quote).order_by(func.rand()).limit(1).all()
        if len(random_quote) > 0:
            quote = self.convert_quote(random_quote[0].quote, msg['mucnick'])
            self.msg(quote)
            self.prev_quote.author = random_quote[0].author
            self.prev_quote.details = random_quote[0].details
            self.prev_related_quote_word = ""
            self.prev_joker = random_quote[0].author
        elif answer:
            self.msg('Aucune citation connue. Ajoutez-en avec !quote add')

    def message_reaction(self, msg):
        if msg['body'] == self.prev_msg and msg['mucnick'] != self.prev_author:
            self.msg(msg['body'])
            return
        if self.test_regexps(msg):
            return
        self.p += 1
        if random.randint(0, config.min_number_for_talking) < self.p:
            if not self.search_and_answer_related_quote(msg):
                self.random_quote(msg, answer=False)

    def muc_message(self, msg):
        if msg['mucnick'] == self.nick:
            return
        print('<' + msg['mucnick'] + "> | " + msg['body'])
        self.prev_msgs = self.update_prev_msgs_list(msg['body'], self.prev_msgs)
        self.message_reaction(msg)
        self.prev_msg = msg['body']
        self.prev_author = msg['mucnick']

    def muc_online(self, presence):
        if presence['muc']['nick'] != self.nick:
            print("Presence:", presence['muc']['nick'], '(' + presence['muc']['role'] + ')')
            self.userlist.add(presence['muc']['nick'])

    def muc_offline(self, presence):
        if presence['muc']['nick'] == self.nick:
            print('Got kicked, reconnecting...')
            self.plugin['xep_0045'].join_muc(self.room, self.nick, wait=True)
        else:
            self.userlist.remove(presence['muc']['nick'])

    def msg(self, text):
        if not self.quiet:
            if self.cyber_proba > 0:
                text = self.cyberize(text, self.cyber_proba)
            self.send_message(mto=config.room_jid, mbody=text, mtype='groupchat')
            print(self.nick + ': ' + text)

    def add_command(self, name, description, handler):
        cmd = Command(description, handler)
        self.cmds[name] = cmd

    def shortener(self, link):
        r = http.request('GET', link, timeout=config.url_shortener_timeout)
        if r.status != 200:
            self.msg(str(r.status))
            return
        t = lxml.html.fromstring(r.data)
        title_search = t.find(".//title")
        if title_search is not None:
            title = title_search.text
        else:
            title = ""
        r = http.request('GET', config.shortener_url + '?url=' + base64.urlsafe_b64encode(link.encode('utf8')).decode('ascii'))
        if r.status != 200:
            self.msg(str(r.status))
        else:
            self.msg(config.shortener_external_url + r.data.decode('ascii') + ' ' + title)

    def convert_quote(self, quote, nick):
        return quote.replace("%%", nick)

    def answer(self, msg):
        quote = db.query(Quote).filter_by(author='answer').order_by(func.rand()).limit(1).all()
        if len(quote) > 0:
            self.msg(self.convert_quote(quote[0].quote, (msg['mucnick'])))

    def cmd_quote(self, args, msg):
        if args is not None and len(args) > 0:
            a = args.split()
            if a[0] == 'list':
                rs = db.query(Quote.author, func.count(Quote.author)).group_by(Quote.author)
                m = ""
                rs = sorted(rs, key=lambda r: r[1], reverse=True)
                for r in rs:
                    nick = r[0]
                    # add '_' in the nick to prevent HL
                    if nick in self.userlist and len(nick) > 1:
                        nick = nick[0] + '_' + nick[1:]
                    m += nick + ' (' + str(r[1]) + ') '
                m.rstrip(' ')
                self.msg(m)
            elif a[0] == 'add':
                re = self.re_quote_add.search(args)
                if re:
                    author = re.group(1)
                    quote = re.group(2)
                    details = re.group(4)
                    if db.query(db.query(Quote).filter(Quote.author==author, Quote.quote==quote).exists()).scalar():
                        self.msg("Citation déjà connue.")
                    else:
                        q = Quote(author=author, quote=quote, details=details)
                        db.add(q)
                        db.commit()
                        self.msg("Citation ajoutée pour %s : %s" % (author, quote))
                else:
                    self.msg("Commande incorrecte.")
            else:
                # quote <author>
                random_quote = db.query(Quote).filter_by(author=a[0]).order_by(func.rand()).limit(1).all()
                nb_quotes_by_author = db.query(Quote).filter_by(author=a[0]).count()
                if len(random_quote) > 0:
                    quote = self.convert_quote(random_quote[0].quote, msg['mucnick'])
                    self.msg(quote + ' (?/' + str(nb_quotes_by_author) + ')')
                    self.prev_quote.author = random_quote[0].author
                    self.prev_quote.details = random_quote[0].details
                else:
                    self.msg('Aucune citation trouvée pour %s.' % a[0])
        else:
            self.random_quote(msg, answer=True)

    def cmd_quiet(self, args, msg):
        if not self.quiet:
            self.msg("Becoming quiet.")
        self.quiet = not self.quiet
        if not self.quiet:
            self.msg("Stop being quiet.")

    def cmd_help(self, args, msg):
        help_message = ""
        for cmd in self.cmds:
            help_message += self.cmds[cmd].description + "\n"
        for doc in self.supplementary_doc:
            help_message += doc + "\n"
        self.msg(help_message.rstrip())

    def cmd_battle(self, args, msg):
        choices = args.split()
        choice = random.choice(choices)
        r = random.randint(1, 20)
        # sometimes change answer
        if (r == 1):
            self.msg(msg['mucnick'] + ': ' + "demain.")
        elif (r == 2 and len(choices) == 2):
            self.msg(msg['mucnick'] + ': ' + "les deux")
        else:
            self.msg(msg['mucnick'] + ': ' + choice)

    def cmd_cyber(self, args, msg):
        if args is None:
            self.msg('Syntaxe : cyber <probabilité>')
        self.cyber_proba = float(args)
        if self.cyber_proba == 0:
            self.msg('Mode cyber désactivé.')
        else:
            self.msg('Mode cyber: probabilité définie à %s' % self.cyber_proba)

    def cmd_who(self, args, msg):
        ans = self.prev_quote.author
        if ans is not None:
            if self.prev_quote.details is not None:
                ans += ' (' + self.prev_quote.details + ')'
            self.msg(ans)

    def cmd_why(self, args, msg):
        if self.prev_related_quote_word != "":
            self.msg(self.prev_related_quote_word)
        else:
            self.msg("Unrelated.")

    def cmd_isit(self, args, msg):
        if self.prev_quote.author in ["answer", "random"]:
            self.msg("Ne cherche pas, je n'en sais rien !")
        else:
            if args == self.prev_quote.author:
                self.msg("Oui !")
            else:
                self.msg("Non !")

    def cmd_related(self, args, msg):
        if not self.search_and_answer_related_quote(msg):
            self.msg("Aucune citation trouvée.")

    def cmd_speak(self, args, msg):
        ok = True
        if args is not None:
            if args == 'less':
                config.min_number_for_talking = int(1.2 * config.min_number_for_talking)
            elif args == 'more':
                config.min_number_for_talking = int(0.8 * config.min_number_for_talking)
            else:
                try:
                    config.min_number_for_talking = int(args)
                except ValueError:
                    self.msg('Syntaxe : !speak [less|more|<nombre>]')
                    ok = False
        if ok:
            self.msg('Cap fixé à %s.' % config.min_number_for_talking)

    def add_def(self, name, definition):
        prev_def = None
        q_prev_def = db.query(Definition).filter(Definition.name==name).all()
        if len(q_prev_def) > 0:
            prev_def = q_prev_def[0].definition
        d = Definition(name=name, definition=definition)
        db.add(d)
        db.commit()
        if prev_def is not None:
            self.msg("Définition ajoutée pour %s : %s\nDéfinition précédente : %s" %
                     (name, definition, prev_def))
        else:
            self.msg("Définition ajoutée pour %s : %s" %w (name, definition))

    def show_def(self, name):
        q_def = db.query(Definition).filter(Definition.name==name).all()
        if len(q_def) > 0:
            self.msg('%s : %s ' % (name, q_def[0].definition))
        else:
            self.msg('%s : Non défini' % name)

    def find_related_quote(self, msgs):
        for msg in msgs:
            words = self.get_words(msg)
            random.shuffle(words)
            for word in words:
                quote = db.query(Quote).filter(Quote.quote.like('%' + word + '%')).filter(Quote.quote!=msg).order_by(func.rand()).limit(1).all()
                if len(quote) > 0:
                    return quote[0], word
        return None, None

    def get_words(self, msg):
        words = self.re_get_words.findall(msg)
        if words is not None:
            return words
        else:
            return []

    def cyberize(self, text, cyber_proba):
        res = ""
        pres_pos = 0
        for m in self.re_get_words.finditer(text):
            if random.random() <= cyber_proba:
                res += text[pres_pos:m.start()] + 'cyber'
                pres_pos = m.start()
        res += text[pres_pos:]
        return res

    def add_jokepoints(self, joker, laugher, nb_points):
        if joker == None or joker == laugher:
            # todo: also test aliases here
            return
        j = JokePoints(joker=joker, laugher=laugher, nb_points=nb_points) # + date
        db.add(j)
        db.commit()
        print("+%s points blague pour %s de %s" % (nb_points, joker, laugher))

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

    eng = create_engine('mysql+mysqldb://' + config.db_user + ':' +
                        config.db_pass + '@' + config.db_server +
                        '/' + config.db_name, pool_recycle=3600)
    Base.metadata.bind = eng
    #Base.metadata.create_all()
    Session = sessionmaker(bind=eng)
    db = Session()
    Base.metadata.create_all(bind=eng)

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
