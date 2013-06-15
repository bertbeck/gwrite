#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''GWrite
@author: U{Jiahua Huang <jhuangjiahua@gmail.com>}
@license: LGPLv3+
'''

__version__ = '0.5.1'

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gdk

import gtkdialogs
import gtklatex
import config

import os, sys
import thread
import re
import urllib2
import time

try: import i18n
except: from gettext import gettext as _

def get_doctitle(html):
    title = ''
    title = (re.findall(r'''<title>([^\0]*)</title>''', html)+[_("NewDocument")])[0]
    return title


def proc_webkit_color(*webviews):
    ## 设置样式，让 WebKit 背景色使用 Gtk 颜色
    style = webviews[0].get_style()
    v = Gtk.TextView()
    v.show()
    html_bg_color = v.get_style_context().get_background_color(Gtk.StateFlags.NORMAL).to_string()
    v.destroy()
    #html_fg_color = style.text[Gtk.StateType.NORMAL]
    user_stylesheet = ''' html {
        background-color: %s;
        }\n''' % (
            html_bg_color,
        )
    user_stylesheet_file = config.user_stylesheet_file
    file(user_stylesheet_file, 'w').write(user_stylesheet)
    user_stylesheet_uri = 'file://' + user_stylesheet_file
    for webview in webviews:
        settings = webview.get_settings()
        settings.set_property('user-stylesheet-uri', user_stylesheet_uri)
    pass

def menu_find_with_stock(menu, stock):
    # 查找菜单中对应 stock 的菜单项位置
    n = 0
    for i in menu.get_children():
        try:
            if i.get_image().get_stock()[0] == stock:
                return n
        except:
            pass
        n += 1
        pass
    return -1

Windows = []
new_num = 1
Title = _("GWrite")
## 是否单实例模式
#single_instance_mode = 0
#mdi_mode = 1

class MainWindow:
    def __init__(self, editfile='', create = True, accel_group = None):
        self.editfile = editfile
        ## 考虑已经打开文档的情况
        if editfile:
            for i in Windows:
                if i.editfile == editfile:
                    #-print _('File "%s" already opened') % editfile
                    i.window.show()
                    i.window.present()
                    #@TODO: 让 edit 获得焦点
                    i.window.grab_focus()
                    i.edit.grab_focus()
                    del self
                    return
                pass
            pass
        ##
        Windows.append(self)
        import webkitedit # 推迟 import webkitedit
        ##
        if accel_group is None:
            self.accel_group = Gtk.AccelGroup()
        else:
            self.accel_group = accel_group
        if create:
            self.window = Gtk.Window()
            self.window.set_default_icon_name("gtk-dnd")
            self.window.set_icon_name("gtk-dnd")
            self.window.set_default_size(780, 550)
            self.window.set_title(Title)
            if editfile: self.window.set_title(os.path.basename(self.editfile) + ' - ' + Title) 
            self.window.add_accel_group(self.accel_group)
            self.window.show()
            self.window.connect("delete_event", self.on_close)

        ## 用 Alt-1, Alt-2... 来切换标签页，Gdk.ModifierType.MOD1_MASK 是 Alt
        for k in range(1, 10):
            self.accel_group.connect(Gdk.keyval_from_name(str(k)), Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE, self.on_accel_connect)
            pass

        self.vbox1 = Gtk.VBox(False, 0)
        self.vbox1.show()

        menubar1 = Gtk.MenuBar()
        menubar1.show()

        menuitem_file = Gtk.MenuItem.new_with_mnemonic(_("_File"))
        menuitem_file.show()

        menu_file = Gtk.Menu()
        menu_file.append(Gtk.TearoffMenuItem())
        self.menu_file = menu_file

        menuitem_new = Gtk.ImageMenuItem.new_from_stock("gtk-new", self.accel_group)
        menuitem_new.show()
        menuitem_new.connect("activate", self.on_new)
        menuitem_new.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("n"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        menu_file.append(menuitem_new)

        if config.mdi_mode:
            menuitem_new_window = Gtk.ImageMenuItem.new_with_mnemonic(_("New _Window"))
            menuitem_new_window.show()
            img = Gtk.Image.new_from_stock(Gtk.STOCK_NEW, Gtk.IconSize.MENU)
            menuitem_new_window.set_image(img)
            menuitem_new_window.connect("activate", self.on_new_window)
            menuitem_new_window.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("n"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)

            menu_file.append(menuitem_new_window)
            pass

        menuitem_open = Gtk.ImageMenuItem.new_from_stock("gtk-open", self.accel_group)
        menuitem_open.show()
        menuitem_open.connect("activate", self.on_open)
        menuitem_open.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("o"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)


        menu_file.append(menuitem_open)

        menuitem_save = Gtk.ImageMenuItem.new_from_stock("gtk-save", self.accel_group)
        menuitem_save.show()
        menuitem_save.connect("activate", self.on_save)
        menuitem_save.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("s"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)


        menu_file.append(menuitem_save)

        menuitem_save_as = Gtk.ImageMenuItem.new_from_stock("gtk-save-as", self.accel_group)
        menuitem_save_as.show()
        menuitem_save_as.connect("activate", self.on_save_as)

        menu_file.append(menuitem_save_as)

        menu_file.append(Gtk.SeparatorMenuItem.new())

        menuitem = Gtk.ImageMenuItem.new_from_stock("gtk-properties", self.accel_group)
        menuitem.show()
        menuitem.connect("activate", self.on_word_counts)

        menu_file.append(menuitem)

        menuitem_print = Gtk.ImageMenuItem.new_from_stock("gtk-print", self.accel_group)
        menuitem_print.show()
        menuitem_print.connect("activate", self.on_print)
        menuitem_print.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("p"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        
        menu_file.append(menuitem_print)

        menu_file.append(Gtk.SeparatorMenuItem.new())

        ## 最近使用文件菜单 ################
        self.recent = Gtk.RecentManager()
        menu_recent = Gtk.RecentChooserMenu()
        menu_recent.set_limit(25)
        #if editfile: self.add_recent(editfile) #改在 new_edit() 里统一添加
        ##
        self.file_filter = Gtk.RecentFilter()
        self.file_filter.add_mime_type("text/html")
        menu_recent.set_filter(self.file_filter)

        menu_recent.connect("item-activated", self.on_select_recent)
        menuitem_recent = Gtk.ImageMenuItem.new_with_mnemonic(_("_Recently"))
        menuitem_recent.set_image(Gtk.Image.new_from_icon_name("document-open-recent", Gtk.IconSize.MENU))

        menuitem_recent.set_submenu(menu_recent)
        menu_file.append(menuitem_recent)
        #####################################

        menuitem_separatormenuitem1 = Gtk.SeparatorMenuItem.new()
        menuitem_separatormenuitem1.show()

        menu_file.append(menuitem_separatormenuitem1)

        menuitem_close = Gtk.ImageMenuItem.new_from_stock("gtk-close", self.accel_group)
        menuitem_close.show()
        menuitem_close.connect("activate", self.close_tab)
        menuitem_close.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("w"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        menu_file.append(menuitem_close)
        
        if config.mdi_mode:
            menuitem_close_window = Gtk.ImageMenuItem.new_with_mnemonic(_("Close Win_dow"))
            menuitem_close_window.show()
            img = Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU)
            menuitem_close_window.set_image(img)
            menuitem_close_window.connect("activate", self.on_close)
            menuitem_close_window.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("w"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)

            menu_file.append(menuitem_close_window)
            pass

        menuitem_quit = Gtk.ImageMenuItem.new_from_stock("gtk-quit", self.accel_group)
        menuitem_quit.show()
        menuitem_quit.connect("activate", self.on_quit)
        menuitem_quit.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("q"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)


        menu_file.append(menuitem_quit)

        menuitem_file.set_submenu(menu_file)

        menubar1.append(menuitem_file)

        menuitem_edit = Gtk.MenuItem.new_with_mnemonic(_("_Edit"))
        menuitem_edit.show()

        menu_edit = Gtk.Menu()
        menu_edit.append(Gtk.TearoffMenuItem())

        menuitem_undo = Gtk.ImageMenuItem.new_from_stock("gtk-undo", self.accel_group)
        menuitem_undo.show()
        menuitem_undo.connect("activate", self.do_undo)

        menu_edit.append(menuitem_undo)

        menuitem_redo = Gtk.ImageMenuItem.new_from_stock("gtk-redo", self.accel_group)
        menuitem_redo.show()
        menuitem_redo.connect("activate", self.do_redo)

        menu_edit.append(menuitem_redo)

        menuitem_separator2 = Gtk.SeparatorMenuItem.new()
        menuitem_separator2.show()

        menu_edit.append(menuitem_separator2)

        menuitem_cut = Gtk.ImageMenuItem.new_from_stock("gtk-cut", self.accel_group)
        menuitem_cut.show()
        menuitem_cut.connect("activate", self.do_cut)

        menu_edit.append(menuitem_cut)

        menuitem_copy = Gtk.ImageMenuItem.new_from_stock("gtk-copy", self.accel_group)
        menuitem_copy.show()
        menuitem_copy.connect("activate", self.do_copy)

        menu_edit.append(menuitem_copy)

        menuitem_paste = Gtk.ImageMenuItem.new_from_stock("gtk-paste", self.accel_group)
        menuitem_paste.show()
        menuitem_paste.connect("activate", self.do_paste)

        menu_edit.append(menuitem_paste)

        menuitem_paste_unformatted = Gtk.ImageMenuItem.new_with_mnemonic(_("Pa_ste Unformatted"))
        menuitem_paste_unformatted.show()
        menuitem_paste_unformatted.connect("activate", self.do_paste_unformatted)
        menuitem_paste_unformatted.add_accelerator("activate", 
                self.accel_group, Gdk.keyval_from_name("v"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)
        menu_edit.append(menuitem_paste_unformatted)

        menuitem_delete = Gtk.ImageMenuItem.new_from_stock("gtk-delete", self.accel_group)
        menuitem_delete.show()
        menuitem_delete.connect("activate", self.do_delete)

        menu_edit.append(menuitem_delete)

        menuitem_separator3 = Gtk.SeparatorMenuItem.new()
        menuitem_separator3.show()

        menu_edit.append(menuitem_separator3)

        menuitem_select_all = Gtk.ImageMenuItem.new_from_stock("gtk-select-all", self.accel_group)
        menuitem_select_all.show()
        menuitem_select_all.connect("activate", self.do_selectall)

        menu_edit.append(menuitem_select_all)

        menuitem_separator12 = Gtk.SeparatorMenuItem.new()
        menuitem_separator12.show()

        menu_edit.append(menuitem_separator12)

        menuitem_find = Gtk.ImageMenuItem.new_from_stock("gtk-find", self.accel_group)
        menuitem_find.show()
        menuitem_find.connect("activate", self.show_findbar)
        menuitem_find.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("f"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)


        menu_edit.append(menuitem_find)

        menuitem_find_and_replace = Gtk.ImageMenuItem.new_from_stock("gtk-find-and-replace", self.accel_group)
        menuitem_find_and_replace.show()
        menuitem_find_and_replace.connect("activate", self.show_findbar)

        menu_edit.append(menuitem_find_and_replace)
        ##

        menu_edit.append(Gtk.SeparatorMenuItem.new())

        menuitem = Gtk.ImageMenuItem.new_from_stock("gtk-preferences", self.accel_group)
        menuitem.show()
        menuitem.connect("activate", lambda *i: (config.show_preference_dlg(), config.write()))

        menu_edit.append(menuitem)
        ##

        menuitem_edit.set_submenu(menu_edit)

        menubar1.append(menuitem_edit)

        menuitem_view = Gtk.MenuItem.new_with_mnemonic(_("_View"))
        menuitem_view.show()

        menu_view = Gtk.Menu()
        menu_view.append(Gtk.TearoffMenuItem())

        ## 缩放菜单
        menuitem_zoom_in = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_ZOOM_IN, self.accel_group)
        menuitem_zoom_in.connect("activate", self.zoom_in)
        # Ctrl++
        menuitem_zoom_in.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("equal"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        menuitem_zoom_in.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("plus"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        menuitem_zoom_in.show()
        menu_view.append(menuitem_zoom_in)

        menuitem_zoom_out = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_ZOOM_OUT, self.accel_group)
        menuitem_zoom_out.connect("activate", self.zoom_out)
        # Ctrl+-
        menuitem_zoom_out.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("minus"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        menuitem_zoom_out.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("underscore"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        menuitem_zoom_out.show()
        menu_view.append(menuitem_zoom_out)

        menuitem_zoom_100 = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_ZOOM_100, self.accel_group)
        menuitem_zoom_100.connect("activate", self.zoom_100)
        # Ctrl+0
        menuitem_zoom_100.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("0"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        menuitem_zoom_100.show()
        menu_view.append(menuitem_zoom_100)

        ##
        menuitem_separator10 = Gtk.SeparatorMenuItem.new()
        menuitem_separator10.show()
        menu_view.append(menuitem_separator10)

        menuitem_update_contents = Gtk.ImageMenuItem.new_with_mnemonic(_("Update _Contents"))
        menuitem_update_contents.show()
        menuitem_update_contents.connect("activate", self.view_update_contents)

        img = Gtk.Image.new_from_stock(Gtk.STOCK_INDEX, Gtk.IconSize.MENU)
        menuitem_update_contents.set_image(img)
        menu_view.append(menuitem_update_contents)

        menuitem_toggle_numbered_title = Gtk.ImageMenuItem.new_with_mnemonic(_("Toggle _Numbered Title"))
        menuitem_toggle_numbered_title.show()
        menuitem_toggle_numbered_title.connect("activate", self.view_toggle_autonumber)

        img = Gtk.Image.new_from_stock(Gtk.STOCK_SORT_DESCENDING, Gtk.IconSize.MENU)
        menuitem_toggle_numbered_title.set_image(img)
        menu_view.append(menuitem_toggle_numbered_title)

        menuitem_update_images = Gtk.ImageMenuItem.new_with_mnemonic(_("Update _Images"))
        menuitem_update_images.show()
        menuitem_update_images.connect("activate", self.do_update_images)

        img = Gtk.Image.new_from_icon_name('stock_insert_image', Gtk.IconSize.MENU)
        menuitem_update_images.set_image(img)
        menu_view.append(menuitem_update_images)

        menuitem_separator10 = Gtk.SeparatorMenuItem.new()
        menuitem_separator10.show()

        menu_view.append(menuitem_separator10)

        menuitem_view_source = Gtk.ImageMenuItem.new_with_mnemonic(_("So_urce/Visual"))
        menuitem_view_source.show()
        menuitem_view_source.connect("activate", self.view_sourceview)
        menuitem_view_source.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("u"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_view-html-source', Gtk.IconSize.MENU)
        menuitem_view_source.set_image(img)
        menu_view.append(menuitem_view_source)

        menuitem_view.set_submenu(menu_view)

        menubar1.append(menuitem_view)

        menuitem_insert = Gtk.MenuItem.new_with_mnemonic(_("_Insert"))
        menuitem_insert.show()

        menu_insert = Gtk.Menu()
        menu_insert.append(Gtk.TearoffMenuItem())

        menuitem_picture = Gtk.ImageMenuItem.new_with_mnemonic(_("_Picture"))
        menuitem_picture.show()
        menuitem_picture.connect("activate", self.do_insertimage)

        img = Gtk.Image.new_from_icon_name('stock_insert_image', Gtk.IconSize.MENU)
        menuitem_picture.set_image(img)
        menu_insert.append(menuitem_picture)

        menuitem_link = Gtk.ImageMenuItem.new_with_mnemonic(_("_Link"))
        menuitem_link.show()
        menuitem_link.connect("activate", self.do_createlink)
        menuitem_link.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("k"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_link', Gtk.IconSize.MENU)
        menuitem_link.set_image(img)
        menu_insert.append(menuitem_link)

        menuitem_horizontalrule = Gtk.ImageMenuItem.new_with_mnemonic(_("Horizontal_Rule"))
        menuitem_horizontalrule.show()
        menuitem_horizontalrule.connect("activate", self.do_inserthorizontalrule)

        img = Gtk.Image.new_from_icon_name('stock_insert-rule', Gtk.IconSize.MENU)
        menuitem_horizontalrule.set_image(img)
        menu_insert.append(menuitem_horizontalrule)

        menuitem_insert_table = Gtk.ImageMenuItem.new_with_mnemonic(_("_Table"))
        menuitem_insert_table.show()
        menuitem_insert_table.connect("activate", self.do_insert_table)

        img = Gtk.Image.new_from_icon_name('stock_insert-table', Gtk.IconSize.MENU)
        menuitem_insert_table.set_image(img)
        menu_insert.append(menuitem_insert_table)

        menuitem_insert_html = Gtk.ImageMenuItem.new_with_mnemonic(_("_HTML"))
        menuitem_insert_html.show()
        menuitem_insert_html.connect("activate", self.do_insert_html)

        img = Gtk.Image.new_from_icon_name('stock_view-html-source', Gtk.IconSize.MENU)
        menuitem_insert_html.set_image(img)
        menu_insert.append(menuitem_insert_html)

        menuitem_separator9 = Gtk.SeparatorMenuItem.new()
        menuitem_separator9.show()

        menu_insert.append(menuitem_separator9)

        ##
        menuitem_latex_math_equation = Gtk.ImageMenuItem.new_with_mnemonic(_("LaTeX _Equation"))
        menuitem_latex_math_equation.show()
        menuitem_latex_math_equation.connect("activate", self.do_insert_latex_math_equation)

        menu_insert.append(menuitem_latex_math_equation)
        
        menu_insert.append(Gtk.SeparatorMenuItem.new())
        ##

        menuitem_insert_contents = Gtk.ImageMenuItem.new_with_mnemonic(_("_Contents"))
        menuitem_insert_contents.show()
        menuitem_insert_contents.connect("activate", self.do_insert_contents)

        img = Gtk.Image.new_from_stock(Gtk.STOCK_INDEX, Gtk.IconSize.MENU)
        menuitem_insert_contents.set_image(img)
        menu_insert.append(menuitem_insert_contents)

        menuitem_insert.set_submenu(menu_insert)

        menubar1.append(menuitem_insert)

        menuitem_style = Gtk.MenuItem.new_with_mnemonic(_("_Style"))
        menuitem_style.show()

        menu_style = Gtk.Menu()
        menu_style.append(Gtk.TearoffMenuItem())

        menuitem_normal = Gtk.ImageMenuItem.new_with_mnemonic(_("_Normal"))
        menuitem_normal.show()
        menuitem_normal.connect("activate", self.do_formatblock_p)
        menuitem_normal.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("0"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_insert_section', Gtk.IconSize.MENU)
        menuitem_normal.set_image(img)
        menu_style.append(menuitem_normal)

        menuitem_separator4 = Gtk.SeparatorMenuItem.new()
        menuitem_separator4.show()

        menu_style.append(menuitem_separator4)

        menuitem_heading_1 = Gtk.ImageMenuItem.new_with_mnemonic(_("Heading _1"))
        menuitem_heading_1.show()
        menuitem_heading_1.connect("activate", self.do_formatblock_h1)
        menuitem_heading_1.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("1"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_insert-header', Gtk.IconSize.MENU)
        menuitem_heading_1.set_image(img)
        menu_style.append(menuitem_heading_1)

        menuitem_heading_2 = Gtk.ImageMenuItem.new_with_mnemonic(_("Heading _2"))
        menuitem_heading_2.show()
        menuitem_heading_2.connect("activate", self.do_formatblock_h2)
        menuitem_heading_2.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("2"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_line-spacing-2', Gtk.IconSize.MENU)
        menuitem_heading_2.set_image(img)
        menu_style.append(menuitem_heading_2)

        menuitem_heading_3 = Gtk.ImageMenuItem.new_with_mnemonic(_("Heading _3"))
        menuitem_heading_3.show()
        menuitem_heading_3.connect("activate", self.do_formatblock_h3)
        menuitem_heading_3.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("3"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_line-spacing-1', Gtk.IconSize.MENU)
        menuitem_heading_3.set_image(img)
        menu_style.append(menuitem_heading_3)

        menuitem_heading_4 = Gtk.ImageMenuItem.new_with_mnemonic(_("Heading _4"))
        menuitem_heading_4.show()
        menuitem_heading_4.connect("activate", self.do_formatblock_h4)
        menuitem_heading_4.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("4"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_line-spacing-1.5', Gtk.IconSize.MENU)
        menuitem_heading_4.set_image(img)
        menu_style.append(menuitem_heading_4)

        menuitem_heading_5 = Gtk.ImageMenuItem.new_with_mnemonic(_("Heading _5"))
        menuitem_heading_5.show()
        menuitem_heading_5.connect("activate", self.do_formatblock_h5)
        menuitem_heading_5.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("5"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_list_enum-off', Gtk.IconSize.MENU)
        menuitem_heading_5.set_image(img)
        menu_style.append(menuitem_heading_5)

        menuitem_heading_6 = Gtk.ImageMenuItem.new_with_mnemonic(_("Heading _6"))
        menuitem_heading_6.show()
        menuitem_heading_6.connect("activate", self.do_formatblock_h6)
        menuitem_heading_6.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("6"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_list_enum-off', Gtk.IconSize.MENU)
        menuitem_heading_6.set_image(img)
        menu_style.append(menuitem_heading_6)

        menuitem_separator5 = Gtk.SeparatorMenuItem.new()
        menuitem_separator5.show()

        menu_style.append(menuitem_separator5)

        menuitem_bulleted_list = Gtk.ImageMenuItem.new_with_mnemonic(_("_Bulleted List"))
        menuitem_bulleted_list.show()
        menuitem_bulleted_list.connect("activate", self.do_insertunorderedlist)

        img = Gtk.Image.new_from_icon_name('stock_list_bullet', Gtk.IconSize.MENU)
        menuitem_bulleted_list.set_image(img)
        menu_style.append(menuitem_bulleted_list)

        menuitem_numbered_list = Gtk.ImageMenuItem.new_with_mnemonic(_("Numbered _List"))
        menuitem_numbered_list.show()
        menuitem_numbered_list.connect("activate", self.do_insertorderedlist)

        img = Gtk.Image.new_from_icon_name('stock_list_enum', Gtk.IconSize.MENU)
        menuitem_numbered_list.set_image(img)
        menu_style.append(menuitem_numbered_list)

        menuitem_separator6 = Gtk.SeparatorMenuItem.new()
        menuitem_separator6.show()

        menu_style.append(menuitem_separator6)

        div1 = Gtk.ImageMenuItem.new_with_mnemonic(_("Di_v"))
        div1.show()
        div1.connect("activate", self.do_formatblock_div)

        img = Gtk.Image.new_from_icon_name('stock_tools-hyphenation', Gtk.IconSize.MENU)
        div1.set_image(img)
        menu_style.append(div1)

        address1 = Gtk.ImageMenuItem.new_with_mnemonic(_("A_ddress"))
        address1.show()
        address1.connect("activate", self.do_formatblock_address)

        img = Gtk.Image.new_from_icon_name('stock_tools-hyphenation', Gtk.IconSize.MENU)
        address1.set_image(img)
        menu_style.append(address1)

        #menuitem_formatblock_code = Gtk.ImageMenuItem.new_with_mnemonic(_("_Code"))
        #menuitem_formatblock_code.show()
        #menuitem_formatblock_code.connect("activate", self.do_formatblock_code)
        #
        #img = Gtk.Image.new_from_icon_name('stock_text-monospaced', Gtk.IconSize.MENU)
        #menuitem_formatblock_code.set_image(img)
        #menu_style.append(menuitem_formatblock_code)

        menuitem_formatblock_blockquote = Gtk.ImageMenuItem.new_with_mnemonic(_("Block_quote"))
        menuitem_formatblock_blockquote.show()
        menuitem_formatblock_blockquote.connect("activate", self.do_formatblock_blockquote)

        img = Gtk.Image.new_from_icon_name('stock_list-insert-unnumbered', Gtk.IconSize.MENU)
        menuitem_formatblock_blockquote.set_image(img)
        menu_style.append(menuitem_formatblock_blockquote)

        menuitem_formatblock_pre = Gtk.ImageMenuItem.new_with_mnemonic(_("_Preformat"))
        menuitem_formatblock_pre.show()
        menuitem_formatblock_pre.connect("activate", self.do_formatblock_pre)
        menuitem_formatblock_pre.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("t"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_text-quickedit', Gtk.IconSize.MENU)
        menuitem_formatblock_pre.set_image(img)
        menu_style.append(menuitem_formatblock_pre)

        menuitem_style.set_submenu(menu_style)

        menubar1.append(menuitem_style)

        menuitem_format = Gtk.MenuItem.new_with_mnemonic(_("For_mat"))
        menuitem_format.show()

        menu_format = Gtk.Menu()
        menu_format.append(Gtk.TearoffMenuItem())

        menuitem_bold = Gtk.ImageMenuItem.new_from_stock("gtk-bold", self.accel_group)
        menuitem_bold.show()
        menuitem_bold.connect("activate", self.on_bold)
        menuitem_bold.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("b"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        menu_format.append(menuitem_bold)

        menuitem_italic = Gtk.ImageMenuItem.new_from_stock("gtk-italic", self.accel_group)
        menuitem_italic.show()
        menuitem_italic.connect("activate", self.do_italic)
        menuitem_italic.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("i"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        menu_format.append(menuitem_italic)

        menuitem_underline = Gtk.ImageMenuItem.new_from_stock("gtk-underline", self.accel_group)
        menuitem_underline.show()
        menuitem_underline.connect("activate", self.do_underline)
        menuitem_underline.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("u"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        menu_format.append(menuitem_underline)

        menuitem_strikethrough = Gtk.ImageMenuItem.new_from_stock("gtk-strikethrough", self.accel_group)
        menuitem_strikethrough.show()
        menuitem_strikethrough.connect("activate", self.do_strikethrough)

        menu_format.append(menuitem_strikethrough)

        self.separator7 = Gtk.SeparatorMenuItem.new()
        self.separator7.show()

        menu_format.append(self.separator7)

        menuitem_font_fontname = Gtk.ImageMenuItem.new_from_stock("gtk-select-font", self.accel_group)
        menuitem_font_fontname.show()
        #menuitem_font_fontname.connect("activate", self.do_font_fontname)

        ## 字体列表菜单 #########################################
        self.fontname_menu = Gtk.Menu()
        self.fontname_menu.append(Gtk.TearoffMenuItem())
        fontnames = sorted(( familie.get_name() for familie in Gtk.Label().get_pango_context().list_families() ))
        ## 调整字体列表顺序，将中文字体提至前列
        for fontname in fontnames:
            try:
                fontname.decode('ascii')
                pass
            except:
                fontnames.remove(fontname)
                fontnames.insert(0, fontname)
                pass
            pass
        for fontname in ['Serif', 'Sans', 'Sans-serif', 'Monospace', ''] + fontnames:
            if fontname:
                menu = Gtk.MenuItem(fontname)
                menu.connect("activate", self.do_font_fontname, fontname)
                pass
            else:
                menu = Gtk.SeparatorMenuItem.new()
                pass
            menu.show()
            self.fontname_menu.append(menu)
            pass
        self.fontname_menu.show()
        menuitem_font_fontname.set_submenu(self.fontname_menu)
        ###########################################

        menu_format.append(menuitem_font_fontname)

        menuitem_font_size = Gtk.ImageMenuItem.new_with_mnemonic(_("Font _Size"))
        menuitem_font_size.show()

        img = Gtk.Image.new_from_icon_name('stock_font-size', Gtk.IconSize.MENU)
        menuitem_font_size.set_image(img)
        self.font_size1_menu = Gtk.Menu()
        self.font_size1_menu.append(Gtk.TearoffMenuItem())

        menuitem_fontsize_1 = Gtk.MenuItem.new_with_mnemonic(_("_1"))
        menuitem_fontsize_1.show()
        menuitem_fontsize_1.connect("activate", self.do_fontsize_1)

        self.font_size1_menu.append(menuitem_fontsize_1)

        menuitem_fontsize_2 = Gtk.MenuItem.new_with_mnemonic(_("_2"))
        menuitem_fontsize_2.show()
        menuitem_fontsize_2.connect("activate", self.do_fontsize_2)

        self.font_size1_menu.append(menuitem_fontsize_2)

        menuitem_fontsize_3 = Gtk.MenuItem.new_with_mnemonic(_("_3"))
        menuitem_fontsize_3.show()
        menuitem_fontsize_3.connect("activate", self.do_fontsize_3)

        self.font_size1_menu.append(menuitem_fontsize_3)

        menuitem_fontsize_4 = Gtk.MenuItem.new_with_mnemonic(_("_4"))
        menuitem_fontsize_4.show()
        menuitem_fontsize_4.connect("activate", self.do_fontsize_4)

        self.font_size1_menu.append(menuitem_fontsize_4)

        menuitem_fontsize_5 = Gtk.MenuItem.new_with_mnemonic(_("_5"))
        menuitem_fontsize_5.show()
        menuitem_fontsize_5.connect("activate", self.do_fontsize_5)

        self.font_size1_menu.append(menuitem_fontsize_5)

        menuitem_fontsize_6 = Gtk.MenuItem.new_with_mnemonic(_("_6"))
        menuitem_fontsize_6.show()
        menuitem_fontsize_6.connect("activate", self.do_fontsize_6)

        self.font_size1_menu.append(menuitem_fontsize_6)

        menuitem_fontsize_7 = Gtk.MenuItem.new_with_mnemonic(_("_7"))
        menuitem_fontsize_7.show()
        menuitem_fontsize_7.connect("activate", self.do_fontsize_7)

        self.font_size1_menu.append(menuitem_fontsize_7)

        menuitem_font_size.set_submenu(self.font_size1_menu)

        menu_format.append(menuitem_font_size)

        menuitem_color = Gtk.ImageMenuItem.new_from_stock("gtk-select-color", self.accel_group)
        menuitem_color.show()
        menuitem_color.connect("activate", self.on_color_select_forecolor)

        menu_format.append(menuitem_color)

        menuitem_bg_color = Gtk.ImageMenuItem.new_with_mnemonic(_("_Highlight"))
        menuitem_bg_color.show()
        menuitem_bg_color.connect("activate", self.do_color_hilitecolor)
        menuitem_bg_color.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("h"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_text_color_hilight', Gtk.IconSize.MENU)
        menuitem_bg_color.set_image(img)
        menu_format.append(menuitem_bg_color)

        menuitem_bg_color_select = Gtk.ImageMenuItem.new_with_mnemonic(_("_HiliteColor"))
        menuitem_bg_color_select.show()
        menuitem_bg_color_select.connect("activate", self.on_color_select_hilitecolor)

        img = Gtk.Image.new_from_stock(Gtk.STOCK_SELECT_COLOR, Gtk.IconSize.MENU)
        menuitem_bg_color_select.set_image(img)
        menu_format.append(menuitem_bg_color_select)

        menuitem_clearformat = Gtk.ImageMenuItem.new_with_mnemonic(_("_Clear format"))
        img = Gtk.Image.new_from_icon_name("gtk-clear", Gtk.IconSize.MENU)
        menuitem_clearformat.set_image(img)
        menuitem_clearformat.show()
        menuitem_clearformat.connect("activate", self.do_removeformat)
        menuitem_clearformat.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("backslash"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        menu_format.append(menuitem_clearformat)

        self.separator8 = Gtk.SeparatorMenuItem.new()
        self.separator8.show()

        menu_format.append(self.separator8)

        menuitem_justifyleft = Gtk.ImageMenuItem.new_from_stock("gtk-justify-left", self.accel_group)
        menuitem_justifyleft.show()
        menuitem_justifyleft.connect("activate", self.do_justifyleft)
        menuitem_justifyleft.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("l"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)

        menu_format.append(menuitem_justifyleft)

        menuitem_justifycenter = Gtk.ImageMenuItem.new_from_stock("gtk-justify-center", self.accel_group)
        menuitem_justifycenter.show()
        menuitem_justifycenter.connect("activate", self.do_justifycenter)
        menuitem_justifycenter.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("e"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)

        menu_format.append(menuitem_justifycenter)

        menuitem_justifyright = Gtk.ImageMenuItem.new_from_stock("gtk-justify-right", self.accel_group)
        menuitem_justifyright.show()
        menuitem_justifyright.connect("activate", self.do_justifyright)
        menuitem_justifyright.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("r"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)

        menu_format.append(menuitem_justifyright)

        menuitem_justifyfull = Gtk.ImageMenuItem.new_from_stock("gtk-justify-fill", self.accel_group)
        menuitem_justifyfull.show()
        menuitem_justifyfull.connect("activate", self.do_justifyfull)
        menuitem_justifyfull.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("j"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)

        menu_format.append(menuitem_justifyfull)

        self.separator11 = Gtk.SeparatorMenuItem.new()
        self.separator11.show()

        menu_format.append(self.separator11)

        menuitem_increase_indent = Gtk.ImageMenuItem.new_from_stock("gtk-indent", self.accel_group)
        menuitem_increase_indent.show()
        menuitem_increase_indent.connect("activate", self.do_indent)

        menu_format.append(menuitem_increase_indent)

        menuitem_decrease_indent = Gtk.ImageMenuItem.new_from_stock("gtk-unindent", self.accel_group)
        menuitem_decrease_indent.show()
        menuitem_decrease_indent.connect("activate", self.do_outdent)

        menu_format.append(menuitem_decrease_indent)

        self.separator16 = Gtk.SeparatorMenuItem.new()
        self.separator16.show()

        menu_format.append(self.separator16)

        menuitem_superscript = Gtk.ImageMenuItem.new_with_mnemonic(_("Su_perscript"))
        menuitem_superscript.show()
        menuitem_superscript.connect("activate", self.do_superscript)
        menuitem_superscript.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("period"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_superscript', Gtk.IconSize.MENU)
        menuitem_superscript.set_image(img)
        menu_format.append(menuitem_superscript)

        menuitem_subscript = Gtk.ImageMenuItem.new_with_mnemonic(_("Subs_cript"))
        menuitem_subscript.show()
        menuitem_subscript.connect("activate", self.do_subscript)
        menuitem_subscript.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("comma"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        img = Gtk.Image.new_from_icon_name('stock_subscript', Gtk.IconSize.MENU)
        menuitem_subscript.set_image(img)
        menu_format.append(menuitem_subscript)

        menuitem_format.set_submenu(menu_format)

        menubar1.append(menuitem_format)
        ##
        menuitem_tools = Gtk.MenuItem.new_with_mnemonic(_("_Tools"))
        menuitem_tools.show()

        menu_tools = Gtk.Menu()
        menu_tools.append(Gtk.TearoffMenuItem())

        menuitem_word_count = Gtk.ImageMenuItem.new_with_mnemonic(_("_Word Count"))
        img = Gtk.Image.new_from_icon_name('gtk-index', Gtk.IconSize.MENU)
        menuitem_word_count.set_image(img)
        menuitem_word_count.show()
        menuitem_word_count.connect("activate", self.on_word_counts)
        menuitem_word_count.add_accelerator("activate", self.accel_group, Gdk.keyval_from_name("c"), Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE)

        menu_tools.append(menuitem_word_count)

        menuitem_tools.set_submenu(menu_tools)

        menubar1.append(menuitem_tools)
        ##
        menuitem_help = Gtk.MenuItem.new_with_mnemonic(_("_Help"))
        menuitem_help.show()

        menu_help = Gtk.Menu()
        menu_help.append(Gtk.TearoffMenuItem())

        menuitem_about = Gtk.ImageMenuItem.new_from_stock("gtk-about", self.accel_group)
        menuitem_about.show()
        menuitem_about.connect("activate", self.on_about)

        menu_help.append(menuitem_about)

        menuitem_help.set_submenu(menu_help)

        menubar1.append(menuitem_help)

        menubar1.show_all()

        self.vbox1.pack_start(menubar1, False, False, 0)

        ## 工具栏


        self.toolbar1 = Gtk.Toolbar()
        self.toolbar1.show()

        toolbutton_new = Gtk.ToolButton()
        toolbutton_new.set_tooltip_text(_("New"))
        toolbutton_new.show()
        toolbutton_new.set_stock_id(Gtk.STOCK_NEW)
        toolbutton_new.connect("clicked", self.on_new)
        self.toolbar1.add(toolbutton_new)

        toolbutton_open = Gtk.MenuToolButton()
        toolbutton_open.set_stock_id(Gtk.STOCK_OPEN)
        toolbutton_open.set_tooltip_text(_("Open"))
        toolbutton_open.show()
        #toolbutton_open.set_stock_id(Gtk.STOCK_OPEN)
        toolbutton_open.connect("clicked", self.on_open)

        ########################################
        menu_recent = Gtk.RecentChooserMenu()
        menu_recent.set_limit(25)
        #if editfile: self.add_recent(editfile) #改在 new_edit() 里统一添加
        ##
        menu_recent.set_filter(self.file_filter)

        menu_recent.connect("item-activated", self.on_select_recent)
        toolbutton_open.set_menu(menu_recent)
        self.toolbar1.add(toolbutton_open)
        ########################################

        toolbutton_save = Gtk.ToolButton()
        toolbutton_save.set_tooltip_text(_("Save"))
        toolbutton_save.show()
        toolbutton_save.set_stock_id(Gtk.STOCK_SAVE)
        toolbutton_save.connect("clicked", self.on_save)
        self.toolbar1.add(toolbutton_save)

        separatortoolitem1 = Gtk.SeparatorToolItem()
        separatortoolitem1.show()
        self.toolbar1.add(separatortoolitem1)

        toolbutton_undo = Gtk.ToolButton()
        toolbutton_undo.set_tooltip_text(_("Undo"))
        toolbutton_undo.show()
        toolbutton_undo.set_stock_id(Gtk.STOCK_UNDO)
        toolbutton_undo.connect("clicked", self.do_undo)
        self.toolbar1.add(toolbutton_undo)

        toolbutton_redo = Gtk.ToolButton()
        toolbutton_redo.set_tooltip_text(_("Redo"))
        toolbutton_redo.show()
        toolbutton_redo.set_stock_id(Gtk.STOCK_REDO)
        toolbutton_redo.connect("clicked", self.do_redo)
        self.toolbar1.add(toolbutton_redo)

        separatortoolitem3 = Gtk.SeparatorToolItem()
        separatortoolitem3.show()
        self.toolbar1.add(separatortoolitem3)

        toolbutton_cut = Gtk.ToolButton()
        toolbutton_cut.set_tooltip_text(_("Cut"))
        toolbutton_cut.show()
        toolbutton_cut.set_stock_id(Gtk.STOCK_CUT)
        toolbutton_cut.connect("clicked", self.do_cut)
        self.toolbar1.add(toolbutton_cut)

        toolbutton_copy = Gtk.ToolButton()
        toolbutton_copy.set_tooltip_text(_("Copy"))
        toolbutton_copy.show()
        toolbutton_copy.set_stock_id(Gtk.STOCK_COPY)
        toolbutton_copy.connect("clicked", self.do_copy)
        self.toolbar1.add(toolbutton_copy)

        toolbutton_paste = Gtk.ToolButton()
        toolbutton_paste.set_tooltip_text(_("Paste"))
        toolbutton_paste.show()
        toolbutton_paste.set_stock_id(Gtk.STOCK_PASTE)
        toolbutton_paste.connect("clicked", self.do_paste)
        self.toolbar1.add(toolbutton_paste)

        separatortoolitem2 = Gtk.SeparatorToolItem()
        separatortoolitem2.show()
        self.toolbar1.add(separatortoolitem2)

        ## p, h1, h2 样式
        label1 = Gtk.Label("")
        label1.set_markup("<b>P</b>")
        button1 = Gtk.ToolButton()
        button1.set_icon_widget(label1)
        button1.set_label(_("Paragraph"))
        button1.set_tooltip_text(_("Paragraph"))
        button1.connect("clicked", self.do_formatblock_p)
        button1.show()
        self.toolbar1.add( button1)

        label1 = Gtk.Label("")
        label1.set_markup("<big><big><b>H1</b></big></big>")
        button1 = Gtk.ToolButton()
        button1.set_icon_widget(label1)
        button1.set_label(_("Heading 1"))
        button1.set_tooltip_text(_("Heading 1"))
        button1.connect("clicked", self.do_formatblock_h1)
        button1.show()
        self.toolbar1.add( button1)

        label1 = Gtk.Label("")
        label1.set_markup("<big><b>H2</b></big>")
        button1 = Gtk.ToolButton()
        button1.set_icon_widget(label1)
        button1.set_label(_("Heading 2"))
        button1.set_tooltip_text(_("Heading 2"))
        button1.connect("clicked", self.do_formatblock_h2)
        button1.show()
        self.toolbar1.add( button1)

        ## h3 样式

        label1 = Gtk.Label("")
        label1.set_markup("<b>H3</b>")
        button1 = Gtk.MenuToolButton()
        button1.set_icon_widget(label1)
        button1.set_label(_("Heading 3"))
        button1.set_tooltip_text(_("Heading 3"))
        button1.set_arrow_tooltip_markup(_("Style"))
        button1.connect("clicked", self.do_formatblock_h3)
        button1.show()
        self.toolbar1.add( button1)

        menu_style = Gtk.Menu()

        menuitem_heading_4 = Gtk.ImageMenuItem.new_with_mnemonic(_("Heading _4"))
        menuitem_heading_4.show()
        menuitem_heading_4.connect("activate", self.do_formatblock_h4)

        img = Gtk.Image.new_from_icon_name('stock_line-spacing-1.5', Gtk.IconSize.MENU)
        menuitem_heading_4.set_image(img)
        menu_style.append(menuitem_heading_4)

        menuitem_heading_5 = Gtk.ImageMenuItem.new_with_mnemonic(_("Heading _5"))
        menuitem_heading_5.show()
        menuitem_heading_5.connect("activate", self.do_formatblock_h5)

        img = Gtk.Image.new_from_icon_name('stock_list_enum-off', Gtk.IconSize.MENU)
        menuitem_heading_5.set_image(img)
        menu_style.append(menuitem_heading_5)

        menuitem_heading_6 = Gtk.ImageMenuItem.new_with_mnemonic(_("Heading _6"))
        menuitem_heading_6.show()
        menuitem_heading_6.connect("activate", self.do_formatblock_h6)

        img = Gtk.Image.new_from_icon_name('stock_list_enum-off', Gtk.IconSize.MENU)
        menuitem_heading_6.set_image(img)
        menu_style.append(menuitem_heading_6)

        menuitem_separator5 = Gtk.SeparatorMenuItem.new()
        menuitem_separator5.show()

        menu_style.append(menuitem_separator5)

        menuitem_bulleted_list = Gtk.ImageMenuItem.new_with_mnemonic(_("_Bulleted List"))
        menuitem_bulleted_list.show()
        menuitem_bulleted_list.connect("activate", self.do_insertunorderedlist)

        img = Gtk.Image.new_from_icon_name('stock_list_bullet', Gtk.IconSize.MENU)
        menuitem_bulleted_list.set_image(img)
        menu_style.append(menuitem_bulleted_list)

        menuitem_numbered_list = Gtk.ImageMenuItem.new_with_mnemonic(_("Numbered _List"))
        menuitem_numbered_list.show()
        menuitem_numbered_list.connect("activate", self.do_insertorderedlist)

        img = Gtk.Image.new_from_icon_name('stock_list_enum', Gtk.IconSize.MENU)
        menuitem_numbered_list.set_image(img)
        menu_style.append(menuitem_numbered_list)

        menuitem_separator6 = Gtk.SeparatorMenuItem.new()
        menuitem_separator6.show()

        menu_style.append(menuitem_separator6)

        div1 = Gtk.ImageMenuItem.new_with_mnemonic(_("Di_v"))
        div1.show()
        div1.connect("activate", self.do_formatblock_div)

        img = Gtk.Image.new_from_icon_name('stock_tools-hyphenation', Gtk.IconSize.MENU)
        div1.set_image(img)
        menu_style.append(div1)

        address1 = Gtk.ImageMenuItem.new_with_mnemonic(_("A_ddress"))
        address1.show()
        address1.connect("activate", self.do_formatblock_address)

        img = Gtk.Image.new_from_icon_name('stock_tools-hyphenation', Gtk.IconSize.MENU)
        address1.set_image(img)
        menu_style.append(address1)

        #menuitem_formatblock_code = Gtk.ImageMenuItem.new_with_mnemonic(_("_Code"))
        #menuitem_formatblock_code.show()
        #menuitem_formatblock_code.connect("activate", self.do_formatblock_code)
        #
        #img = Gtk.Image.new_from_icon_name('stock_text-monospaced', Gtk.IconSize.MENU)
        #menuitem_formatblock_code.set_image(img)
        #menu_style.append(menuitem_formatblock_code)

        menuitem_formatblock_blockquote = Gtk.ImageMenuItem.new_with_mnemonic(_("Block_quote"))
        menuitem_formatblock_blockquote.show()
        menuitem_formatblock_blockquote.connect("activate", self.do_formatblock_blockquote)

        img = Gtk.Image.new_from_icon_name('stock_list-insert-unnumbered', Gtk.IconSize.MENU)
        menuitem_formatblock_blockquote.set_image(img)
        menu_style.append(menuitem_formatblock_blockquote)

        menuitem_formatblock_pre = Gtk.ImageMenuItem.new_with_mnemonic(_("_Preformat"))
        menuitem_formatblock_pre.show()
        menuitem_formatblock_pre.connect("activate", self.do_formatblock_pre)

        img = Gtk.Image.new_from_icon_name('stock_text-quickedit', Gtk.IconSize.MENU)
        menuitem_formatblock_pre.set_image(img)
        menu_style.append(menuitem_formatblock_pre)

        button1.set_menu(menu_style)

        ########################

        ## 粗体按钮菜单
        menu_format = Gtk.Menu()
        menu_format.append(Gtk.TearoffMenuItem())

        menuitem_italic = Gtk.ImageMenuItem.new_from_stock("gtk-italic", self.accel_group)
        menuitem_italic.show()
        menuitem_italic.connect("activate", self.do_italic)

        menu_format.append(menuitem_italic)

        menuitem_underline = Gtk.ImageMenuItem.new_from_stock("gtk-underline", self.accel_group)
        menuitem_underline.show()
        menuitem_underline.connect("activate", self.do_underline)

        menu_format.append(menuitem_underline)

        menuitem_strikethrough = Gtk.ImageMenuItem.new_from_stock("gtk-strikethrough", self.accel_group)
        menuitem_strikethrough.show()
        menuitem_strikethrough.connect("activate", self.do_strikethrough)

        menu_format.append(menuitem_strikethrough)

        separatortoolitem4 = Gtk.SeparatorToolItem()
        separatortoolitem4.show()
        self.toolbar1.add(separatortoolitem4)

        toolbutton_bold = Gtk.MenuToolButton()
        toolbutton_bold.set_stock_id(Gtk.STOCK_BOLD)
        toolbutton_bold.set_label(_("Bold"))
        toolbutton_bold.set_tooltip_text(_("Bold"))
        toolbutton_bold.show()
        toolbutton_bold.set_stock_id(Gtk.STOCK_BOLD)
        toolbutton_bold.connect("clicked", self.on_bold)
        toolbutton_bold.set_menu(menu_format)
        self.toolbar1.add(toolbutton_bold)

        ## 高亮颜色
        toolbutton_hilitecolor = Gtk.MenuToolButton()
        toolbutton_hilitecolor.set_icon_name("stock_text_color_hilight")
        toolbutton_hilitecolor.set_label(_("Highlight"))
        toolbutton_hilitecolor.set_tooltip_text(_("Highlight"))
        toolbutton_hilitecolor.set_arrow_tooltip_markup(_("Select hilitecolor"))
        toolbutton_hilitecolor.set_menu(Gtk.Menu())
        toolbutton_hilitecolor.show()
        toolbutton_hilitecolor.connect("clicked", self.do_color_hilitecolor)
        ### 处理 ToolButton 箭头
        on_color_select_hilitecolor = self.on_color_select_hilitecolor
        ib, mb = toolbutton_hilitecolor.get_children()[0].get_children()
        mb.connect("clicked", self.on_color_select_hilitecolor)
        self.toolbar1.add(toolbutton_hilitecolor)

        ## 清除格式
        button1 = Gtk.ToolButton()
        button1.set_icon_name("gtk-clear")
        button1.set_label(_("Clear format"))
        button1.set_tooltip_text(_("Clear format"))
        button1.show()
        button1.connect("clicked", self.do_removeformat)
        self.toolbar1.add(button1)

        ### 字体菜单按钮
        #toolbutton_font = Gtk.MenuToolButton("gtk-select-font")
        #toolbutton_font.set_label(_("Font"))
        #toolbutton_font.set_tooltip_text(_("Font"))
        #toolbutton_font.show()
        #toolbutton_font.set_menu(self.fontname_menu)

        ### 处理 Gtk.MenuToolButton 按钮
        #m =  toolbutton_font
        #ib, mb = m.child.children()
        #mb.remove(mb.child)
        #ib.child.reparent(mb)
        #m.child.remove(ib)

        #self.toolbar1.add(toolbutton_font)

        ## 

        ###############

        self.toolbar = Gtk.HandleBox()

        self.toolbar.add(self.toolbar1)

        self.toolbar.show_all()

        self.vbox1.pack_start(self.toolbar, False, False, 0)
        

        ## 编辑区
        #self.editport = Gtk.Viewport()
        #self.editport.show()
        #self.editport.set_shadow_type(Gtk.SHADOW_NONE)
        #
        #self.vbox1.pack_start(self.editport)

        ##
        self.notebox = Gtk.Notebook()
        self.notebox.set_tab_pos(2) # 0, 1, 2, 3 -> left, top, right, bottom
        self.notebox.set_border_width(0)
        self.notebox.popup_enable()
        #self.notebox.set_property('homogeneous', 0)
        self.notebox.props.can_focus = 0
        self.notebox.set_scrollable(True)
        self.notebox.connect("switch-page", self.on_mdi_switch_page)
        self.notebox.connect("button-press-event", self.on_mdi_menu) # 用 "button-release-event" 会不能中止事件向上传递
        self.notebox.show()
        editbox = self.new_edit(self.editfile)
        editbox.show()
        self.notebox_insert_page(editbox)
        self.notebox.set_tab_reorderable(editbox, True)
        self.notebox.show_all()
        self.vbox1.pack_start(self.notebox, True, True, 0)

        ## 搜索栏

        self.findbar = Gtk.HandleBox()
        self.findbar.set_shadow_type(Gtk.ShadowType.OUT)

        self.findbox = Gtk.HBox(False, 0)
        self.findbox.show()

        button_hidefindbar = Gtk.Button()
        button_hidefindbar.set_tooltip_text(_("Close Findbar"))
        button_hidefindbar.show()
        button_hidefindbar.set_relief(Gtk.ReliefStyle.NONE)
        button_hidefindbar.connect("clicked", self.hide_findbar)

        image113 = Gtk.Image()
        image113.set_from_stock(Gtk.STOCK_CLOSE, 1)
        image113.show()
        button_hidefindbar.add(image113)

        self.findbox.pack_start(button_hidefindbar, False, False, 0)

        self.entry_searchtext = Gtk.Entry()
        self.entry_searchtext.show()
        self.entry_searchtext.connect("changed", self.do_highlight_text_matches)
        #self.entry_searchtext.set_property("primary-icon-stock", "gtk-go-back")
        #self.entry_searchtext.set_property("primary-icon-tooltip-text", _("Find Previous"))
        #self.entry_searchtext.set_property("secondary-icon-stock", "gtk-find")
        #self.entry_searchtext.set_property("secondary-icon-tooltip-text", _("Find Next"))
        self.entry_searchtext.set_property("primary-icon-stock", "gtk-find")
        self.entry_searchtext.set_property("primary-icon-tooltip-text", _("Find Next"))
        self.entry_searchtext.connect("icon-release", self.do_find_text)
        self.entry_searchtext.set_tooltip_text(_("Search text"))
        #self.entry_searchtext.set_flags(Gtk.CAN_DEFAULT)
        #self.entry_searchtext.grab_focus()
        self.findbox.pack_start(self.entry_searchtext, True, True, 0)

        button1 = Gtk.Button()
        button1.set_tooltip_text(_("Find Previous"))
        button1.show()
        button1.set_relief(Gtk.ReliefStyle.NONE)
        button1.connect("clicked", self.do_find_text_backward)

        image1 = Gtk.Image()
        image1.set_from_stock(Gtk.STOCK_GO_BACK, 4)
        image1.show()
        button1.add(image1)

        self.findbox.pack_start(button1, False, False, 0)

        button_search_text = Gtk.Button(_("Find"))
        img = Gtk.Image()
        img.set_from_stock("gtk-find", 4)
        img.show()
        button_search_text.set_image(img)
        button_search_text.set_tooltip_text(_("Find Next"))
        button_search_text.show()
        button_search_text.set_relief(Gtk.ReliefStyle.NONE)
        button_search_text.connect("clicked", self.do_find_text)
        button_search_text.add_accelerator("clicked", self.accel_group, Gdk.keyval_from_name("F3"), 0, Gtk.AccelFlags.VISIBLE)

        self.findbox.pack_start(button_search_text, False, False, 0)

        self.findbox.pack_start(Gtk.VSeparator(), False, False, 3)

        self.entry_replace_text = Gtk.Entry()
        self.entry_replace_text.show()
        self.entry_replace_text.set_tooltip_text(_("Replace text"))
        self.entry_replace_text.set_property("primary-icon-stock", "gtk-find-and-replace")
        self.entry_replace_text.set_property("primary-icon-tooltip-text", _("Replace"))
        self.findbox.pack_start(self.entry_replace_text, True, True, 0)

        button_replace_text = Gtk.Button()
        button_replace_text.set_tooltip_text(_("Replace"))
        button_replace_text.show()
        button_replace_text.set_relief(Gtk.ReliefStyle.NONE)
        button_replace_text.connect("clicked", self.do_replace_text)

        alignment1 = Gtk.Alignment()
        alignment1.show()

        hbox2 = Gtk.HBox(False, 0)
        hbox2.show()
        hbox2.set_spacing(2)

        image136 = Gtk.Image()
        image136.set_from_stock(Gtk.STOCK_FIND_AND_REPLACE, 4)
        image136.show()
        hbox2.pack_start(image136, False, False, 0)

        label1 = Gtk.Label(_("Replace"))
        label1.show()
        hbox2.pack_start(label1, False, False, 0)

        alignment1.add(hbox2)

        button_replace_text.add(alignment1)

        self.findbox.pack_start(button_replace_text, False, False, 0)

        #self.findbox.pack_start(Gtk.VSeparator(), False, False, 0)

        button2 = Gtk.Button()
        button2.set_tooltip_text(_("Replace All"))
        button2.set_label(_("ReplaceAll"))
        button2.show()
        button2.set_relief(Gtk.ReliefStyle.NONE)

        img = Gtk.Image()
        img.set_from_stock("gtk-convert", 4)
        img.show()
        button2.set_image(img)
        button2.connect("clicked", self.do_replace_text_all)

        self.findbox.pack_start(button2, False, False, 0)

        self.findbar.add(self.findbox)

        self.vbox1.pack_start(self.findbar, False, False, 0)

        #self.edit.contextmenu.append(menuitem_style)

        #self.edit.connect("popup-menu", self._populate_popup)

        GObject.timeout_add(1000 * 60, self.do_autosave)


        if create:
            self.window.add(self.vbox1)
            pass
        pass

    def mdi_get_tab_menu(self, editbox=None, windowslist=0):
        menu = Gtk.Menu()

        menuitem_new = Gtk.ImageMenuItem.new_from_stock("gtk-new", self.accel_group)
        menuitem_new.show()
        menuitem_new.connect("activate", self.on_new)
        menu.append(menuitem_new)

        menuitem_close = Gtk.ImageMenuItem.new_from_stock("gtk-close", self.accel_group)
        menuitem_close.show()
        menuitem_close.connect("activate", self.close_tab, editbox)
        menu.append(menuitem_close)

        menu.append(Gtk.SeparatorMenuItem.new())

        notebox = self.notebox
        for box in notebox.get_children():
            menuitem = Gtk.ImageMenuItem(box.edit.title)
            menuitem.set_image(Gtk.Image.new_from_stock("gtk-dnd", Gtk.IconSize.MENU))
            menuitem.connect("activate", self.notebox_set_current, box)
            menuitem.show()
            menu.append(menuitem)
            pass
        if windowslist and config.single_instance_mode:
            pass
        menu.show_all()
        return menu

    def on_accel_connect(self, accel_group, acceleratable, keyval, modifier):
        ## 按 Alt-1, Alt-2... 切换标签页
        ## Gdk.keyval_from_name('1') 为 49
        num = keyval - 49
        self.notebox.set_current_page(num)
        return

    def on_mdi_menu(self, widget, event, editbox=None, *args):
        #-print self, widget, event, editbox, args
        if event.button == 3:
            return False
            #menu = self.menu_file
            def popup_menu():
                menu = self.mdi_get_tab_menu(editbox)
                menu.popup(None, None, None, None, 0, 0)
            GLib.idle_add(popup_menu)
            return False
        elif (
                ( event.type.value_name == "GDK_BUTTON_PRESS" and event.button == 2 ) or
                ( event.type.value_name == "GDK_2BUTTON_PRESS" and event.button == 1 ) 
              ):
            # 标签上 中键/双击 关闭，空白处 中键/双击 新建
            if editbox:
                self.close_tab(editbox)
                pass
            else:
                self.on_new()
                pass
            return True
        #box = self.notebox
        #label = box.get_tab_label( box.get_nth_page( box.get_current_page() ) )
        return False

    def on_mdi_switch_page(self, notebook, page, page_num, *user_param):
        #-print 'on_mdi_switch_page:', notebook, page, page_num
        ## show/hide tabbar
        self.notebox.props.can_focus = 0
        if self.notebox.get_n_pages() > 1:
            self.notebox.set_show_tabs(True)
            pass
        else:
            self.notebox.set_show_tabs(False)
            pass
        ## edit, linkview
        editbox = self.notebox.get_nth_page(page_num)
        self.editbox = editbox
        self.edit = editbox.edit
        self.linkview = editbox.linkview
        ##
        #self.edit.set_flags(Gtk.CAN_DEFAULT)
        #if self.edit.editfile: self.window.set_title(os.path.basename(self.editfile) + ' - ' + Title)
        self.window.set_title(self.edit.title + ' - ' + Title)
        ##
        try:
            self.do_highlight_text_matches()
        except:
            pass
        pass

    def on_over_link(self, edit, alt, href): 
        #-print edit, alt, href
        href = href or ""
        uri = edit.get_main_frame().get_uri()
        url = urllib2.unquote(uri)
        if "#" in href and uri.split('#', 1)[0] == href.split('#', 1)[0]:
            href = "#" + href.split('#', 1)[1]
        self.window.set_tooltip_text(href)
        pass

    def notebox_set_current(self, widget, editbox=None):
        editbox = editbox or widget # 考虑非事件的调用
        num = self.notebox.page_num(editbox)
        self.notebox.set_current_page(num)
        self.window.present()
        return

    def notebox_set_label_text(self, editbox, text):
        #self.notebox.set_tab_label_text(editbox, text)
        self.notebox.set_menu_label_text(editbox, text)
        label = Gtk.Label(text)
        label.show()
        box = Gtk.EventBox()
        box.set_visible_window(0)
        box.connect("button-press-event", self.on_mdi_menu, editbox)
        box.add(label)
        self.notebox.set_tab_label(editbox, box)
        pass

    def notebox_insert_page(self, editbox):
        cn = self.notebox.get_current_page()
        n = self.notebox.insert_page(editbox, None, cn+1)
        self.notebox_set_label_text(editbox, editbox.edit.title)
        self.notebox.set_tab_reorderable(editbox, True)
        #self.notebox.show_all()
        self.notebox.set_current_page(n)
        ##
        #self.notebox.get_tab_label(editbox).connect("button-press-event", self.on_mdi_menu)
        return

    def new_edit(self, editfile):
        global new_num
        editbox = Gtk.VBox()
        editbox.show()

        separator = Gtk.HSeparator()
        separator.show()
        editbox.pack_start(separator, False, False, 0)

        hpaned = Gtk.HPaned()
        hpaned.set_border_width(0)
        hpaned.set_position(170)
        hpaned.show()

        editbox.pack_start(hpaned, True, True, 0)
        
        ## 导航栏
        vbox1 = Gtk.VBox()
        label1 = Gtk.Label(_("Navigation Pane"))
        label1.set_alignment(0, 0)
        vbox1.pack_start(label1, False, False, 0)
        scrolledwindow1 = Gtk.ScrolledWindow()
        scrolledwindow1.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolledwindow1.show()
        scrolledwindow1.set_shadow_type(Gtk.ShadowType.IN)

        import webkitlinkview
        linkview = webkitlinkview.LinkTextView()
        linkview.connect('url-clicked', self.on_title_clicked)
        linkview.connect('populate-popup', self._linkview_populate_popup)
        linkview.show()
        scrolledwindow1.add(linkview)

        editbox.linkview = linkview

        vbox1.pack_start(scrolledwindow1, True, True, 0)
        vbox1.show_all()

        hpaned.pack1(vbox1, False, True)

        editbox.navigation_pane = vbox1

        ## 编辑区
        import webkitedit
        scrolledwindow2 = Gtk.ScrolledWindow()
        scrolledwindow2.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolledwindow2.show()
        scrolledwindow2.set_shadow_type(Gtk.ShadowType.IN)

        edit = webkitedit.WebKitEdit(editfile)
        edit.show()
        edit.connect("load-finished", self.on_load_finished)
        edit.connect("hovering-over-link", self.on_over_link)
        edit.props.can_focus = 1
        edit.props.can_default = 1
        self.window.present()
        scrolledwindow2.add(edit)

        editbox.edit = edit

        hpaned.pack2(scrolledwindow2, True, True)

        if editfile:
            edit.lastDir = os.path.dirname(editfile)
            edit.title = os.path.basename(editfile)
            self.add_recent(editfile)
            pass
        else:
            if config.mdi_mode or config.single_instance_mode:
                edit.title = _("[New Document] %s") % new_num
                new_num += 1
                pass
            else:
                edit.title = _("[New Document]")
                pass

        editbox.connect("button-press-event", lambda *i: True) ## 中止鼠标按钮事件向上传递

        GObject.idle_add(proc_webkit_color, edit, linkview)

        return editbox


    def _populate_popup(self, view, menu):
        pass

    def zoom(self, level):
        self.edit.set_zoom_level(level)
        pass

    def zoom_100(self, *args):
        self.edit.set_zoom_level(1.0)
        pass

    def zoom_in(self, *args):
        self.edit.zoom_in()
        pass

    def zoom_out(self, *args):
        self.edit.zoom_out()
        pass

    def _linkview_populate_popup(self, view, menu):
        # 检查是否有链接相关菜单项
        href = ""
        if menu_find_with_stock(menu, 'gtk-open') > -1:
            href = view.get_main_frame().get_title()
            pass
        ## 取消原先的菜单
        #menu.destroy()
        #menu = Gtk.Menu()
        for i in menu.get_children():
            menu.remove(i)
            pass

        ## 跳转到
        if href:
            menuitem_jump_to = Gtk.ImageMenuItem.new_from_stock("gtk-jump-to", self.accel_group)
            menuitem_jump_to.show()
            menuitem_jump_to.connect("activate", self.edit.go_anchor, href)
            menu.append(menuitem_jump_to)

            menuitem_select = Gtk.ImageMenuItem.new_with_mnemonic(_("_Select this"))
            menuitem_select.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_SELECT_ALL, Gtk.IconSize.MENU))
            menuitem_select.show()
            menuitem_select.set_tooltip_markup(_("You can also <b>doubleclick</ b> to select the section of text"))
            menuitem_select.connect("activate", self.edit.select_section, href)

            menu.append(menuitem_select)

            menu.append(Gtk.SeparatorMenuItem.new())
            pass

        ## 更新目录
        menuitem_update_contents = Gtk.ImageMenuItem.new_with_mnemonic(_("Update _Contents"))
        menuitem_update_contents.show()
        menuitem_update_contents.connect("activate", self.view_update_contents)

        img = Gtk.Image.new_from_stock(Gtk.STOCK_INDEX, Gtk.IconSize.MENU)
        menuitem_update_contents.set_image(img)
        menu.append(menuitem_update_contents)

        menuitem_toggle_numbered_title = Gtk.ImageMenuItem.new_with_mnemonic(_("Toggle _Numbered Title"))
        menuitem_toggle_numbered_title.show()
        menuitem_toggle_numbered_title.connect("activate", self.view_toggle_autonumber)

        img = Gtk.Image.new_from_stock(Gtk.STOCK_SORT_DESCENDING, Gtk.IconSize.MENU)
        menuitem_toggle_numbered_title.set_image(img)
        menu.append(menuitem_toggle_numbered_title)

        ## 缩放菜单
        linkview = self.linkview
        menuitem_separator10 = Gtk.SeparatorMenuItem.new()
        menuitem_separator10.show()
        menu.append(menuitem_separator10)

        menuitem_zoom_in = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_ZOOM_IN, self.accel_group)
        menuitem_zoom_in.connect("activate", lambda *i: linkview.zoom_in())
        menuitem_zoom_in.show()
        menu.append(menuitem_zoom_in)

        menuitem_zoom_out = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_ZOOM_OUT, self.accel_group)
        menuitem_zoom_out.connect("activate", lambda *i: linkview.zoom_out())
        menuitem_zoom_out.show()
        menu.append(menuitem_zoom_out)

        menuitem_zoom_100 = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_ZOOM_100, self.accel_group)
        menuitem_zoom_100.connect("activate", lambda *i: linkview.set_zoom_level(1.0))
        menuitem_zoom_100.show()
        menu.append(menuitem_zoom_100)

        menu.show_all()
        pass

    def on_title_clicked(self, widget, href, type):
        if href.startswith('+'):
            self.edit.select_section(href.split('#', 1)[1])
            return True
        href = href.split('#', 1)[1]
        self.edit.go_anchor(href)
        pass

    def on_load_finished(self, edit, *args):
        #-print 'on_load_finished:'
        self.view_update_contents()
        if edit._html == "":
            edit.set_saved()
            pass
        pass

    last_autosave_time = 0

    def do_autosave(self, *args):
        if not float(config.autosaveinterval) \
           or time.time() - self.last_autosave_time < (float(config.autosaveinterval) - 1 ) * 1000 * 60:
            return True
        for editbox in self.notebox.get_children():
            edit = editbox.edit
            filename = edit.editfile
            if filename and not edit.is_saved():
                if filename and not '.' in os.path.basename(filename):
                    filename = filename + '.html'
                    pass
                html = self.edit.get_html()
                try:
                    filedir = os.path.dirname(filename)
                    if not os.path.exists(filedir): os.makedirs(filedir)
                    file(filename, 'w').write(html)
                    edit.set_saved()
                    pass
                except:
                    pass
                pass
            pass
        self.last_autosave_time = time.time()
        return True

    def close_tab(self, widget=None, editbox=None, *args):
        notebox = self.notebox
        if widget and 'edit' in widget.__dict__:
            editbox = widget
            pass
        if not editbox:
            n = notebox.get_current_page()
            editbox = notebox.get_nth_page(n)
            pass
        edit = editbox.edit
        linkview = editbox.linkview
        self.window.show()
        if not edit.is_saved():
            ## r: 1, -1, 0 => yes, no, cancel
            r = gtkdialogs.savechanges(_("%s Save Changes?") % edit.title) 
            if r == 1:
                filename = self.on_save()
                if not filename: 
                    return True
                pass
            elif r == 0:
                return True
            pass
        # 关闭标签
        notebox.remove(editbox)
        edit.destroy()
        linkview.destroy()
        editbox.destroy()
        # 无标签时关闭窗口
        if self.notebox.get_n_pages():
            return True
        Windows.remove(self)
        Gdk.threads_leave()
        self.window.destroy()
        if not Windows:
            Gtk.main_quit() 
        return

    def on_close(self, *args):
        '''关闭窗口
        '''
        #-print 'on_close:', self
        #@TODO: 退出时未保存提示
        for i in range(self.notebox.get_n_pages()):
            self.close_tab()
            pass
        if self.notebox.get_n_pages():
            return True
        try: 
            Windows.remove(self)
            pass
        except: 
            pass
        Gdk.threads_leave()
        self.window.destroy()
        if not Windows:
            Gtk.main_quit() 
        pass

    def on_quit(self, *args):
        #-print 'on_quit:'
        windows = reversed(Windows)
        for window in windows:
            window.on_close()
            pass
        Gtk.main_quit()
        pass

    def on_new(self, *args):
        #-print 'on_new:'
        return self.open("")

    def on_new_window(self, *args):
        '''打开新窗口
        '''
        if config.single_instance_mode:
            return MainWindow()
        else:
            return os.spawnvp(os.P_NOWAIT, sys.argv[0], ['gwrite'])
        pass
            

    def add_recent(self, filename):
        uri = 'file://' + filename
        # @TODO add_recent
        #self.recent.add_full(uri, {'mime_type':'text/html', 'app_name':'gwrite', 'app_exec':'gwrite', 'group':'gwrite'})

    def open(self, filename=""):
        self.window.present()
        # mdi mode
        if config.mdi_mode:
            if filename:
                for editbox in self.notebox.get_children():
                    if editbox.edit.editfile == filename:
                        self.notebox.set_current_page(self.notebox.page_num(editbox))
                        return
                    pass
                pass
            editbox = self.new_edit(filename)
            self.notebox_insert_page(editbox)
            return
        # 如果当前空文档，则在当前窗口打开
        if filename and self.edit.editfile == '' and self.edit.is_saved():
            self.window.set_title(os.path.basename(filename) + ' - ' + Title)
            self.edit.lastDir = os.path.dirname(filename)
            self.edit.editfile = filename
            self.edit._html = ""
            if filename and os.access(filename, os.R_OK):
                self.edit.open(filename)
                self.add_recent(filename)
                pass
            pass
        elif config.single_instance_mode:
            MainWindow(editfile = filename)
            pass
        else:
            if filename:
                os.spawnvp(os.P_NOWAIT, sys.argv[0], ['gwrite', filename])
                pass
            else:
                os.spawnvp(os.P_NOWAIT, sys.argv[0], ['gwrite'])
                pass
            pass
        pass
    
    def on_select_recent(self, menu):
        filename = menu. get_current_item().get_uri_display()
        #-print 'on_select_recent:', filename
        self.open(filename)
        pass

    def on_open(self, *args):
        #-print 'on_open:'
        filename = gtkdialogs.open(title=_('Open'),
                name_mimes=[
                    [_("Html Document"), "text/html"],
                    [_("MS Doc Document"), "application/msword"],
                    ])
        if filename and os.access(filename, os.R_OK):
            self.open(filename)
            pass
        Gdk.threads_leave()
        pass

    def on_save(self, *args):
        #-print 'on_save:'
        html = self.edit.get_html()
        if self.edit.editfile:
            filename = self.edit.editfile
        else:
            #current_name = _('新建文档')
            #current_name = ''
            current_name = get_doctitle(html)
            filename = gtkdialogs.save(title=_('Save'), 
                    name_mimes=[[_("Html Document"), "text/html"]],
                    current_name=current_name,)
            if filename and not '.' in os.path.basename(filename):
                filename = filename + '.html'
        if filename:
            try:
                file(filename, 'w').write(html)
                pass
            except:
                gtkdialogs.warning(_("Unable to write to file."))
                return False
            self.edit.lastDir = os.path.dirname(filename)
            if not self.edit.editfile: self.add_recent(filename) #添加到最近文件
            self.editfile = filename
            self.edit.set_saved()
            self.window.set_title(os.path.basename(filename) + ' - ' + Title) 
            ## 更新标签名
            self.edit.editfile = filename
            self.edit.title = os.path.basename(filename)
            self.notebox_set_label_text(self.editbox, self.edit.title)
            pass
        Gdk.threads_leave()
        return filename

    def on_save_as(self, *args):
        #-print 'on_save_as:'
        html = self.edit.get_html()
        #current_name = _('新建文档')
        #current_name = ''
        current_name = get_doctitle(html)
        filename = gtkdialogs.save(title=_('Save As'), 
                name_mimes=[[_("Html Document"), "text/html"]],
                current_name=current_name, folder=self.edit.lastDir,)
        if filename and not '.' in os.path.basename(filename):
            filename = filename + '.html'
        if filename:
            try:
                file(filename, 'w').write(html)
                pass
            except:
                gtkdialogs.warning(_("Unable to write to file."))
                return False
            self.add_recent(filename) #添加到最近文件
            self.edit.lastDir = os.path.dirname(filename)
            pass
        Gdk.threads_leave()
        pass

    def on_word_counts(self, *args):
        document = self.edit.get_text().decode('utf8')
        selection = self.edit.get_selection()
        #-print text
        #-print selection
        # 行: '', 文档, 选中范围
        # 列: 字数及英文单词数, 字符数(含空格), 字符数(不含空格), 段落数, 行数, 英文单词, 中文字
        text = document
        words_cn = len( re.findall(u'[\u4e00-\uffff]', text) )
        words_en = len( re.findall(u'\\w+', text) )
        words = words_cn + words_en
        characters_with_spaces = len(text)
        characters_no_spaces = len(''.join(text.split()))
        _lines = text.splitlines()
        lines = len(_lines)
        paragraphs = len([i for i in _lines if i])
        ##
        text = selection
        s_words_cn = len( re.findall(u'[\u4e00-\uffff]', text) )
        s_words_en = len( re.findall(u'\\w+', text) )
        s_words = s_words_cn + s_words_en
        s_characters_with_spaces = len(text)
        s_characters_no_spaces = len(''.join(text.split()))
        _s_lines = text.splitlines()
        s_lines = len(_s_lines)
        s_paragraphs = len([i for i in _s_lines if i])

        info = (
            ("", _("Document"), selection and _("Selection")),
            (_("Words: "), words, selection and s_words, ),
            (_("Characters (with spaces): "), characters_with_spaces, selection and s_characters_with_spaces),
            (_("Characters (no spaces): "), characters_no_spaces, selection and s_characters_no_spaces),
            (_("Paragraphs: "), paragraphs, selection and s_paragraphs),
            (_("Lines: "), lines, selection and s_lines),
            (_("English words: "), words_en, selection and s_words_en),
            (_("Chinese characters: "), words_cn, selection and s_words_cn),
        )
        #-print info
        gtkdialogs.infotablebox(_("Word Counts"), "<b>%s</b>" % self.edit.title, info)
        return

    def on_print(self, *args):
        #-print 'on_print:'
        self.edit.do_print()
        pass

    def do_undo(self, *args):
        #-print 'do_undo:'
        self.window.present()
        self.edit.do_undo()
        pass

    def do_redo(self, *args):
        #-print 'do_redo:'
        self.window.present()
        self.edit.do_redo()
        pass

    def do_cut(self, *args):
        #-print 'do_cut:'
        self.window.present()
        self.edit.do_cut()
        pass

    def do_copy(self, *args):
        #-print 'do_copy:'
        self.window.present()
        self.edit.do_copy()
        pass

    def do_paste(self, *args):
        #-print 'do_paste:'
        self.window.present()
        self.edit.do_paste()
        pass

    def do_paste_unformatted(self, *args):
        #-print 'do_paste_unformatted:'
        self.edit.do_paste_unformatted()
        return

    def do_delete(self, *args):
        #-print 'do_delete:'
        self.window.present()
        self.edit.do_delete()
        pass

    def do_selectall(self, *args):
        #-print 'do_selectall:'
        self.window.present()
        self.edit.do_selectall()
        pass

    def show_findbar(self, *args):
        #-print 'show_findbar:'
        self.findbar.show_all()
        self.entry_searchtext.grab_focus()
        self.do_find_text(self.entry_searchtext)
        pass

    def view_update_contents(self, *args):
        #-print 'view_update_contents:'
        self.window.present()
        self.linkview.updatehtmllinks( self.edit.do_view_update_contents() )
        pass

    def view_toggle_autonumber(self, *args):
        #-print 'view_toggle_autonumber:'
        self.window.present()
        self.linkview.updatehtmllinks( self.edit.do_view_toggle_autonumber() )
        pass

    def view_sourceview(self, *args):
        #-print 'view_sourceview:'
        self.window.present()
        ## 源码模式隐藏导航栏
        #@NOTE 执行顺序和 idle_add 是为了避免闪烁
        if not self.edit.get_view_source_mode():
            ## 先转到源码模式，再 idle_add 隐藏导航条，以便显示变化平滑
            self.edit.toggle_html_view()
            GObject.idle_add( self.editbox.navigation_pane.hide )
            pass
        else:
            ## 先显示导航条，再 idle_add 转为所见所得模式，以便显示变化平滑
            self.editbox.navigation_pane.show_all()
            GObject.idle_add( self.edit.toggle_html_view )
            pass
        #self.edit.do_bodyhtml_view()
        pass

    def do_update_images(self, *args):
        #-print 'do_update_images:'
        self.window.present()
        self.edit.do_image_base64()
        pass

    def do_insertimage(self, *args):
        #-print 'do_insertimage:'
        src = gtkdialogs.open(title=_('InsertImage'), name_mimes=[[_("Image Files"), "image/*"]])
        if src:
            self.edit.do_insertimage(src)
        pass

    def do_createlink(self, *args):
        #-print 'do_createlink:'
        ##print self.edit.get_link_message()
        link = gtkdialogs.inputbox(title=_('Create Link'), label=_('URL:'), text="")
        if link and link != "http://":
            self.edit.do_createlink(link)
        pass

    def do_inserthorizontalrule(self, *args):
        #-print 'do_inserthorizontalrule:'
        self.window.present()
        self.edit.do_inserthorizontalrule()
        pass

    def do_insert_table(self, *args):
        #-print 'do_insert_table:'
        cow,row = gtkdialogs.spinbox2(title=_('Insert Table'),label1=_('Rows:'),value1=3, label2=_('Cows:'),value2=3)
        self.edit.do_insert_table(cow, row)
        pass

    def do_insert_html(self, *args):
        #-print 'do_insert_html:'
        html = gtkdialogs.textbox(title=_('Insert Html'), text='', lang='html')
        if html:
            self.edit.do_insert_html(html)
        pass

    def do_insert_latex_math_equation(self, *args):
        '''Insert Latex math equation
        '''
        latex = gtklatex.latex_dlg()
        if latex:
            img = gtklatex.tex2html(latex)
            self.edit.do_insert_html(img)
            pass
        pass

    def do_insert_contents(self, *args):
        #-print 'do_insert_contents:'
        self.window.present()
        self.edit.do_insert_contents()
        pass

    def do_formatblock_p(self, *args):
        #-print 'do_formatblock_p:'
        self.window.present()
        self.linkview.updatehtmllinks( self.edit.do_formatblock_p() )
        pass

    def do_formatblock_h1(self, *args):
        #-print 'do_formatblock_h1:'
        self.window.present()
        self.linkview.updatehtmllinks( self.edit.do_formatblock_h1() )
        pass

    def do_formatblock_h2(self, *args):
        #-print 'do_formatblock_h2:'
        self.window.present()
        self.linkview.updatehtmllinks( self.edit.do_formatblock_h2() )
        pass

    def do_formatblock_h3(self, *args):
        #-print 'do_formatblock_h3:'
        self.window.present()
        self.linkview.updatehtmllinks( self.edit.do_formatblock_h3() )
        pass

    def do_formatblock_h4(self, *args):
        #-print 'do_formatblock_h4:'
        self.window.present()
        self.linkview.updatehtmllinks( self.edit.do_formatblock_h4() )
        pass

    def do_formatblock_h5(self, *args):
        #-print 'do_formatblock_h5:'
        self.window.present()
        self.linkview.updatehtmllinks( self.edit.do_formatblock_h5() )
        pass

    def do_formatblock_h6(self, *args):
        #-print 'do_formatblock_h6:'
        self.window.present()
        self.linkview.updatehtmllinks( self.edit.do_formatblock_h6() )
        pass

    def do_insertunorderedlist(self, *args):
        #-print 'do_insertunorderedlist:'
        self.window.present()
        self.edit.do_insertunorderedlist()
        pass

    def do_insertorderedlist(self, *args):
        #-print 'do_insertorderedlist:'
        self.window.present()
        self.edit.do_insertorderedlist()
        pass

    def do_formatblock_div(self, *args):
        #-print 'do_formatblock_address:'
        self.window.present()
        self.edit.do_formatblock_div()
        pass

    def do_formatblock_address(self, *args):
        #-print 'do_formatblock_address:'
        self.window.present()
        self.edit.do_formatblock_address()
        pass

    def do_formatblock_code(self, *args):
        #-print 'do_formatblock_code:'
        self.window.present()
        self.edit.do_formatblock_code()
        pass

    def do_formatblock_blockquote(self, *args):
        #-print 'do_formatblock_blockquote:'
        self.window.present()
        self.edit.do_formatblock_blockquote()
        pass

    def do_formatblock_pre(self, *args):
        #-print 'do_formatblock_pre:'
        self.window.present()
        self.edit.do_formatblock_pre()
        pass

    def on_bold(self, *args):
        #-print 'on_bold:'
        self.window.present()
        self.edit.do_bold()
        pass

    def do_underline(self, *args):
        #-print 'do_underline:'
        self.window.present()
        self.edit.do_underline()
        pass

    def do_italic(self, *args):
        #-print 'do_italic:'
        self.window.present()
        self.edit.do_italic()
        pass

    def do_strikethrough(self, *args):
        #-print 'do_strikethrough:'
        self.window.present()
        self.edit.do_strikethrough()
        pass

    def do_font_fontname(self, widget, fontname):
        #-print 'do_font_fontname:', fontname
        self.window.present()
        self.edit.do_font_fontname(fontname)
        pass

    def do_fontsize_1(self, *args):
        #-print 'do_fontsize_1:'
        self.window.present()
        self.edit.do_fontsize_11()
        pass

    def do_fontsize_2(self, *args):
        #-print 'do_fontsize_2:'
        self.window.present()
        self.edit.do_fontsize_2()
        pass

    def do_fontsize_3(self, *args):
        #-print 'do_fontsize_3:'
        self.window.present()
        self.edit.do_fontsize_3()
        pass

    def do_fontsize_4(self, *args):
        #-print 'do_fontsize_4:'
        self.window.present()
        self.edit.do_fontsize_4()
        pass

    def do_fontsize_5(self, *args):
        #-print 'do_fontsize_5:'
        self.window.present()
        self.edit.do_fontsize_5()
        pass

    def do_fontsize_6(self, *args):
        #-print 'do_fontsize_6:'
        self.window.present()
        self.edit.do_fontsize_6()
        pass

    def do_fontsize_7(self, *args):
        #-print 'do_fontsize_7:'
        self.window.present()
        self.edit.do_fontsize_7()
        pass

    def do_color_forecolor(self, *args):
        #-print 'on_color_forecolor:'
        if "forecolor" in self.__dict__:
            self.edit.grab_focus()
            self.edit.do_color_forecolor(self.forecolor)
            pass
        else:
            self.on_color_select_forecolor()
            pass
        pass

    def on_color_select_forecolor(self, *args):
        #-print 'on_color_select_forecolor:'
        color = gtkdialogs.colorbox()
        if color:
            self.forecolor = color
            self.edit.do_color_forecolor (color)
            pass
        pass

    def do_color_hilitecolor(self, *args):
        #-print 'do_color_hilitecolor:'
        if "hilitecolor" in self.__dict__:
            self.edit.grab_focus()
            self.edit.do_color_hilitecolor(self.hilitecolor)
            pass
        else:
            self.on_color_select_hilitecolor()
            pass
        pass

    def on_color_select_hilitecolor(self, *args):
        #-print 'on_color_select_hilitecolor:', args
        # 处理 Gtk.MenuToolButton 箭头重复事件
        if self.__dict__.get('_on_color_select_hilitecolor'): 
            return True
        self._on_color_select_hilitecolor = 1
        color = gtkdialogs.colorbox()
        self._on_color_select_hilitecolor = 0
        if color:
            self.hilitecolor = color
            self.edit.do_color_hilitecolor(color)
        return False

    def do_removeformat(self, *args):
        #-print 'do_removeformat:'
        self.window.present()
        self.edit.do_removeformat()
        pass

    def do_justifyleft(self, *args):
        #-print 'do_justifyleft:'
        self.window.present()
        self.edit.do_justifyleft()
        pass

    def do_justifycenter(self, *args):
        #-print 'do_justifycenter:'
        self.window.present()
        self.edit.do_justifycenter()
        pass

    def do_justifyfull(self, *args):
        #-print 'do_justify:'
        self.window.present()
        self.edit.do_justifyfull()
        pass

    def do_justifyright(self, *args):
        #-print 'do_justifyright:'
        self.window.present()
        self.edit.do_justifyright()
        pass

    def do_indent(self, *args):
        #-print 'do_indent:'
        self.window.present()
        self.edit.do_indent()
        pass

    def do_outdent(self, *args):
        #-print 'do_outdent:'
        self.edit.do_outdent()
        pass

    def do_subscript(self, *args):
        #-print 'do_subscript:'
        self.window.present()
        self.edit.do_subscript()
        pass

    def do_superscript(self, *args):
        #-print 'do_superscript:'
        self.window.present()
        self.edit.do_superscript()
        pass

    def on_about(self, *args):
        #-print 'on_about:'
        authors = [
            "Jiahua Huang <jhuangjiahua@gmail.com>",
            "Aron Xu <happyaron.xu@gmail.com>",
            ]
        about = GObject.new(Gtk.AboutDialog, 
                name=_("GWrite"), 
                program_name=_("GWrite"),
                logo_icon_name="gwrite",
                version=__version__,
                copyright=_("Copyright (C) 2009-2010 Jiahua Huang, Aron Xu"),
                comments=_("Simple GTK+ HTML5 Rich Text Editor"),
                license="LGPLv3+",
                website="http://gwrite.googlecode.com/",
                website_label="gwrite.googlecode.com",
                authors=authors)
        #about.set_transient_for(self.window)
        about.run()     
        about.destroy()
        pass

    def hide_findbar(self, *args):
        #-print 'hide_findbar:'
        self.findbar.hide()
        pass

    def do_highlight_text_matches(self, *args):
        text = self.entry_searchtext.get_text()
        if text:
            self.edit.unmark_text_matches()
            matches = self.edit.mark_text_matches(text, 0, 0)
            self.edit.set_highlight_text_matches(1)
            self.entry_searchtext.set_tooltip_markup(_("%s matches") % matches)
            pass
        else:
            self.edit.unmark_text_matches()
            self.edit.set_highlight_text_matches(0)
            self.entry_searchtext.set_tooltip_text(_("Search text"))
            pass
        pass

    def do_find_text_backward(self, *args):
        #-print 'do_find_text_backward:'
        text = self.entry_searchtext.get_text()
        if not text: return
        self.edit.do_find_text_backward(text)
        pass

    def do_find_text(self, *args):
        #-print 'do_find_text:'
        #  点击前面的图标为向上查找
        #if self.entry_searchtext.get_pointer()[0] < 30:
        #    return self.do_find_text_backward()
        text = self.entry_searchtext.get_text()
        if text:
            self.edit.do_find_text(text)
        pass

    def do_replace_text(self, *args):
        #-print 'do_replace_text:'
        ffindtext   = self.entry_searchtext.get_text()
        replacetext = self.entry_replace_text.get_text()
        if ffindtext:
            self.edit.do_replace_text(ffindtext, replacetext)
        pass

    def do_replace_text_all(self, *args):
        #-print 'do_replace_text_all:'
        ffindtext   = self.entry_searchtext.get_text()
        replacetext = self.entry_replace_text.get_text()
        if ffindtext:
            self.edit.do_replace_text_all(ffindtext, replacetext)
        pass

    def get_custom_widget(self, id, string1, string2, int1, int2):
        w = Gtk.Label(_("(custom widget: %s)") % id)
        return w


##cmd test

usage = _("""GWrite

Usage:
  gwrite [OPTION...] [FILE...] - Edit html files

Options:
  -h, --help                     Show help options
  -v, --version                  Show version information
""")

def openedit(filename=""):
    '''MainWindow() 的包装
    要 return False 以免 Gtk.idle_add, Gtk.timeout_add 重复执行
    '''
    Windows[0].open(filename)
    return False

def _listen(s):
    '''监听 unix socket
    '''
    #-print 'listen:', s
    while 1:
        conn, addr = s.accept()
        rev = conn.recv(102400)
        for i in rev.split('\n'):
            #-print 'Open:', i
            GObject.idle_add(openedit, i)
            pass
        pass
    pass

def main():
    '''处理命令行
    '''
    import os, sys
    import socket
    ## 处理命令行参数
    import getopt
    config.load()
    GObject.threads_init()
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vh', ['version', 'help'])
        pass
    except:
        print usage
        return
    for o, v in opts:
        if o in ('-h', '--help'):
            print usage
            return
        elif o in ('-v', '--version'):
            print __version__
            return
        pass
    ## 要 打开的文件
    editfiles = [ os.path.abspath(i) for i in args ]
    ## 单实例模式
    if config.single_instance_mode:
        ## 设 profdir 和 ctlfile
        profdir = config.profdir
        ## 单实例运行， 尝试用已打开 GWrite
        ctlfile = config.ctlfile
        try:
            ## 已打开 GWrite 的情况
            s = socket.socket(socket.AF_UNIX)
            s.connect(ctlfile)
            s.send('\n'.join(editfiles))
            #-print 'sent:', editfiles
            return
        except:
            #raise
            #-print 'new:'
            pass
        ## 监听 socket
        s = socket.socket(socket.AF_UNIX)
        if os.access(ctlfile, os.R_OK): os.remove(ctlfile)
        s.bind(ctlfile)
        s.listen(1)
        thread.start_new_thread(_listen, (s,))
        pass
    ## 打开文件
    edit = MainWindow( editfiles[0:] and editfiles[0] or '' )
    for i in editfiles[1:]:
        i = os.path.abspath(i)
        edit.open(i)
        pass
    ## 处理 Gtk 图标主题
    settings = Gtk.Settings.get_default()
    if settings.get_property( 'gtk-icon-theme-name' ) == 'hicolor':
        settings.set_property( 'gtk-icon-theme-name', 'Tango')
        pass
    ## 处理额外图标路径
    icon_theme = Gtk.IconTheme.get_default()
    icon_dir = os.path.dirname(__file__) + '/icons'
    icon_theme.append_search_path(icon_dir)
    ##
    Gdk.threads_enter()
    Gtk.main()
    Gdk.threads_leave()

if __name__ == '__main__':
    main()

