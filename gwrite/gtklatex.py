#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''Gtk LaTex
@author: U{Jiahua Huang <jhuangjiahua@gmail.com>}
@license: LGPLv3+
'''

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import GdkPixbuf

import thread
import time
import subprocess

import os, sys
import base64

try: from gi.repository import GtkSource
except: GtkSource = None

try: import i18n
except: from gettext import gettext as _

latex_mark_list = [
#    ["+",            r" + "],
#    ["<big>-</big>", r" - "],
    ["<b>⋅</b>",     r" \cdot "],
    ["x",            r" \times "],
    ["/",            r" / "],
    ["<big><b>÷</b></big>", r" \frac { } { }"],

    ["a<sup>n</sup>",     r"^{%s}"],
    ["a<sub>n</sub>",     r"_{%s}"],

    [" ≠ ",   r" \neq "],
    [" ≤ ",   r" \le "],
    [" ≥ ",   r" \ge "],
    [" ≡ ",   r" \equiv "],

    [" ≪ ",   r" \ll "],
    [" ≫ ",   r" \gg "],
    [" ≃ ",    r" \simeq "],
    [" ≈ ",   r" \approx "],

    ["√¯",    r" \sqrt[] {%s}"],
    ["∫",     r" \int^{}_{} "],
    ["∬",     r" \iint^{}_{} "],
    ["∮",     r" \oint^{}_{} "],
    ["[ ]",    r"\[ %s \]"],
    ["( )",    r"\( %s \)"],
    ["{ }",    r"\{ %s \}"],
    ["[≡]",    r"""
\[
   \begin{matrix}
       a & b & c\\
       c & e & f
   \end{matrix}
\]
"""],
    ["(≡)",    r"""    
   \begin{pmatrix}
       a & b & c\\
       c & e & f
   \end{pmatrix}
"""],

    ["(<big> : </big>)",    r"{ } \choose { } "],
    ["<big>(</big> x <big>)</big>",         r"\left( { %s } \right)"],

    [" ± ",   r" \pm "],
    [" ∓ ",    r" \mp "],
    [" ∨ ",   r" \lor" ],
    [" ∧ ",   r" \land "],

    ["mod",    r" \bmod "],
    [" ∼ ",   r" \sim "],
    ["∥ ",    r" \parallel "],
    [" ⊥ ",   r" \perp "],
    ["<big><big>∞</big></big>",     r" \infty "],

    ["∠",     r" \angle "],
    ["<big><b>△</b></big>",     r" \triangle "],
    ["∑",     r" \sum_{ }^{ } "],
    ["lim",    r"\lim_{  }"],
    ["⇒",     r" \Rightarrow "],
    ["⇔",     r" \Leftrightarrow "],
    ["∧",     r" \wedge "],
    ["∨",     r" \vee "],
    ["¬",      r" \neg "],
    ["∀",     r" \forall "],
    ["∃",     r" \exists "],
    ["∅",      r" \varnothing "],
    ["∈",     r" \in "],
    ["∉",      r" \notin "],
    ["⊆",     r" \subseteq "],
    ["⊂",     r" \subset "],
    ["∪",     r" \cup "],
    ["⋂",      r" \cap "],
    ["→",     r" \to "],
    ["↦",      r" \mapsto "],
    ["∏",     r" \prod "],
    ["○",     r" \circ "],

    ["sin",    r" \sin "],
    ["cos",    r" \cos "],
    ["tan",    r" \tan "],
    ["ctan",   r" \ctab "],
    ["asin",   r" \asin "],
    ["acos",   r" \acos "],
    ["atan",   r" \atan "],
    ["actan",  r" \actan "],
    ["log",    r" \log "],
    ["ln",     r" \ln "],

    ["...",                       r" \cdots "],
    [" <sub>...</sub> ",          r" \ldots "],
    ["<big>⁝</big>",              r" \vdots "],
    ["<sup>.</sup>.<sub>.</sub>", r" \ddots "],

    ["α",     r" \alpha "],
    ["β",     r" \beta "],
    ["Γ",     r" \Gamma "],
    ["γ",     r" \gamma "],
    ["Δ",     r" \Delta "],
    ["δ",     r" \delta "],
    ["ϵ",      r" \epsilon "],
    ["ε",     r" \varepsilon "],
    ["ζ",     r" \zeta "],
    ["η",     r" \eta "],
    ["Θ",     r" \Theta "],
    ["θ",     r" \theta "],
    ["ϑ",      r" \vartheta "],
    ["ι",     r" \iota "],
    ["κ",     r" \kappa "],
    ["Λ",     r" \Lambda "],
    ["λ",     r" \lambda "],
    ["μ",     r" \mu "],
    ["ν",     r" \nu "],
    ["Ξ",     r" \Xi "],
    ["ξ",     r" \xi "],
    ["Π",     r" \Pi "],
    ["π",     r" \pi "],
    ["ϖ",      r" \varpi "],
    ["ρ",     r" \rho "],
    ["ϱ",      r" \varrho "],
    ["Σ",     r" \Sigma "],
    ["σ",     r" \sigma "],
    ["ς",      r" \varsigma "],
    ["τ",     r" \tau "],
    ["Υ",     r" \Upsilon "],
    ["υ",     r" \upsilon "],
    ["Φ",     r" \Phi "],
    ["ϕ",      r" \phi "],
    ["φ",     r" \varphi "],
    ["χ",     r" \chi "],
    ["Ψ",     r" \Psi "],
    ["ψ",     r" \psi "],
    ["Ω",     r" \Omega "],
    ["ω",     r" \omega "],
]

class GtkToolBoxView(Gtk.TextView):
    '''流式布局 ToolBox
    '''
    def __init__(self, latex=""):
        '''初始化
        '''
        Gtk.TextView.__init__(self)
        self.props.can_focus = 0
        self.set_editable(0)
        self.set_wrap_mode(Gtk.WrapMode.WORD)
        self.connect('realize', self.on_realize)
        pass

    def on_realize(self, *args):
        ## 将默认 I 形鼠标指针换成箭头
        self.get_window(Gtk.TextWindowType.TEXT).set_cursor(Gdk.Cursor(Gdk.CursorType.ARROW))
        pass

    def add(self, widget):
        '''插入 Widget
        '''
        buffer = self.get_buffer()
        iter = buffer.get_end_iter()
        anchor = buffer.create_child_anchor(iter)
        buffer.insert(iter, "")
        #widget.set_data('buffer_anchor', anchor)
        widget.buffer_anchor = anchor
        self.add_child_at_anchor(widget, anchor)
        pass

    def remove(self, widget):
        '''删除 widget
        '''
        anchor = widget.get_data('buffer_anchor')
        if anchor:
            buffer = self.get_buffer()
            start = buffer.get_iter_at_child_anchor(anchor)
            end = buffer.get_iter_at_offset( start.get_offset() + 1 )
            buffer.delete(start, end)
            pass
        pass

class LatexMathExpressionsEditor(Gtk.Table):
    '''LaTex 数学公式编辑器
    '''
    def __init__(self, latex=""):
        '''初始化
        '''
        Gtk.Table.__init__(self)
        self.set_row_spacings(10)
        self.set_col_spacings(10)
        ## latex edit
        scrolledwindow1 = Gtk.ScrolledWindow()
        scrolledwindow1.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolledwindow1.show()
        scrolledwindow1.set_shadow_type(Gtk.ShadowType.IN)

        if GtkSource:
            self.latex_textview = GtkSource.View()
            lm = GtkSource.LanguageManager.get_default()
            language = lm.get_language('latex')
            buffer = GtkSource.Buffer()
            buffer.set_highlight_syntax(1)
            buffer.set_language(language)
            self.latex_textview.set_buffer(buffer)
            pass
        else:
            self.latex_textview = Gtk.TextView()
            pass
        self.latex_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.latex_textview.set_cursor_visible(True)
        self.latex_textview.set_indent(5)
        self.latex_textview.set_editable(True)
        self.latex_textview.show()
        #self.latex_textview.set_size_request(302, 200)
        buffer = self.latex_textview.get_buffer()
        buffer.set_text(latex)
        scrolledwindow1.add(self.latex_textview)

        self.attach(scrolledwindow1, 0, 1, 0, 1)
        ## latex preview
        self.latex_image = Gtk.Image()
        #self.latex_image.set_size_request(200, 100)
        self.latex_image.set_padding(0, 0)
        self.latex_image.show()

        box = Gtk.EventBox()
        box.show()
        box.modify_bg(Gtk.StateType.NORMAL, Gdk.Color.parse("#FFFFFF")[1])
        box.add(self.latex_image)
        
        self.attach(box, 0, 1, 1, 2)
        ## toolbox
        toolview = GtkToolBoxView()
        toolview.show()
        #toolview.set_size_request(302, 200)
        for text, mark in latex_mark_list:
            label = Gtk.Label()
            label.set_markup(text)
            label.set_size_request(30, 20)
            label.show()
            button = Gtk.Button()
            button.props.can_focus = 0
            button.add(label)
            button.set_relief(Gtk.ReliefStyle.NONE)
            button.connect("clicked", self.on_insert_tex_mark, text, mark)
            button.set_tooltip_text(mark)
            button.show()
            toolview.add(button)
            pass
        scrolledwindow2 = Gtk.ScrolledWindow()
        #scrolledwindow2.set_size_request(300, 400)
        scrolledwindow2.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolledwindow2.show()
        scrolledwindow2.set_shadow_type(Gtk.ShadowType.IN)
        scrolledwindow2.add(toolview)
        self.attach(scrolledwindow2, 1, 2, 0, 2)

        self.show_all()

        thread.start_new_thread(self._up_preview, ())
        pass

    def get_latex(self, *args):
        '''获取 LaTex
        '''
        buffer = self.latex_textview.get_buffer()
        return buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter(), 1)

    def set_pic(self, data):
        '''设置图像
        '''
        if not data:
            return self.latex_image.set_from_stock(Gtk.STOCK_DIALOG_ERROR, 2)
        pix = GdkPixbuf.PixbufLoader()
        pix.write(data)
        pix.close()
        self.latex_image.set_from_pixbuf(pix.get_pixbuf())
        return

    def _up_preview(self, *args):
        '''用于定时更新预览
        '''
        old_latex = ""
        while True:
            time.sleep(1)
            if not self.get_window():
                break
            latex = self.get_latex()
            if latex == old_latex:
                continue
            pic = tex2gif(latex, 1)
            old_latex = self.get_latex()
            if latex == self.get_latex():
                GObject.idle_add(self.set_pic, pic)
                pass
            pass
        #-print 'done'
        return

    def up_preview(self, pic):
        '''更新预览'''
        return

    def insert_latex_mark(self, view, mark, text=""):
        '''在 Gtk.TextView 插入 LaTex 标记
        '''
        buffer = view.get_buffer()
        bounds = buffer.get_selection_bounds()
        select = bounds and buffer.get_slice(bounds[0], bounds[1]) or text
        if mark.count("%") == 1:
            mark = mark % select
            pass
        else:
            mark = mark + select
            pass
        buffer.delete_selection(1, 1)
        buffer.insert_at_cursor(mark)
        pass

    def on_insert_tex_mark(self, widget, text, mark):
        print 'on_insert_tex_mark:', text, mark
        self.insert_latex_mark(self.latex_textview, mark)
        pass

def latex_dlg(latex="", title=_("LaTeX math expressions"), parent=None):
    dlg = Gtk.Dialog(title, parent, Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK    ))
    dlg.set_default_size(680, 400)
    editor = LatexMathExpressionsEditor(latex)
    dlg.vbox.pack_start(editor, True, True, 5)
    dlg.show_all()
    resp = dlg.run()
    latex = editor.get_latex()
    dlg.destroy()
    if resp == Gtk.ResponseType.OK:
        return latex
    return None    

def stastr(stri):
    '''处理字符串的  '   "
    '''
    return stri.replace("\\","\\\\").replace(r'"',r'\"').replace(r"'",r"\'").replace('\n',r'\n')

def tex2gif(tex, transparent=1):
    '''将 latex 数学公式转为 gif 图片，依赖 mimetex

    mimetex -d -s 7 '公式'
    '''
    if transparent: 
        cmd = ['mimetex', '-d', '-s', '4', tex]
        pass
    else:
        cmd = ['mimetex', '-d', '-o', '-s', '4', tex]
        pass
    i = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    gif = i.communicate()[0]
    if gif.startswith('GIF'):
        return gif
    return ""

def gif2base64(gif):
    '''将 gif 图像转为 base64 内联图像
    '''
    return 'data:image/gif;base64,%s' % base64.encodestring(gif).replace('\n', '')

def tex2base64(tex):
    '''将 latex 数学公式转为 base64 内联图像
    '''
    return gif2base64(tex2gif(tex))

def tex2html(tex):
    '''将 latex 数学公式转为 base64 内联图像
    '''
    return '<img alt="mimetex:%s" onDblClick="if(uptex) uptex(this);" style="vertical-align: middle; position: relative; top: -5pt; border: 0;" src="%s" />' % (stastr(tex), gif2base64(tex2gif(tex)))


if __name__=="__main__":
    Gdk.threads_init()
    latex = ' '.join(sys.argv[1:]) or 'E=MC^2'
    latex = latex_dlg(latex)
    print latex
    #print tex2html(latex)
    pass


