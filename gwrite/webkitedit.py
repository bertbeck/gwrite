#!/usr/bin/python
# -*- coding: UTF-8 -*-
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# Author: Huang Jiahua <jhuangjiahua@gmail.com>
# License: LGPLv3+
# Last modified:

__version__ = '0.5.1'

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import WebKit

import gtklatex
import urllib2
import os, errno
import re
import docfilter
import highlight

import json

import sys
reload(sys)
sys.setdefaultencoding('utf8')

try: import i18n
except: from gettext import gettext as _

def format_html(html):
    '''给 html 添加适当换行
    '''
    html = re.sub('\n?\ ?<(address|blockquote|center|dir|div|dl|fieldset|form|h1|h2|h3|h4|h5|h6|hr|isindex|menu|noframes|noscript|ol|p|pre|table|ul|dd|dt|frameset|li|tbody|td|tfoot|th|thead|tr)([^>]*?)>', '\n<\\1\\2>', html)
    html = re.sub('</(address|blockquote|center|dir|div|dl|fieldset|form|h1|h2|h3|h4|h5|h6|hr|isindex|menu|noframes|noscript|ol|p|pre|table|ul|dd|dt|frameset|li|tbody|td|tfoot|th|thead|tr)([^>]*?)>\ ?\n?', '</\\1\\2>\n', html)
    html = re.sub('\n?<(img|hr|br)([^>]*?)>\n?', '\n<\\1\\2>\n', html)
    ## 对于 pre，合并相邻 <pre>，将 <pre> 内的 <br> 转为 "\n"
    html = re.sub('\n?</pre>\s*<pre>\n?', '\n', html)
    html = re.sub('<pre>[^\0]*?</pre>', lambda m: re.sub('\n?<br>\n?', '\\n', m.group()), html)
    return html

def stastr(stri):
    '''处理字符串的  '   "
    '''
    return stri.replace("\\","\\\\").replace(r'"',r'\"').replace(r"'",r"\'").replace('\n',r'\n')

def get_end_ids(start):
    '''获取可能的下一个 id
    @note: 为了符合 w3 的 id 命名，在数字前加上字母 g 前缀

    >>> get_end_ids('g5.1.1.1')
    ['g5.1.1.2', 'g5.1.2', 'g5.2', 'g6']
    '''
    start = start.replace('g', '')
    ids = start.split('.')
    ends = []
    for i in range(1, len(ids)+1):
        end = int(ids[-i])+1
        end = '.'.join(ids[:-i] + [str(end)])
        ends.append('g' + end)
        pass
    return ends

def textbox(title='Text Box', label='Text',
        parent=None, text=''):
    """display a text edit dialog
    
    return the text , or None
    """
    dlg = Gtk.Dialog(title, parent, Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK    ))
    dlg.set_default_size(500,500)
    #lbl = Gtk.Label(label)
    #lbl.set_alignment(0, 0.5)
    #lbl.show()
    #dlg.vbox.pack_start(lbl,  False)
    gscw = Gtk.ScrolledWindow()
    gscw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    textview=Gtk.TextView()
    textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    buffer = textview.get_buffer()
    
    if text: buffer.set_text(text)    
    
    #textview.show()
    gscw.add(textview)
    #gscw.show()
    dlg.vbox.pack_start(gscw)
    dlg.show_all()
    resp = dlg.run()
    
    text=buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter())
    dlg.destroy()
    if resp == Gtk.ResponseType.OK:
        return text
    return None

def menu_find_with_stock(menu, stock):
    '''查找菜单中对应 stock 的菜单项位置
    '''
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

BLANKHTML='''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="generator" content="GWrite (WYSIWYG editor)" />
  <title></title>
  <style>
img{
    border: 2px;
    border-style: solid;
    border-color: #c3d9ff;
    padding: 5px;
}
h1, h2, h3, h4, h5, h6 {
    color: #7DA721;
    font-weight: bold;
}
p{
    text-indent: 2em;
    text-align: justify;
}
blockquote{
    background-color:#EEFFFF;
    border-left: 5px solid green;
    padding-left: 5px;
    margin: 0px;
    padding: 5px;
}
pre{
    background-color:#EEEEFF;
    display: block;
    border-left: 1px solid green;
    margin: 0px;
    padding: 5px;
}
code{
    background-color:#EEEEFF;
    margin: 15px;
    padding: 5px;
}
#toctitle {
    -webkit-transition: all .3s ease-out-in;
}
#toctitle::-webkit-scrollbar {
    width: 3.5px;
    height: 3.5px;
}
#toctitle::-webkit-scrollbar-thumb:horizontal {
    background-color: #D35D22;
}
#WebKit-Editing-Delete-Button {
    border: none;
    padding: 0px;
}
  </style>
</head>
<body>
<p><br/></p>
</body>
</html>
'''

