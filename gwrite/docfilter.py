#!/usr/bin/python
# -*- coding: UTF-8 -*-
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# Author: Huang Jiahua <jhuangjiahua@gmail.com>
# License: LGPLv3+
# Last modified:

'''文档格式转换
'''

import os

def doc2html(docfile):
    '''将 mso doc 转换为 html
    依赖 wv
    '''
    dir = os.tmpnam().replace('file', 'gwrite-%s/file' % os.getlogin() )
    html = 'gwrite.html'
    os.makedirs(dir)
    i, o = os.popen2(['wvHtml', '--targetdir=%s'%dir, docfile, html])
    o.read()
    return dir + '/' + html

