# 安装 #



# 在 Windows 系安装 #

稍候请朋友帮忙打包 XP 版本。


如果您想要手工安装，可以试试参照下边 Linux 下的方式先行安装 python-gobject gir1.2-gtk-3.0 gir1.2-gtksource-3.0 gir1.2-webkit-3.0  gir1.2-gdkpixbuf-2.0



# 在 Linux 系安装 #

## 以 deb 包格式安装 ##

官方 Ubuntu/Debian 源已经包含了 gwrite 相关包，您可以直接
```
sudo apt-get install gwrite
```
来安装

不过官方源里的包可能会有些旧，所以您也可以选择从 [下载页](http://code.google.com/p/gwrite/downloads/list)点击 deb 包来安装


## 从源码安装 ##

### 依赖 ###

本程序使用了 python-gobject gir1.2-gtk-3.0 gir1.2-gtksource-3.0 gir1.2-webkit-3.0  gir1.2-gdkpixbuf-2.0 几个包，

setup.py 脚本使用了 python-distutils-extra，

所以请您先安装上述几个包


如果您需要在文档中处理 LaTex 数学公式，请再安装 mimetex 这个独立程序


在 Ubuntu/Debian 里边，您可以使用
```
sudo apt-get install mercurial fakeroot devscripts cdbs debhelper python python-distutils-extra mimetex wv python-gobject gir1.2-gtk-3.0 gir1.2-gtksource-3.0 gir1.2-webkit-3.0  gir1.2-gdkpixbuf-2.0
```
来安装所需要的所有包


### 获取源码 ###

本软件在 code.google 使用水银（）来管理源码，

如果您希望获取最新的源码，请安装水银，然后执行
```
    hg clone https://gwrite.googlecode.com/hg/ gwrite  
```

以从水银仓库抓取一份源码


或许您可以先浏览  http://code.google.com/p/gwrite/source/browse/ 以在线查阅源码


### 安装准备 ###

如果您使用的是 python2.6 的 deb 发行版， 由于新版本 python 的路径有所改变，请先执行下命令
```
    sudo mv /usr/lib/python2.6/site-packages/* /usr/lib/python2.6/dist-packages/
    sudo rmdir /usr/lib/python2.6/site-packages/
    sudo ln -sf dist-packages /usr/lib/python2.6/site-packages/
```
以便修正兼容的 python 路径

### 常规安装 ###

软件采用标准的 python distutils 安装方式，
您可以如同其他 Python 软件一样在源码目录下执行
```
    ./setup build
    sudo ./setup.py install
```
来安装他

### 打包为 deb ###

或者您可以先打包为 deb 再安装，可以在源码目录执行
```
debuild -rfakeroot
```


## 从最新的源码生成 deb 包来安装 ##

如果您使用的是 Ubuntu/Debian，也许会希望将最新的源码打包为 deb 再安装，以便统一包管理

```
  sudo apt-get install mercurial fakeroot devscripts cdbs debhelper python python-support python-setuptools python-distutils-extra python-jswebkit mimetex
  hg clone https://gwrite.googlecode.com/hg/ gwrite  
  cd gwrite
  debuild -rfakeroot
  cd ..
  sudo dpkg -i *deb
```


# 执行 #

安装完毕，您可以在 开始菜单，应用程序，附件 里边 找到 ［写字板］， 点击即可执行本软件。

或者您也可以直接执行 gwrite 来启动。

在 软件菜单：编辑，首选项 里边，可以选择不同的运行模式。