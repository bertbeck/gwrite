#!/usr/bin/python

from distutils.core import setup
from DistUtilsExtra.command import *
from glob import glob

setup(name='gwrite',
      version='0.5.1',
      description='HTML5 Doc Writer based on GTK2',
      long_description ="""GWrite is a simple HTML5 Doc Writer base on Gtk2.

Features include:

   1. HTML Format
   2. Indexes and Tables
   3. Headings order processor
   4. Hyper links
   5. Images resize / scale
   6. Base64 URL scheme inline images
   7. Font size and styles
   8. undo/redo
   9. Inline pixel margin setting on paragraph / span / block attributes
  10. Bullet list / Orderet list
  11. Paste image direct from from other application
  12. Paste html direct from firefox browser image included
  13. Paste excel formated table section copy from openoffice
  14. Paste full html page direct from browser image included       
      """,
      author='Jiahua Huang',
      author_email='jhuangjiahua@gmail.com',
      license='LGPL-3',
      url="http://code.google.com/p/gwrite",
      download_url="http://code.google.com/p/gwrite/downloads/list",
      platforms = ['Linux'],
      scripts=['scripts/gwrite'],
      packages = ['gwrite'], 
      package_data = {'gwrite': ['icons/*']},
      data_files = [
          ('share/pixmaps', ['gwrite.png']),
      ],
      include_data_files = [
          ('.', ['po']),
      ],
      cmdclass = { "build" :  build_extra.build_extra,
                   "build_i18n" :  build_i18n.build_i18n,
                 }
      )