class WebKitEdit(WebKit.WebView):
    '''Html Edit Widget
    '''
    def __init__(self, editfile=''):
        '''WebKitEdit.__init__
        '''
        WebKit.WebView.__init__(self)
        self.set_property('can-focus', True)
        self.set_property('can-default', True)
        self.set_full_content_zoom(1)
        self.write_html(BLANKHTML)
        self.lastDir = ''
        self.editfile = editfile
        if editfile and os.access(editfile, os.R_OK):
            self.open(editfile)
            self.lastDir = os.path.dirname(editfile)
            pass
        else:
            pass
        self.set_editable(1)
        #self.do_editable()
        self.connect("load-finished", self.do_editable) # 确保 document.body 已经准备好了
        self._html = ""
        self.connect("navigation-requested", self.on_navigation_requested)
        self.connect("new-window-policy-decision-requested", self.on_new_window_policy_decision_requested)
        self.connect_after("populate-popup", self.populate_popup)
        self.connect("script-alert", self.on_script_alert)

        ## 允许跨域 XMLHttpRequest，以便 base64 内联图片
        settings = self.get_settings()
        settings.set_property('enable-xss-auditor', False)
        settings.set_property('enable-universal-access-from-file-uris', True)
        settings.set_property('enable-file-access-from-file-uris', True)
        settings.set_property('enable-page-cache', True)
        settings.set_property('javascript-can-access-clipboard', True)
        settings.set_property('tab-key-cycles-through-elements', False)

        ##
        pass

    def open(self, editfile):
        '''打开文件
        '''
        self.editfile = editfile
        ## 导入 .doc
        if re.match('.*\.doc', editfile, re.I):
            self.editfile = editfile[:-4] + '.html'
            editfile = docfilter.doc2html(editfile)
            pass
        ## 导入 .odf
        elif re.match('.*\.odf', editfile, re.I):
            pass
        ## 导入 .rtf
        elif re.match('.*\.rtf', editfile, re.I):
            pass
        ## 打开 html
        WebKit.WebView.open(self, editfile)
        pass

    def eval(self, js):
        '''执行 javascript
        '''
        d = self.get_dom_document()
        ddw = d.get_default_view()
        ddw.set_status(js)
        self.execute_script('''
            window.status = JSON.stringify( eval(window.status) );
        ''')
        m = ddw.get_status()
        return m and json.loads(m) or ''

    def get_html(self, *args):
        '''获取 HTML 内容
        '''
        if not self.get_view_source_mode():
            self.execute_script('guesstitle();')
            self.do_image_base64()
            domdocument = self.get_dom_document()
            html = domdocument.get_document_element().get_outer_html()
            html = format_html(html)
            return '<!DOCTYPE html>\n' + html
        else:
            text = self.eval('''
                html = document.body.innerHTML;
                html = html.replace(/td><td/g, 'td>\\n<td');
                document.body.innerHTML = html;
                text = document.body.textContent;
                text;''')
            text = re.sub('\\s*</body>', '\n</body>', text)
            text = text.replace(' \n', '\n')
            text = format_html(text)
            return text

    def get_section(self, *args):
        #@TODO: 用于查看章节字数等
        js = '''
        var range = document.createRange();
        range.setStart(startNode, startOffset);
        range.setEnd(endNode, endOffset);
        '''
        pass

    def get_selection(self, *args):
        '''获取选中区域的文本
        '''
        text = self.eval('''
            document.getSelection().toString();
        ''')
        return text

    def get_text(self, *args):
        '''获取纯文本内容

        处理过换行
        '''
        text = self.eval('''
            text = document.body.innerText;
            text;''')
        return text

    def set_saved(self, *args):
        '''设置为已经保存
        '''
        self._html = self.eval('document.documentElement.innerHTML')
        pass

    def unset_saved(self, *args):
        '''设置为未保存
        '''
        self._html = ""
        pass

    def is_saved(self, *args):
        '''查询是否已经保存
        '''
        return self._html == self.eval('document.documentElement.innerHTML')

    def on_new_window_policy_decision_requested(self, widget,
            WebKitWebFrame, WebKitNetworkRequest, 
            WebKitWebNavigationAction, WebKitWebPolicyDecision):
        '''处理新窗口事件
        如点击 target=_blank 的链接
        '''
        uri = WebKitNetworkRequest.get_uri()
        uri = urllib2.unquote(uri)
        os.spawnvp(os.P_NOWAIT, 'xdg-open', ['xdg-open', uri])
        return True

    def on_script_alert(self, view, frame, msg, *args):
        if msg.startswith('_#uptex:'):
            a, id, m, latex = msg.split(':', 3)
            print id, latex
            latex = latex.replace('\\n', '\n').replace('\\\\', '\\')
            latex = gtklatex.latex_dlg(latex)
            if latex:
                img = gtklatex.tex2base64(latex)
                self.execute_script("""
                    window.focus();
                    img = document.getElementById('%s');
                    img.alt = "mimetex:"+"%s";
                    img.src = '%s';
                """ % (id, stastr(latex), stastr(img)))
                pass
            self.execute_script("""document.getElementById('%s').removeAttribute("id");""" % id)
            return True
        return False

    def on_navigation_requested(self, widget, WebKitWebFrame, WebKitNetworkRequest):
        '''处理点击链接事件
        如点击超链接后应执行 xdg-open 用桌面浏览器打开 URL
        '''
        #-print 'on_navigation_requested:'
        #print WebKitWebFrame, WebKitNetworkRequest
        uri = WebKitNetworkRequest.get_uri()
        uri = urllib2.unquote(uri)
        #-print uri
        # self.open() 的情况
        if uri == 'file://' + self.editfile:
            return False
        # 跳转锚点
        if uri.startswith('#'): 
            self.go_anchor(uri)
            return True
        # 打开外部链接
        docuri = self.get_main_frame().get_uri()
        if docuri.split('#', 1)[0] != uri.split('#', 1)[0]: 
            os.spawnvp(os.P_NOWAIT, 'xdg-open', ['xdg-open', uri])
            return True
        return False

    def populate_popup(self, view, menu):
        '''处理编辑区右键菜单
        '''
        # 无格式粘贴菜单
        cb = self.get_clipboard(Gdk.Atom.intern_static_string('CLIPBOARD'))
        cbp = self.get_clipboard(Gdk.Atom.intern_static_string('PRIMARY'))
        text = cb.wait_for_text() or cbp.wait_for_text()
        if text:
            menuitem_paste_unformatted = Gtk.ImageMenuItem(_("Pa_ste Unformatted"))
            menuitem_paste_unformatted.show()
            #menuitem_paste_unformatted.connect("activate", self.do_paste_unformatted)
            menuitem_paste_unformatted.connect("activate", 
                    lambda *i: self.do_insert_text(text) )
            n = menu_find_with_stock(menu, 'gtk-paste')
            if n > -1:
                menu.insert(menuitem_paste_unformatted, n+1)
                pass
            pass
        return False

    def select_section(self, widget, anc=""):
        '''在编辑区选中 id 对应章节文字
        '''
        if not anc: anc = widget
        start_id = anc.replace('#', '')
        end_ids = get_end_ids(start_id)
        #-print 'select_section:', start_id, end_ids
        self.go_anchor(anc)
        self.eval('''
            //document.execCommand("selectall", false, false);
            start = document.getElementById("%s");
            ids = %s;
            for (var i=0; i<ids.length; i++){
                if (end = document.getElementById(ids[i])) break;
            }
            sel = document.getSelection();
            sel.collapse(start, 0);
            if (end){
                sel.extend(end, 0);
            } else {
                end = document.createElement('span');
                document.body.appendChild(end);
                sel.extend(end, 0);
                document.body.removeChild(end);
            }
            window.focus();
        ''' % (start_id, end_ids))
        pass

    def go_anchor(self, widget, anc=""):
        '''跳转到锚点
        '''
        if not anc: anc = widget
        anc = anc.replace('#', '')
        return self.execute_script("window.location.href='#%s';" % anc);
        #self.execute_script("""
        #el = document.getElementById("%s");
        #window.scrollTo(0, el.offsetTop);
        #""" % anc)

    def write_html(self, html):
        '''写入 HTML
        '''
        #print 'WebKitEdit.write_html:'
        self.load_html_string(html, 'file:///tmp/blank.html')
        pass

    def update_html(self, html):
        '''更新 html
        用 dom 操作保留页面滚动条位置
        '''
        #print 'WebKitEdit.update_html:'
        # js document 无法更新 head:
        #   console message:  @3: Error: NO_MODIFICATION_ALLOWED_ERR: DOM Exception 7
        # 所以改为直接 load_html_string()
        uri = (self.editfile.startswith('/') and 'file://' + self.editfile) or 'file:///tmp/blank.html'
        self.load_html_string(html, uri)
        return
        #head = (re.findall(r'''<head>([^\0]*)</head>''', html)+[""])[0]
        #body =  re.sub(r'''<head>[^\0]*</head>''', '', html)
        #self.execute_script(r''' 
        #        document.body.innerHTML="%s";
        #        document.getElementsByTagName("head")[0].innerHTML="%s";
        #        '''% (stastr(body), stastr(head)))
        #pass

    def update_bodyhtml(self, html):
        '''更新正文 html
        '''
        #print 'WebKitEdit.update_bodyhtml:'
        d = self.get_dom_document()
        body = d.get_body()
        body.set_innerHTML(html)
        pass

    def do_editable(self, *args):
        '''set editable
        '''
        #@TODO: 加入更新标题，更新目录 js 函数
        #-print 'WebKitEdit.set_editable:'
        #cmd = r''' document.documentElement.contentEditable="true"; '''
        self.set_editable(1)
        if self.get_view_source_mode():
            # 隐藏源码编辑模式下的 webkit 删除工具
            # webkit 编辑模式下会有
            #   #WebKit-Editing-Delete-Container
            #   #WebKit-Editing-Delete-Outline
            #   #WebKit-Editing-Delete-Button
            # 几个 div 和 img 删除控件，
            # 在编辑模式的源码表格下会影响使用，所以需要隐藏掉
            # 默认源码模式下 styleSheets 是空的，所以得先插入一个 <style>
            self.execute_script('''
                s = document.createElement('style')
                document.body.appendChild(s);
                setTimeout(function() {
                    document.styleSheets[0].insertRule('#WebKit-Editing-Delete-Container {display: none;}', 0);
                    document.styleSheets[0].insertRule('#WebKit-Editing-Delete-Outline {display: none;}', 0);
                    document.styleSheets[0].insertRule('#WebKit-Editing-Delete-Button {display: none;}', 0);
                }, 100);
            ''')
            pass
        cmd = r''' 
            /*document.documentElement.contentEditable="true";*/
            /*document.body.contentEditable="true";*/
            document.execCommand("useCSS",false, true);
            /* 处理标题 */
            function guesstitle(){
              if( (t=document.getElementsByTagName("title")) && (title=t[0].textContent) ){
                return title;
              }else if( (h1=document.getElementsByTagName("h1")) && h1.length>0 ){
                title=h1[0].textContent;
              } else {
                //p = document.createElement('pre');
                //p.innerHTML = document.body.innerHTML.replace(/</g, '\n\n<').replace(/>/g, '>\n\n');
                //title = p.textContent.replace(/^\s+/g, '').split('\n')[0];
                title = document.body.textContent.split('\n')[0];
              }
              if(! document.getElementsByTagName("title") ){
                t = document.createElement('title');
                t.textContent=title;
                document.getElementsByTagName("head")[0].appendChild(t);
              }else{
                document.getElementsByTagName("title")[0].textContent=title;
              }
            };

            /* 目录处理 */
            function getheads(){
                /* 取得所有 heading 标签到 heads */
                return document.querySelectorAll('h1, h2, h3, h4, h5, h6');
            };
            
            var autonu = 0;
            if( i = document.body.getAttribute("orderedheadings")){
                autonu = i;
            }
            
            function toggledirnu(){
                if (autonu == 1){
                    autonu = 0;
                    document.body.setAttribute("orderedheadings", 0);
                }else{
                    autonu = 1;
                    document.body.setAttribute("orderedheadings", 1);
                }
                return updatedir();
            };
            function getiname(tt, name){
                if (autonu == 1){
                    return tt + '  ' + iname;
                }else{
                    return iname;
                }
            }
            
            function getdir(){
                var heads = getheads();
                var tt = '';
                var tdir = '';
                var h1 = 0;
                var h2 = 0;
                var h3 = 0;
                var h4 = 0;
                var h5 = 0;
                var h6 = 0;
                var startHeader = 0;
                var startHeader = 1;
                var g = '';
                
                for (var i=startHeader ; i<heads.length; i++){
                    var inode = heads[i];
                    iname = inode.textContent.replace(/^\s*[.\d]*\s+/, ''); /*把标题前边的数字识别为序号*/
                    iname = iname.replace('\n',' ');
                    g = (inode.id.replace(/[.0-9]/g,'') || g.replace(/[.0-9]/g,'') || Math.random().toString(36).replace(/[.0-9]/g,'')) + '.';
                    switch(heads[i].nodeName){
                        case "H1":
                        tt = '';
                        h1 += 1;
                        h2 = 0;
                        h3 = 0;
                        h4 = 0;
                        h5 = 0;
                        h6 = 0;
                        tt += String(h1);
                        inode.id = g + tt;
                        inode.textContent = getiname(tt, name);   
                        tdir += '';
                        tdir += '<a href="#g' + tt + '">' + getiname(tt, name) + '</a>\n';
                        break;
            
                        case "H2":
                        tt = '';
                        h2 += 1;
                        h3 = 0;
                        h4 = 0;
                        h5 = 0;
                        h6 = 0;
                        tt += String(h1) + '.' + h2;
                        inode.id = g + tt;
                        inode.textContent = getiname(tt, name);           
                        tdir += ' ';
                        tdir += '<a href="#g' + tt + '">' + getiname(tt, name) + '</a>\n';
                        break;
            
                        case "H3":
                        tt = '';
                        h3 += 1;
                        h4 = 0;
                        h5 = 0;
                        h6 = 0;
                        tt += String(h1) + '.' + h2 + '.' + h3;
                        inode.id = g + tt;
                        inode.textContent = getiname(tt, name);           
                        tdir += '  ';
                        tdir += '<a href="#g' + tt + '">' + getiname(tt, name) + '</a>\n';
                        break;
            
                        case "H4":
                        tt = '';
                        h4 += 1;
                        h5 = 0;
                        h6 = 0;
                        tt += String(h1) + '.' + h2 + '.' + h3 + '.' +h4;
                        inode.id = g + tt;
                        inode.textContent = getiname(tt, name);           
                        tdir += '   ';
                        tdir += '<a href="#g' + tt + '">' + getiname(tt, name) + '</a>\n';
                        break;
            
                        case "H5":
                        tt = '';
                        h5 += 1;
                        h6 = 0;
                        tt += String(h1) + '.' + h2 + '.' + h3 + '.' + h4 + '.' + h5;
                        inode.id = g + tt;
                        inode.textContent = getiname(tt, name);           
                        tdir += '    ';
                        tdir += '<a href="#g' + tt + '">' + getiname(tt, name) + '</a>\n';
                        break;
            
                        case "H6":
                        tt = '';
                        h6 += 1;
                        tt += String(h1) + '.' + h2 + '.' + h3 + '.' + h4 + '.' + h5 + '.' + h6;
                        inode.id = g + tt;
                        inode.textContent = getiname(tt, name);           
                        tdir += '     ';
                        tdir += '<a href="#g' + tt + '">' + getiname(tt, name) + '</a>\n';
                        break;
                    }
            
                }
                pre = document.createElement('pre');
                pre.innerHTML = tdir;
                tdir = pre.innerHTML;
                return tdir;
            }
            
            function updatedir(){
                if( i = document.body.getAttribute("orderedheadings")){
                    autonu = i;
                }
                dirhtml = getdir();
                if (t=document.getElementById("toctitledir")){
                    t.innerHTML = dirhtml;
                }
                return dirhtml;
            };

            function  randomChars()  {
                return Math.random().toString(16).slice(2);
            }

            function uptex(img){
                img.id = 'mimetex_' + randomChars();
                alert("_#uptex:" + img.id + ':' + img.alt);
            }
                        
            window.focus();
            ;'''
        self.execute_script(cmd)
        pass

    def do_image_base64(self, use_canvas=False):
        '''convert images to base64 inline image
        see http://tools.ietf.org/html/rfc2397
        当 use_canvas=True 时会使用异步操作，图片会用 jpeg 80% 减小体积
        '''
        Gdk.threads_leave() # 修正线程问题
        if use_canvas:
            self.execute_script(r'''
    var make_images_inline = function(doc){
        doc = doc || document.body;
        var image2dataurl = function(img) {
            if (img.src.match(/^data:/)) { return img.src }
            //img.crossOrigin = "Anonymous";
            var canvas = document.createElement("canvas");
            canvas.width = img.width;
            canvas.height = img.height;
            var ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0);
            var dataURL = canvas.toDataURL("image/jpeg", 0.8);
            return dataURL;
        }
        var make_image_inline = function(img) {
            if (img.src.match(/^data:/)) { return 0; }
            if (img.complete) {
                img.setAttribute('data-src', img.src);
                img.src = image2dataurl(img);
            } else {
                img.onload = function() {
                    make_image_inline(img);
                };
            }
        }
        var images = doc.querySelectorAll('img');
        for (var i=images.length-1; i+1; i--){
            img = images[i];
            try {
              make_image_inline(img);
            } catch(e){
            }
        }
    };
    make_images_inline();
        ''')
        else:
            self.execute_script(r'''
        var keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
        function encode64(input) {
           var output = "";
           var chr1, chr2, chr3;
           var enc1, enc2, enc3, enc4;
           var i = 0;
           do {
              chr1 = input.charCodeAt(i++) & 0xff;
              chr2 = input.charCodeAt(i++) & 0xff;
              chr3 = input.charCodeAt(i++) & 0xff;
              enc1 = chr1 >> 2;
              enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
              enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
              enc4 = chr3 & 63;
              if (isNaN(chr2)) {
                 enc3 = enc4 = 64;
              } else if (isNaN(chr3)) {
                 enc4 = 64;
              }
              output = output + keyStr.charAt(enc1) + keyStr.charAt(enc2) + 
                 keyStr.charAt(enc3) + keyStr.charAt(enc4);
           } while (i < input.length);   
           return output;
        };
        /*netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserRead");*/
        for (var i=document.images.length-1; i+1; i--){
             img = document.images[i];
             if(img.src && !img.src.match(/^data:/)){
                 mx = new XMLHttpRequest();
                 mx.open("GET", img.src, false);
                 mx.overrideMimeType('text/plain; charset=x-user-defined');           
                 mx.send(null);
                 if (mx.responseText && (mx.status==200 || mx.status==0) ){
                     img.setAttribute('uri', img.src);
                     img.src = "data:image;base64," + encode64(mx.responseText);
                 };
             }
        };
        ;
        ''')
        pass

    def set_visual_view(self, visual=True):
        '''切换所见所得模式
        '''
        if visual:
            if self.get_view_source_mode():
                self.toggle_html_view()
            pass
        else:
            if not self.get_view_source_mode():
                self.toggle_html_view()
                pass
            pass
        pass

    __prev_visual_html = ''
    __prev_source_html = ''
    def toggle_html_view(self, *args):
        '''查看源码
        '''
        #print 'WebKitEdit.toggle_html_view:'
        ## 转换模式会修改 html 源码，所以得判断下可有保存
        ## 从所见所得模式转到源码模式
        if not self.get_view_source_mode():
            html = self.get_html()
            self.__prev_visual_html = html
            is_saved = self.is_saved()
            self.set_view_source_mode(1)
            self.reload()
            self.update_html(html)
            def do_is_saved():
                if is_saved:
                    self.__prev_source_html = self.get_html()
                    pass
                else:
                    self.__prev_source_html = ''
                pass
            GObject.idle_add(do_is_saved)
            pass
        ## 从源码模式转到所见所得模式
        else:
            html = self.get_html()
            self.set_view_source_mode(0)
            self.reload()
            if self.__prev_source_html == html:
                self.update_html(self.__prev_visual_html)
                GObject.idle_add(self.set_saved)
                pass
            else:
                self.update_html(html)
                pass
            pass
        return

    def do_print(self, *args):
        '''打印
        '''
        #print 'WebKitEdit.do_print:'
        self.execute_script('print(); ')
        pass

    def do_undo(self, *args):
        '''撤销
        '''
        #print 'WebKitEdit.do_undo:'
        self.execute_script(' document.execCommand("undo", false, false); ')

    def do_redo(self, *args):
        '''重做
        '''
        #print 'WebKitEdit.do_redo:'
        self.execute_script(' document.execCommand("redo", false, false); ')

    def do_cut(self, *args):
        '''剪切
        '''
        #print 'WebKitEdit.do_cut:'
        self.cut_clipboard()

    def do_copy(self, *args):
        '''复制
        '''
        #print 'WebKitEdit.do_copy:'
        self.copy_clipboard()

    def do_paste(self, *args):
        '''粘贴
        '''
        #print 'WebKitEdit.do_paste:'
        #self.execute_script(' document.execCommand("paste", false, false); ')
        self.paste_clipboard()

    def do_paste_unformatted(self, *args):
        '''无格式粘贴
        '''
        #-print 'do_paste_unformatted:'
        text = Gtk.Clipboard().wait_for_text() or Gtk.Clipboard(selection="PRIMARY").wait_for_text()
        if text:
            self.do_insert_text(text)
            return
        return

    def do_delete(self, *args):
        '''删除选中内容
        '''
        #print 'WebKitEdit.do_delete:'
        self.execute_script(' document.execCommand("delete", false, false); ')

    def do_selectall(self, *args):
        '''全选
        '''
        #print 'WebKitEdit.do_selectall:'
        self.execute_script(' document.execCommand("selectall", false, false); ')

    ################################################
    #
    def do_view_update_contents(self, *args):
        '''更新文档目录
        依据标题样式
        '''
        #print 'WebKitEdit.view_update_contents:'
        return self.eval(r'''
            updatedir();
            ''')
        pass

    def do_view_toggle_autonumber(self, *args):
        '''切换标题自动编号
        '''
        #print 'WebKitEdit.view_toggle_autonumber:'
        return self.eval(r'''
            toggledirnu();
            ''')
        pass

    def do_view_sourceview(self, *args):
        '''查看源码
        '''
        #print 'WebKitEdit.view_sourceview:'
        self.toggle_html_view()
        pass

    def do_insertimage(self, img=""):
        '''插入图片
        '''
        #if img.startswith('/'): img = 'file://' + img
        #print 'WebKitEdit.do_insertimage:', img
        self.execute_script(''' 
                document.execCommand("insertimage", false, "%s"); 
                '''%stastr(img))
        pass

    def do_createlink(self, link=""):
        '''创建超链接
        '''
        #print 'WebKitEdit.do_createlink:'
        self.execute_script(r''' 
                link = "%s";
                if( !document.execCommand("createlink", false, link) )
                {
                    text = link;
                    i = document.createElement("div");
                    i.textContent = text;
                    text = i.innerHTML;
                    html = '<a href="' + link + '">' + text + '</a>';
                    document.execCommand("inserthtml", false, html);
                }
                '''%stastr(link))
        pass

    def do_inserthorizontalrule(self, *args):
        '''插入水平线
        '''
        #print 'WebKitEdit.do_inserthorizontalrule:'
        self.execute_script(''' 
                document.execCommand("inserthorizontalrule", false, false); ''')
        pass

    def do_insert_table(self, rows, cows):
        '''插入表格

        会询问行、列数
        '''
        #print 'WebKitEdit.do_insert_table:'
        html = "\n<table cellspacing='0' border='1px' bordercolor='#aaaacc' width='100%' ><tbody>\n"
        for row in range(int(rows)):
            html+= "<tr>\n"
            for cow in range(int(cows)):
                html+= "        <td><br/></td>\n"
            html+= "</tr>\n"
        html+= "</tbody></table>\n<br/>\n"
        self.do_insert_html(html)
        pass

    def do_insert_html(self, html):
        '''插入 html
        '''
        #print 'WebKitEdit.do_insert_html:'
        if not self.get_view_source_mode():
            self.execute_script('''
                   window.focus();
                   document.execCommand("inserthtml", false, "%s");
                  '''%stastr(html))
            pass
        else:
            self.execute_script('''
                    var text = "%s";
                    var i = document.createElement("div");
                    i.textContent = text;
                    html = i.innerHTML;
                    html = html.replace(/\\ \\ /g, '&nbsp;&nbsp;');
                    document.execCommand("inserthtml", false, html);
                    '''%stastr(html))
            pass
        pass

    def do_insert_text(self, text):
        '''插入纯文本

        会先专为 html 再 insert_htm
        '''
        #print 'WebKitEdit.do_insert_text:'
        self.execute_script(''' 
                var text = "%s";
                var i = document.createElement("div");
                i.textContent = text;
                html = i.innerHTML;
                html = html.replace(/\\ \\ /g, '&nbsp;&nbsp;');
                html = html.replace(/\\n/g, '<br />\\n');
                document.execCommand("inserthtml", false, html); 
                '''%stastr(text))
        pass

    def do_insert_contents(self, *args):
        '''插入目录
        '''
        #print 'WebKitEdit.do_insert_contents:'
        #@FIXME: 无法删除现存目录表格
        self.execute_script(r''' 
            if(t=document.getElementById("toctitle")){
                document.removeChild(t);
            }
            html = '<br/><div id="toctitle" contentEditable="false" style="\
                text-indent: 0; background-color:#EEEEFF; display: block; border: 1px solid green; margin: 15px; padding: 5px; white-space: pre;"\
            ><div title="点击固定目录" onclick=\' t = document.getElementById("toctitle"); if(this.alt){ this.alt = 0; document.body.style.cssText=" "; t.style.cssText="\
                text-indent: 0; background-color:#EEEEFF; display: block; border: 1px solid green; margin: 15px; padding: 5px; white-space: pre; "\
            ; }else{ this.alt = 1; document.body.style.cssText="\
            margin:5pt; border:5pt; height:100%; margin-right: 210px; overflow-y:auto;"\
            ; t.style.cssText="\
            text-indent: 0; background-color:#EEEEFF; display: block; border-left: 1px solid green; margin: 0px; margin-bottom:3px; padding: 5px; white-space: pre; top:0px; right:0; width: 200px; height:98%; overflow:auto; position:fixed; "\
            ; } \' class="dirtitle">目录<br/></div><span id="toctitledir"> </span></div><br/>';
            document.execCommand("inserthtml", false, html); 
            updatedir();
            '''.replace("目录", _("Table of contents")))
        pass

    def do_formatblock_p(self, *args):
        '''段落样式
        '''
        #print 'WebKitEdit.do_formatblock_p:'
        return self.eval(''' 
                document.execCommand("formatblock", false, "p"); 
                updatedir();
                ''')
        pass

    def do_formatblock_h1(self, *args):
        '''<h1> 样式
        @NOTE: 将一行字设为标题后，回车出现的是 <div> 而非 <p>。需要让他换行后使用 <p>。考虑在下一行添加一个 <p>
        '''
        #print 'WebKitEdit.do_formatblock_h1:'
        return self.eval(''' 
                document.execCommand("formatblock", false, "h1"); 
                updatedir();
                ''')
        pass

    def do_formatblock_h2(self, *args):
        '''<h2> 样式
        '''
        #print 'WebKitEdit.do_formatblock_h2:'
        return self.eval(''' 
                document.execCommand("formatblock", false, "h2"); 
                updatedir();
                ''')
        pass

    def do_formatblock_h3(self, *args):
        '''<h3> 样式
        '''
        #print 'WebKitEdit.do_formatblock_h3:'
        return self.eval(''' 
                document.execCommand("formatblock", false, "h3");
                updatedir();
                ''')
        pass

    def do_formatblock_h4(self, *args):
        '''<h4> 样式
        '''
        #print 'WebKitEdit.do_formatblock_h4:'
        return self.eval(''' 
                document.execCommand("formatblock", false, "h4");
                updatedir();
                ''')
        pass

    def do_formatblock_h5(self, *args):
        '''<h5> 样式
        '''
        #print 'WebKitEdit.do_formatblock_h5:'
        return self.eval(''' 
                document.execCommand("formatblock", false, "h5");
                updatedir();
                ''')
        pass

    def do_formatblock_h6(self, *args):
        '''<h6> 样式
        '''
        #print 'WebKitEdit.do_formatblock_h6:'
        return self.eval(''' 
                document.execCommand("formatblock", false, "h6");
                updatedir();
                ''')
        pass

    def do_insertunorderedlist(self, *args):
        '''圆点列表
        '''
        #print 'WebKitEdit.do_insertunorderedlist:'
        return self.eval(''' 
                document.execCommand("insertunorderedlist", false, null); ''')
        pass

    def do_insertorderedlist(self, *args):
        '''数字列表
        '''
        #print 'WebKitEdit.do_insertorderedlist:'
        return self.eval(''' 
                document.execCommand("insertorderedlist", false, null); ''')
        pass

    def do_formatblock_div(self, *args):
        ''' DIV 样式
        '''
        #print 'WebKitEdit.formatblock_div:'
        return self.eval('''
                document.execCommand("formatblock", false, "div"); ''')
        pass

    def do_formatblock_address(self, *args):
        '''地址样式
        '''
        #print 'WebKitEdit.formatblock_addres:'
        return self.eval(''' 
                document.execCommand("formatblock", false, "address"); ''')
        pass

    def do_formatblock_code(self, *args):
        '''<code> 样式
        '''
        #print 'WebKitEdit.do_formatblock_code:'
        #@FIXME: formatblock code 无效
        return self.eval(''' 
                document.execCommand("formatblock", false, "code"); ''')
        pass

    def do_formatblock_blockquote(self, *args):
        '''引用/缩进 样式
        '''
        #print 'WebKitEdit.do_formatblock_blockquote:'
        self.eval(''' 
                document.execCommand("formatblock", false, "blockquote"); ''')
        pass

    def do_formatblock_pre(self, *args):
        '''预格式化样式
        '''
        #print 'WebKitEdit.do_do_formatblock_pre:'
        self.eval('''
                document.execCommand("formatblock", false, "pre"); ''')
        #return self.do_highlight_pre(*args)
        pass

    def do_bold(self, *args):
        '''粗体
        '''
        #print 'WebKitEdit.do_bold:'
        self.execute_script(''' 
                document.execCommand("bold", false, null); ''')
        pass

    def do_underline(self, *args):
        '''下划线
        '''
        #print 'WebKitEdit.do_underline:'
        self.execute_script(''' 
                document.execCommand("underline", false, null); ''')
        pass

    def do_italic(self, *args):
        '''斜体
        '''
        #print 'WebKitEdit.do_italic:'
        self.execute_script(''' 
                document.execCommand("italic", false, null); ''')
        pass

    def do_strikethrough(self, *args):
        '''删除线
        '''
        #print 'WebKitEdit.do_strikethrough:'
        self.execute_script(''' 
                document.execCommand("strikethrough", false, null); ''')
        pass

    def do_font_fontname(self, fontname):
        '''设置字体名称
        '''
        #print 'WebKitEdit.do_font_fontname:'
        self.execute_script(r''' 
                document.execCommand("useCSS", false, true);
                document.execCommand("fontname", false, "%s"); 
                '''%fontname)
        pass

    def do_fontsize(self, fontsize):
        '''设置字号
        '''
        #print 'WebKitEdit.do_fontsize:'
        self.execute_script(r''' 
                document.execCommand("fontsize", false, "%s"); 
                '''%fontsize)
        pass

    def do_fontsize_1(self, *args):
        '''设置字号 1
        '''
        #print 'WebKitEdit.do_fontsize_1:'
        self.do_fontsize(1)
        pass

    def do_fontsize_2(self, *args):
        '''设置字号 2
        '''
        #print 'WebKitEdit.do_fontsize_2:'
        self.do_fontsize(2)
        pass

    def do_fontsize_3(self, *args):
        '''设置字号 3
        '''
        #print 'WebKitEdit.do_fontsize_3:'
        self.do_fontsize(3)
        pass

    def do_fontsize_4(self, *args):
        '''设置字号 4
        '''
        #print 'WebKitEdit.do_fontsize_4:'
        self.do_fontsize(4)
        pass

    def do_fontsize_5(self, *args):
        '''设置字号 5
        '''
        #print 'WebKitEdit.do_fontsize_5:'
        self.do_fontsize(5)
        pass

    def do_fontsize_6(self, *args):
        '''设置字号 6
        '''
        #print 'WebKitEdit.do_fontsize_6:'
        self.do_fontsize(6)
        pass

    def do_fontsize_7(self, *args):
        '''设置字号 7
        '''
        #print 'WebKitEdit.do_fontsize_7:'
        self.do_fontsize(7)
        pass

    def do_color_forecolor(self, color):
        '''设置字体颜色
        '''
        #print 'WebKitEdit.do_color_forecolor:'
        self.execute_script(r''' 
                document.execCommand("useCSS",false, false);
                document.execCommand("foreColor", false, "%s"); 
                document.execCommand("useCSS",false, true);
                '''%color)
        pass

    def do_color_hilitecolor(self, color):
        '''设置高亮颜色
        
        即字体背景色
        '''
        # 设背景色无效 需要 useCSS 选项 
        #print 'WebKitEdit.do_color_hilitecolor:'
        self.execute_script(r''' 
                document.execCommand("useCSS",false, false);
                document.execCommand("hilitecolor", false, "%s"); 
                document.execCommand("useCSS",false, true);
                '''%color)
        pass

    def do_removeformat(self, *args):
        '''清除格式
        '''
        #print 'WebKitEdit.do_removeformat:'
        self.execute_script(''' 
                document.execCommand("removeformat", false, null); ''')
        pass

    def do_justifyleft(self, *args):
        '''左对齐
        '''
        #print 'WebKitEdit.do_justifyleft:'
        self.execute_script(''' 
                document.execCommand("justifyleft", false, null); ''')
        pass

    def do_justifycenter(self, *args):
        '''居中
        '''
        #print 'WebKitEdit.do_justifycenter:'
        self.execute_script('''
                document.execCommand("justifycenter", false, null); ''')
        pass

    def do_justifyfull(self, *args):
        '''分散对齐
        '''
        #print 'WebKitEdit.do_justifycenter:'
        self.execute_script(''' 
                document.execCommand("justifyfull", false, null); ''')
        pass

    def do_justifyright(self, *args):
        '''右对齐
        '''
        #print 'WebKitEdit.do_justifyright:'
        self.execute_script(''' 
                document.execCommand("justifyright", false, null); ''')
        pass

    def do_indent(self, *args):
        '''增大缩进
        '''
        #print 'WebKitEdit.do_indent:'
        self.execute_script(''' 
                document.execCommand("indent", false, null); ''')
        pass

    def do_outdent(self, *args):
        '''减小缩进
        '''
        #print 'WebKitEdit.do_outdent:'
        self.execute_script(''' 
                document.execCommand("outdent", false, null); ''')
        pass

    def do_subscript(self, *args):
        '''下标
        '''
        #print 'WebKitEdit.do_subscript:'
        self.execute_script(''' 
                document.execCommand("subscript", false, null); ''')
        pass

    def do_superscript(self, *args):
        '''上标
        '''
        #print 'WebKitEdit.do_subperscript:'
        self.execute_script(''' 
                document.execCommand("superscript", false, null); ''')
        pass

    ##
    def do_find_text(self, findtext):
        '''查找文字
        '''
        self.search_text(findtext, case_sensitive=0, forward=1, wrap=1)
        pass

    def do_find_text_backward(self, findtext):
        '''向上查找文字
        '''
        #print 'WebKitEdit.do_find_text_forward:', findtext,
        self.search_text(findtext, case_sensitive=0, forward=0, wrap=1)
        pass

    def do_replace_text(self, findtext, replacetext):
        '''查找替换文字
        '''
        #print 'WebKitEdit.do_replace_text:'
        if self.eval("document.getSelection().toString();"):
            self.do_insert_text(replacetext)
            return
        elif self.search_text(findtext, case_sensitive=0, forward=1, wrap=1):
            self.do_insert_text(replacetext)
            pass
        pass  

    def do_replace_text_all(self, findtext, replacetext):
        '''全部替换
        '''
        #print 'WebKitEdit.do_replace_text_all'
        # 
        ## 来到页首
        while self.search_text(findtext, case_sensitive=0, forward=0, wrap=0):
            self.do_insert_text(replacetext)
            pass
        ## 向下搜索并替换
        while self.search_text(findtext, case_sensitive=0, forward=1, wrap=0):
            self.do_insert_text(replacetext)
            pass
        return

    def do_highlight_pre(self, *args):
        self.eval(r'''
        var mergePreElements = function(){
            var es = document.getElementsByTagName('pre');
            var first = es.length ?  es[0] : null;
            var ces = [first];
            var jces = []
            for (var i=1; i<es.length; i++){
                e = es[i];
                prev = es[i-1];
                if (e.previousSibling && e.previousSibling.textContent == '\n' && e.previousSibling.previousSibling == prev){
                    ces.push(e);
                } else {
                    first = e;
                    jces.push(ces);
                    ces = [first];
                }
            }
            for (var i=0; i<jces.length; i++){
                ces = jces[i];
                var first = ces[0];
                var txt = '';
                txt += first.innerText;
                for (var t=1; t<ces.length; t++){
                    var e = ces[t];
                    txt += '\n' + e.innerText;
                    e.parentElement.removeChild(e);
                }
                first.innerText = txt;
            }
        };
        mergePreElements();
        var getPres = function(){
            var preIds=[];
            var es = document.getElementsByTagName('pre');
            for (var i=1; i<es.length; i++){
                e = es[i];
                e.id = Math.random().toString(16).slice(2);
                preIds.push([e.id, e.inerText]);
            }
            return preIds;
        };
        getPres();
        ''')
        return

    


if __name__=="__main__":
    #print 'WebKitEdit.main'
    w=Gtk.Window()
    w.connect("delete_event", Gtk.main_quit)
    m=WebKitEdit()
    w.add(m)
    w.show_all()
    Gtk.main()



