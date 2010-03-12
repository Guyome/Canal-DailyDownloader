#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#**************************************************************************#
#*     Copyright (C) 2009 by Renaud Guezennec                            #
#*   http://renaudguezennec.homelinux.org/accueil,3.html                   #
#*                                                                         #
#*   Canal+ Daily Downloader is free software;                             #
#*   you can redistribute it and/or modify                                 #
#*   it under the terms of the GNU General Public License as published by  #
#*   the Free Software Foundation; either version 2 of the License, or     #
#*   (at your option) any later version.                                   #
#*                                                                         #
#*   This program is distributed in the hope that it will be useful,       #
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#*   GNU General Public License for more details.                          #
#*                                                                         #
#*   You should have received a copy of the GNU General Public License     #
#*   along with this program; if not, write to the                         #
#*   Free Software Foundation, Inc.,                                       #
#*   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
#**************************************************************************#

from getopt import getopt, GetoptError
from sys import exit, argv
from xml.dom import minidom
from urllib import urlopen
from os import remove, makedirs
from os.path import join, expanduser, exists
from subprocess import Popen

#global variables
debug = True
verbose = False

dest_directory = join(expanduser("~"), join('Vidéos','Canal_Download'))
available_show = {"A": "discrete",
                  "B": "boite", 
                  "C": "planquee", 
                  "G": "guignols", 
                  "J": "petit", 
                  "L": "petite", 
                  "M": "meteo", 
                  "P": "pepites", 
                  "R": "groland", 
                  "S": "sav", 
                  "T": "tele", 
                  "U": "salut", 
                  "Z": "zapping"}
nb_videos_show = {"discrete": 1,
                  "boite": 1, 
                  "planquee": 1, 
                  "guignols": 1, 
                  "petit": 3,
                  "petite": 1, 
                  "meteo": 1, 
                  "pepites": 1, 
                  "groland": 1, 
                  "sav": 1, 
                  "tele": 1, 
                  "salut": 4, 
                  "zapping": 1}
available_quality = {'high': 'HAUT_DEBIT', 'low': 'BAS_DEBIT', 'hd': 'HD'}
url_canal = "http://www.canalplus.fr/rest/bootstrap.php?/bigplayer/search/"
URLdico = {}

def print_dbg(msg):
    if debug:
        print "DBG: " + str(msg)

def print_verbose(msg):
    if verbose:
        print str(msg)

def print_err(msg):
    print >> sys.stderr, str(msg)

def buildURLdico(currentTvShow, nb_video, quality):
    #Get Dom file
    url= url_canal + currentTvShow
    try:
        dom = minidom.parse(urlopen(url))
    except IOError:
        print_err("Unable to reach Canal+'s web site\nCheck your network")
        exit(2)
    #Get the number of videos
    video_tags = dom.getElementsByTagName('VIDEO')
    if nb_video == 0:
        #on va chercher toutes les videos disponibles
        nb_video = len(video_tags)
    else:
        #on va chercher le nombre de videos choisi "nb_video"
        nb_video = nb_videos_show[currentTvShow] *\
        min(len(video_tags), max(nb_video, 1))

    print_verbose("The following URLs have been found:")
    for node in video_tags[:nb_video]:
        #Read date, debit and rubrique for all video tag
        datenodelist = node.getElementsByTagName('DATE')
        hournodelist = node.getElementsByTagName('HEURE')
        debitnodelist = node.getElementsByTagName(available_quality[quality])
        #For the HD case
        if debitnodelist[0].firstChild is None:
            print "There is no HD video, download the high quality instead"
            debitnodelist = node.getElementsByTagName('HAUT_DEBIT')
        rubriquenodelist = node.getElementsByTagName('RUBRIQUE')
        video_rubrique= str(rubriquenodelist[0].firstChild.nodeValue).replace(' ','_')

        if datenodelist.length == debitnodelist.length and \
        video_rubrique.lower().find(currentTvShow.lower())>-1:
            for datevideo in datenodelist:
                #Read video url and date
                video_url=str(debitnodelist[0].firstChild.nodeValue)
                video_date = makeDateISO(str(datevideo.firstChild.nodeValue))
                video_hour = str(hournodelist[0].firstChild.nodeValue)
                video_date = video_date+"_"+video_hour
                if video_url.find("rtmp")>-1:
                    URLdico[video_url]=(video_date, video_rubrique)
                    print_verbose(" + " + video_url)

