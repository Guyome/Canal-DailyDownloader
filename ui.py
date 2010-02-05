#!/usr/bin/env python

import gtk
import pygtk
import canal
from canal import available_show
import gobject

deep = ["d'aujourd'hui", "jusqu'a hier", "depuis 3 jours","Aucune"]

class ShowDeep(gtk.HBox):
    def __init__( self, label, value_list):
        self.box = gtk.HBox(True)
        self.combobox = gtk.combo_box_new_text()
        for value in value_list:
            self.combobox.append_text(value)
        self.select_index = self.combobox.get_active()

        self.box.add(gtk.Label(label))
        self.box.add(self.combobox)
        self.combobox.set_active(3)
        self.combobox.connect('changed', self.changed_cb)

        self.box.show_all()

    def changed_cb(self, combobox):
        self.select_index = combobox.get_active()

    def get_vbox(self):
        return self.box

    def get_date_index(self):
        return self.select_index

class CanalUI:

    def on_destination_selection_changed(self, event):
        self.adresse = self.folder.get_filename()

    def on_apply_clicked(self, event):
        self.expander.set_expanded(False)
        self.expander.hide
        self.progress.show
        self.progress.pulse
        while gtk.events_pending():
            gtk.main_iteration()
        for show in available_show.values():
            try:
                deep = self.box_list[show].get_date_index()
                if deep not in (-1,3):
                    count = 1
                    canal.buildURLdico(show, deep+1, 'high', True)
                    for url in canal.URLdico:
                        self.progress.set_text(show+': '+str(count)+
                            ' sur '+str(deep+1))
                        #try:
                        #canal.downloadURL(url, True, True,True)
                        #except:
                        #    print 'Error when downloading '+url
                        self.progress.set_fraction(float(count)/(deep+1))
                        while gtk.events_pending():
                            gtk.main_iteration()
                        count += 1
                    canal.URLdico.clear()
            except AttributeError:
                print "Error: flvstreamer is not installed,\
                destination does not exits or URL is wrong"

    def gtk_widget_destroy(self, window):
        gtk.main_quit()

    def __init__( self ):
        builder = gtk.Builder()
        builder.add_from_file("canal.glade")

        self.window = builder.get_object("main")
        self.folder = builder.get_object("destination")
        self.expander = builder.get_object("expander1")
        self.progress = builder.get_object("progressbar")
        self.show_choose = builder.get_object("show_choose")
        self.progress.hide()
        self.adresse = "/home/guillaume/Videos/"
        self.folder.set_filename(self.adresse)
        self.box_list = {}

        for show in available_show.values():
            self.box_list[show] = ShowDeep(show,deep)
            self.show_choose.add(self.box_list[show].get_vbox())
            
        builder.connect_signals( self )

if __name__ == "__main__":
    gui = CanalUI()
    gui.window.show()
    gtk.main()

