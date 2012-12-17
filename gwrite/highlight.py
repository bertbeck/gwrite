#!/usr/bin/python
# -*- coding: UTF-8 -*-
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
'''html highlight source code
@author: Jiahua Huang <jhuangjiahua@gmail.com>
@license: LGPLv3+
'''

try:
    import pygments
    import pygments.lexers
    import pygments.formatters
    pass
except:
    pygments = None
    pass


def highlight(src):
    global pygments
    if pygments:
        formatter = pygments.formatters.HtmlFormatter(noclasses=1, nowrap=1, encoding='utf8', style='colorful')
        lex = pygments.lexers.guess_lexer(src)
        return pygments.highlight(src, lex, formatter)
    else:
        return src

if __name__=="__main__":
    import sys
    src = sys.stdin.read()
    print highlight(src)
