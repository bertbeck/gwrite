#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''config
@author: U{Jiahua Huang <jhuangjiahua@gmail.com>}
@license: LGPLv3+
'''

import gtk, gobject
import os, sys

try: import cPickle as pickle
except: import pickle

try: import i18n
except: from gettext import gettext as _

single_instance_mode = 0
mdi_mode = 1
autosaveinterval = 15

def getconf():
    '''获取 config
    '''
    config = {}
    ##
    profdir = os.environ['HOME'] + '/.config/GWrite'
    if not os.path.isdir(profdir): os.makedirs(profdir)
    autosavedir = os.environ['HOME'] + '/.cache/GWrite/autosave'
    if not os.path.isdir(autosavedir): os.makedirs(autosavedir)
    ctlfile = profdir + '/gwrite.ctl' + os.environ['DISPLAY']
    prof = profdir + '/gwrite.conf'
    user_stylesheet_file = profdir + '/user_stylesheet_uri.css'
    ##    
    for k, v in globals().items():
        if not k.startswith('__') and (
              isinstance(v, str) 
           or isinstance(v, int)
           or isinstance(v, long)
           or isinstance(v, float)
           or isinstance(v, dict)
           or isinstance(v, list)
           or isinstance(v, bool)
           ):
            config[k] = v
            pass
    config['profdir'] = profdir
    config['autosavedir'] = autosavedir
    config['autosaveinterval'] = autosaveinterval
    config['ctlfile'] = ctlfile
    config['prof'] = prof
    config['user_stylesheet_file'] = user_stylesheet_file
    return config

def load():
    '''读取 config
    '''
    config = getconf()
    ##
    try: config.update(pickle.loads(file(config['prof']).read()))
    except: pass
    ##
    globals().update(config)
    return config

def write():
    '''保存 config
    '''
    config = getconf()
    file(config['prof'], 'w').write(pickle.dumps(config))
    return config

def show_preference_dlg(title=_("Preferences"), parent=None, *args):
    '''首选项对话框
    '''
    dlg = gtk.Dialog(title, parent, gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OK, gtk.RESPONSE_OK    ))
    dlg.set_default_size(200, 300)
    ##
    config = getconf()
    ##
    notebook1 = gtk.Notebook()
    notebook1.set_tab_pos(gtk.POS_TOP)
    notebook1.set_scrollable(False)
    notebook1.show()

    vbox1 = gtk.VBox(False, 0)
    vbox1.show()
    vbox1.set_spacing(0)

    checkbutton_mdi_mode = gtk.CheckButton()
    checkbutton_mdi_mode.set_active(False)
    checkbutton_mdi_mode.set_label(_("Use Tabs MDI interface"))
    checkbutton_mdi_mode.set_tooltip_text(_("Supports editing multiple files in one window (known sometimes as tabs or MDI)"))
    checkbutton_mdi_mode.show()
    checkbutton_mdi_mode.set_border_width(10)
    checkbutton_mdi_mode.set_relief(gtk.RELIEF_NORMAL)

    vbox1.pack_start(checkbutton_mdi_mode, False, False, 0)

    checkbutton_single_instance_mode = gtk.CheckButton()
    checkbutton_single_instance_mode.set_active(False)
    checkbutton_single_instance_mode.set_label(_("Single Instance mode"))
    checkbutton_single_instance_mode.set_tooltip_text(_("Only one instance of the application will be running at a time."))
    checkbutton_single_instance_mode.show()
    checkbutton_single_instance_mode.set_border_width(10)
    checkbutton_single_instance_mode.set_relief(gtk.RELIEF_NORMAL)

    vbox1.pack_start(checkbutton_single_instance_mode, False, False, 0)

    hseparator1 = gtk.HSeparator()
    hseparator1.show()
    vbox1.pack_start(hseparator1, False, False, 0)

    label2 = gtk.Label(_("You need to restart gwrite for some options to take effect."))
    label2.set_alignment(0, 0)
    label2.set_angle(0)
    label2.set_padding(20, 20)
    label2.set_line_wrap(True)
    label2.set_width_chars(30)
    label2.show()
    vbox1.pack_start(label2)

    label1 = gtk.Label(_("Run mode"))
    label1.set_angle(0)
    label1.set_padding(0, 0)
    label1.set_line_wrap(False)
    label1.show()
    notebook1.append_page(vbox1, label1)
    ##
    checkbutton_mdi_mode.set_active(config.get("mdi_mode", 0))
    checkbutton_single_instance_mode.set_active(config.get("single_instance_mode", 0))

    ##
    vbox2 = gtk.VBox(False, 0)
    vbox2.show()
    vbox2.set_spacing(10)

    label2 = gtk.Label(_("File Saving"))
    label2.set_angle(0)
    label2.set_padding(0, 0)
    label2.set_line_wrap(False)
    label2.show()
    notebook1.append_page(vbox2, label2)

    vbox1 = gtk.VBox(False, 0)
    vbox1.show()
    vbox1.set_spacing(0)

    hbox1 = gtk.HBox(False, 0)
    hbox1.show()
    hbox1.set_spacing(0)

    label3 = gtk.Label(_("Autosave files every:"))
    label3.set_angle(0)
    label3.set_padding(10, 10)
    label3.set_line_wrap(False)
    label3.show()
    hbox1.pack_start(label3, False, False, 0)

    spinbutton1 = gtk.SpinButton(gtk.Adjustment(value=0, lower=0, upper=180, step_incr=1, page_incr=10))
    spinbutton1.set_value(float(config['autosaveinterval']))
    spinbutton1.show()

    hbox1.pack_start(spinbutton1, False, False, 0)

    label2 = gtk.Label(_("minutes"))
    label2.set_angle(0)
    label2.set_padding(0, 0)
    label2.set_line_wrap(False)
    label2.show()
    hbox1.pack_start(label2, False, False, 0)

    vbox1.pack_start(hbox1, True, True, 0)
    vbox2.pack_start(vbox1, False, False, 0)

    ##
    dlg.vbox.pack_start(notebook1, True, True, 0)
    resp = dlg.run()
    ##
    config['mdi_mode'] = checkbutton_mdi_mode.get_active()
    config['single_instance_mode'] = checkbutton_single_instance_mode.get_active()
    config['autosaveinterval'] = spinbutton1.get_value()
    ##
    dlg.destroy()
    if resp == gtk.RESPONSE_CANCEL:
        return {}    
    globals().update(config)
    return config


if __name__=="__main__":
    load()
    print show_preference_dlg()
    write()


