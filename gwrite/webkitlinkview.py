#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''WebkitLinkView
@author: U{Jiahua Huang <jhuangjiahua@gmail.com>}
@license: LGPLv3+
'''

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import WebKit

import re

def proc(html):
    """处理 html 链接

    >>> proc('     <a href="#3.2.1">3.2.1 heading</a>')
    '<a href="#3.2.1" onDblClick="window.location.href=\'+\'+this.href;" onMouseOver="document.title=this.href;" >     3.2.1 heading</a>'
    """
    return re.sub('( *)(.*?)(>)(.*)', 
        '''\\2 onDblClick="window.location.href='+'+this.href;" onMouseOver="document.title=this.href;" \\3\\1\\4''', 
        html)

def stastr(stri):
    '''处理字符串的  '   "
    '''
    return stri.replace("\\","\\\\").replace(r'"',r'\"').replace(r"'",r"\'").replace('\n',r'\n')

class LinkTextView(WebKit.WebView):
    #__gtype_name__ = 'LinkTextView'
    __gsignals__ = {
        'url-clicked': (GObject.SIGNAL_RUN_LAST, None, (str, str)), # href, type
    }    
    def __init__(self):
        WebKit.WebView.__init__(self)
        self.connect("navigation-requested", self.on_navigation_requested)
        #self.connect_after("populate-popup", lambda view, menu: menu.destroy()) # 暂时禁止右键菜单
        self.set_property('can-focus', False)
        pass

    def updatehtmllinks(self, html):
        self.load_html_string('''<html>
        <head>
        <style>
        a:hover {
            font-weight: bold;
            border-bottom: 1px solid blue;
        }
        a { 
            width: 90%%;
            text-decoration: none ;
            white-space: pre;
            display: block;
        }
        </style>
        </head>
        <body>
        <code>%s</code>
        </body>
        </html>''' % proc(html), '') # 首次执行时还没 document.body 对象
        self.updatehtmllinks = lambda html : self.execute_script('document.body.innerHTML="<code>%s</code>";' % stastr(proc(html))) # 保持滚动条位置
        pass

    def on_navigation_requested(self, widget, WebKitWebFrame, WebKitNetworkRequest):
        href = WebKitNetworkRequest.get_uri()
        if '#' in href:
            self.emit("url-clicked", href, "link")
            pass
        return True

if __name__=="__main__":
    main()