def makeDateISO(madate):
    b=madate.split("/")
    madateISO=[]
    madateISO.append(b[2])
    madateISO.append(b[1])
    madateISO.append(b[0])
    return '_'.join(madateISO)


def downloadURL(url, verbose, overwrite, force, rename):
    item = URLdico[url]# consultaion URLdico
    video_date, video_rubrique = item[0], item[1]
    if not exists(join(dest_directory,video_rubrique)):
        if force:
            try:
                makedirs(join(dest_directory,video_rubrique), mode=0755)
            except OSError:
                print_err("Unable to create directories in this\
                location:"+dest_directory+"\nPlease, check permissions.")
        else:
            print_err("The destination directory does not exist. Please,\
            use the -f option to force their creation or redefine the location\
            with --directory option.")

    #Generate the related command
    file_address = ""
    if rename:
        file_address = join(dest_directory, video_rubrique, video_rubrique
        +"_"+video_date.replace('/', '_')+".flv")
    else:
        file_address = join(dest_directory, video_rubrique,
        url.split('/').pop())

    cmd ="flvstreamer -eqr "+url+" -o "+file_address
    if verbose:
        cmd.replace('-eqr','-er') 
        print '\t'+cmd
    #Check if we allow to overwrite
    if exists(file_address) and not overwrite:
        #print file_address+" already exists"
        print video_rubrique+"_"+video_date.replace('/', '_')+".flv already exists"
    elif exists(file_address) and overwrite:
        #Remove file if we can overwrite
        print 'Removing '+file_address
        remove(file_address)
        p = Popen(cmd, shell=True)
    else:
        p = Popen(cmd, shell=True)


def usage():
    print "-h: display help"
    print "-o: force overwritting for anyfiles"
    print "-v: verbose mode"
    print "-r: rename all downloaded files"
    print "-V: display the version information"
    print "-d: [directory] : path to where you store your tv show"
    print "-l: low quality videos"
    print "-f: try to create the directories hierarchy"
    print "-n: [deep]: number of requested broadcasts (0 means all, default is 1)"
    for option, name in available_show.items():
        print "-"+option+": download "+name


def version():
    print "Canal+ Daily Downloader V0.1.2"
    print "Author: Reaud Guezennec"
    print "This program is under a GPL licence"


def main():
    global dest_directory
    global verbose

    #Get option and arguments
    try:
        opts, args = getopt(argv[1:], "hvVrof".join(available_show.keys())+"n:d:q:",
        ["help", "verbose", "Version","rename-file", "overwrite", "force",
        "number=", "directory=", "quality="])
    except GetoptError, err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            usage()
            exit(2)

    #Initiate parameters
    tvshow = []
    deep = 1
    overwrite = False
    rename = False
    force = False
    verbose = False
    quality = 'high'
    #If we use this script from another python script
    #Process options and arguments
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            exit(0)
        if o in ("-q", "--quality"):
            if str(a) == 'l' or str(a) == 'low':
                quality = 'low'
            else:
                quality = 'hd'
        if o in ("-o", "--overwrite"):
            overwrite = True
        if o in ("-v", "--verbose"):
            verbose = True
        if o in ("-r", "--rename"):
            rename = True
        if o in ("-d", "--directory"):
            dest_directory = a
        if o in ("-f", "--force"):
            force = True
        if o in ("-V", "--Version"):
            version()
            exit(0)
        if o in ("-n", "--number"):
            try:
                deep = int(a)
            except ValueError:
                print "Format error : Numbers are expected"
                exit(2)
        if o.replace('-', '') in available_show.keys():
            tvshow.append(available_show[o.replace('-', '')])

    for show in tvshow:
        if verbose:
            print 'Broadcast: '+show
        try:
            buildURLdico(show, deep, quality, verbose)
            for url in URLdico:
                downloadURL(url, verbose, overwrite, force, rename)
            URLdico.clear()
        except OSError:
            print "Error: flvstreamer is not installed,\
            destination does not exits or URL is wrong"


if __name__ == "__main__":
    main()
