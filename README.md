# ipCorePackager

[![Build Status](https://travis-ci.org/Nic30/ipCorePackager.svg?branch=master)](https://travis-ci.org/Nic30/ipCorePackager)
[![CircleCI](https://circleci.com/gh/Nic30/ipCorePackager.svg?style=svg)](https://circleci.com/gh/Nic30/ipCorePackager)
[![Coverage Status](https://coveralls.io/repos/github/Nic30/ipCorePackager/badge.svg?branch=master)](https://coveralls.io/github/Nic30/ipCorePackager?branch=master)
[![PyPI version](https://badge.fury.io/py/ipCorePackager.svg)](http://badge.fury.io/py/ipCorePackager)
[![Documentation Status](https://readthedocs.org/projects/ipcorepackager/badge/?version=latest)](http://ipcorepackager.readthedocs.io/en/latest/?badge=latest)
[![Python version](https://img.shields.io/pypi/pyversions/ipCorePackager.svg)](https://img.shields.io/pypi/pyversions/ipCorePackager.svg)


Scriptable universal IP-Core generator

## Export formats
* [IP-XACT](https://en.wikipedia.org/wiki/IP-XACT) (Vivado)
* Quartus (QSys) *_hw.tcl

## What is IP-Core packager.

IP-Core packager is a tool which generates component.xml or _hw.tcl files which are description of interface of hardware design usually written in Verilog or VHDL. Result is the package with HDL (Verilog/VHDL) files, constraints files (XDC, UCF, ...) tcl based GUI and package description file. IP-Core packages greatly simplifies integration of hardware projects, all major synthesis tools (Xilinx Vivado, Intel Quartus, ...) are supporting them directly and for rest it is better to have IP-Core because of consystency.

## How to use IpCorePackager

IpCorePackager is API for generating of IP-XACT and _hw.tcl files. In order to use the IpCorePackager you need two things.

* You need to have definitions of Interface IP-Core meta for interfaces which require some special care (require to define some parameter in IP-Core, etc.), This meta has to be subclass of [ipCorePackager.intfIpMeta.IntfIpMeta](https://github.com/Nic30/ipCorePackager/blob/master/ipCorePackager/intfIpMeta.py#L19)

* You need to define methods in [ipCorePackager.packager.IpCorePackager](https://github.com/Nic30/ipCorePackager/blob/master/ipCorePackager/packager.py#L142) which are raising the NotImplementedError. This methods are because ipCorePackager does not dependeds on reprenation of design.

This library is used by [hwt](https://github.com/Nic30/hwt) [there](https://github.com/Nic30/hwt/blob/master/hwt/serializer/ip_packager.py) you can find reference implementation of IpCorePackager methods for hwt style hardware description.

The [hwtLib](https://github.com/Nic30/hwtLib) library contains definitions of [IntfIpMeta descriptions](https://github.com/Nic30/hwtLib/blob/master/hwtLib/peripheral/i2c/intf.py#L95) for common interfaces.

## Similar projects

* [Kactus2](https://github.com/Martoni/kactus2) - IP-core packager
* [Qgen](https://github.com/josyb/Qgen) - Quartus ip core packager for MyHDL
* [ipgen](https://github.com/PyHDI/ipgen)
* [ipxact_gen](https://github.com/olofk/ipxact_gen)
* [ipyxact](https://github.com/olofk/ipyxact) - Python-based IP-XACT parser
