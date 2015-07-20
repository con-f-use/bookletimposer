#!/usr/bin/env python
# -*- coding: UTF-8 -*-

########################################################################
# 
# BookletImposer - Utility to achieve some basic imposition on PDF documents
# Copyright (C) 2008-2012 Kjö Hansi Glaz <kjo@a4nancy.net.eu.org>
# 
# This program is  free software; you can redistribute  it and/or modify
# it under the  terms of the GNU General Public  License as published by
# the Free Software Foundation; either  version 3 of the License, or (at
# your option) any later version.
# 
# This program  is distributed in the  hope that it will  be useful, but
# WITHOUT   ANY  WARRANTY;   without  even   the  implied   warranty  of
# MERCHANTABILITY  or FITNESS  FOR A  PARTICULAR PURPOSE.   See  the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################

########################################################################
#
# config.py
#
# This file contains the configuration variables defined at install time
# which will be used somewhere in the program.
#
########################################################################

import gettext
import locale
import os.path

def debug(msg):
    if __debug__: print msg

def get_sharedir():
    if os.path.exists(os.path.join("/", "usr", "local", "share",
            "bookletimposer")):
        return os.path.join("/", "usr", "local", "share")
    elif os.path.exists(os.path.join("/", "usr", "share", "bookletimposer")):
        return os.path.join("/", "usr", "share")
    else:
        return ""

def get_datadir():
    if __debug__ and os.path.exists("data"):
        return "data"
    else:
        return os.path.join(get_sharedir(), "bookletimposer")

def get_helpdir():
    return os.path.join(get_sharedir(), "gnome", "help")

def get_localedir():
    return os.path.join(get_sharedir(), "locale")
