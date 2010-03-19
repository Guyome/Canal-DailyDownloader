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
from os import remove, makedirs, waitpid, rename
from os.path import join, expanduser, exists
from subprocess import Popen
import re
import sys

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
                  "Q": "grand journal", 
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
                  "grand journal": 5, 
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
    url= url_canal + currentTvShow.replace(' ','%20')
    print_dbg("XML URL: " + url)
    try:
        xml = urlopen(url)
#        print xml.read()
        dom = minidom.parse(xml)
        xml.close()
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
        video_rubrique.lower().find(currentTvShow.lower().replace(' ','_'))>-1:
            for datevideo in datenodelist:
                #Read video url and date
                video_url = str(debitnodelist[0].firstChild.nodeValue)
                video_show_title = node.getElementsByTagName('TITRE')[0].firstChild.nodeValue
                video_show_subtitle = node.getElementsByTagName('SOUS_TITRE')[0].firstChild.nodeValue
                video_fulltitle = reformat_date_to_ISO(video_show_title) + " - " + reformat_date_to_ISO(video_show_subtitle)
                if video_url.find("rtmp")>-1:
                    URLdico[video_url]=(video_fulltitle, video_rubrique)
                    print_verbose(" + " + video_url)

def reformat_date_to_ISO(string):
    # Grand Journal, Zapping
    ret = re.sub(r'(.*)(\d\d)/(\d\d)/(\d\d)(.*)', r'\g<1>20\g<4>-\g<3>-\g<2>\g<5>', string)
    # Petite seamine
    ret = re.sub(r'(.*)(\d\d)/(\d\d)(.*)', r'\g<1>2010-\g<3>-\g<2>\g<4>', ret)
    return ret

def process_vod(url, overwrite, force, rename):
    print_dbg("FLV URL: " + url)
    item = URLdico[url]# consultaion URLdico
    video_fulltitle, video_rubrique = item[0], item[1]
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
    filename = ""
    if rename:
        fileext = url.split('.').pop()
        filename = video_fulltitle + "." + fileext
    else:
        filename = url.split('/').pop()
    destination = join(dest_directory, video_rubrique, filename)

    #Check if we allow to overwrite
    if exists(destination) and not overwrite:
        print_verbose("Skipping \"" + filename + "\", destination already exists")
    elif exists(destination) and overwrite:
        #Remove file if we can overwrite
        print_verbose("Removing " + filename)
        remove(destination)
        download_url(url, destination)
    else:
        download_url(url, destination)

def download_url(url, dest):
    cmd = "flvstreamer -eqr " + url + " -o " + dest.replace(" ", "\ ") + ".incomplete"
    if verbose:
        cmd = cmd.replace('-eqr','-er', 1) 
    if(execute(cmd) != 0):
        print_err("Something goes wrong while running flvstreamer")
    else:
        rename(dest + ".incomplete", dest)
        print_verbose(url + " have been successfully downloaded (" + dest + ")")

def execute(cmd):
    print_dbg ("cmd: \"" + cmd + "\"")
    returncode = -1
    try:
        p = Popen(cmd, shell=True)
        returncode = waitpid(p.pid, 0)[1]
        print_dbg("execution return code: " + str(returncode))
    except OSError:
        print_err("Unable to execute: \"" + cmd + "\"")
    return returncode

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
            print_dbg("Verbose mode on.")
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
        print_dbg('Broadcast: ' + show)
        buildURLdico(show, deep, quality)
        for url in URLdico:
            process_vod(url, overwrite, force, rename)
        URLdico.clear()


if __name__ == "__main__":
    main()
