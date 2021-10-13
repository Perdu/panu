# panu

A Jabber (XMPP) bot. You can tell him quotes and it will reuse them in the appropriate context. It can compute how funny people in the room are according to other people's smileys, shorten URL and display the page's title... How cool is that?

Coded in English, talks in French.

Status: actively used and maintained (2020).

## Commands

Commandes disponibles :
```
!backup : génère une backup de la base de données.
!battle : sélectionne un choix au hasard.
!cancel : Annule l'ajout d'une citation.
!cyber [<proba>] : Active le cyber-mode cyber.
!delete : Supprime la dernière citation.
!feature add|list|del : ajouter une demande de feature ou lister toutes les demandes.
!help : affiche les commandes disponibles
!isit <nick> : Deviner de qui est la citation précédente.
!pb [nick|date] : affiche les points-blague.
!quiet : Rendre le bot silencieux.
!quote [add] [<nick>]|search <recherche> : Citation aléatoire.
!quotes [sum [<nick>]|list] : Donne toutes les citations d'un auteur.
!related : Donne une citation en rapport.
!speak [less|more|<nombre>] : diminue/augmente la fréquence des citations aléatoires.
!truth : révèle une vérité absolue sur le monde.
!who : Indique de qui est la citation précédente.
!why : Indique ce qui a provoqué la citation précédente.
!! <nom> = <def> : ajouter une définition.
?? <nom> : lire une définition.
```

## Dependencies

- slixmpp : python-slixmpp-git from AUR (archlinux)
- mysql/mariadb
- python-sqlalchemy
- python-mysqldb (debian) / python-mysqlclient from AUR (archlinux)
- python-urllib3
- python-lxml
- python-certifi
- a web server for the URL shortener

## Install

### Basic configuration

- copy `panu.conf.example` to `panu.conf`
- Create an XMPP account an indicate the JID and password in `panu.conf`
- Indicate room and server to be joined in `panu.conf`

#### Easy install (Docker)

First, copy `env.example` to `.end` and edit it with your configuration. Then, run:
```bash
./setup_docker.sh
sudo docker-compose -f docker-compose.yml up --build
```

#### Manual install

##### Database

- create a mariadb database, a user and give access rights for the database to the user
- enter related configuration in the Database section of panu.conf

##### URL shortener (optional)

Place `shortener/index.php` on a web server you own. Optionally, you can use mine (default config)
