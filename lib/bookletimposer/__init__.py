#!/usr/bin/env python
# -*- coding: UTF-8 -*-

########################################################################
# 
# PdfImposer - Utility to convert PDF files between diffrents page layouts
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
# __init__.py
#
# This file contains bookletimposer package initialisation code.
#
########################################################################

import gettext
import locale
import config

locale.setlocale(locale.LC_ALL, '')
locale.bindtextdomain("bookletimposer", config.get_localedir())
gettext.install("bookletimposer", localedir=config.get_localedir(), unicode=True)
