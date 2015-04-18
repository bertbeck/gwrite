# Build and install as deb pack #

```
  sudo apt-get install mercurial fakeroot devscripts cdbs debhelper python python-support python-distutils-extra mimetex wv python-gobject gir1.2-gtk-3.0 gir1.2-gtksource-3.0 gir1.2-webkit-3.0  gir1.2-gdkpixbuf-2.0
  hg clone https://gwrite.googlecode.com/hg/ gwrite  
  cd gwrite
  debuild -rfakeroot
  cd ..
  sudo dpkg -i gwrite*deb
```