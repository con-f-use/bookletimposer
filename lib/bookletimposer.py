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
# bookletimposer
#
# This file is the main program of bookletimposer
#
# It contains the CLI frontend of bookletimposer, which can either work
# standalone or launch the GTK2+ frontend.
#
########################################################################

import optparse
import gettext

if __debug__:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.getcwd(), "lib"))

import pdfimposer # We need its exceptions

import bookletimposer.gui as gui
import bookletimposer.backend as backend
import bookletimposer.config as config

gettext.install("bookletimposer", localedir=config.get_localedir(), unicode=True)

__version__ = "0.2"

def main():
    """
    This is the function that launches the program
    """
    
    infile = None
    
    parser = optparse.OptionParser(
        usage="%prog [options] [infile]",
        version="%prog " + __version__)
    parser.add_option ("-o", "--output", dest="outfile",
        help=_("output PDF file"))
    parser.add_option ("-a", "--no-gui", 
        action="store_false", dest="gui",
        default=True,
        help=_("automatic converstion (don't show the user interface). At least input file must be defined"))
    parser.add_option ("-i", "--gui", 
        action="store_true", dest="gui",
        default=True,
        help=_("shows the user interface (default)."))
    parser.add_option ("-b", "--booklet",
        action="store_const", dest="conv_type", 
        const=backend.ConversionType.BOOKLETIZE, default=backend.ConversionType.BOOKLETIZE,
        help=_("makes a booklet"))
    parser.add_option ("-l", "--linearize",
        action="store_const", dest="conv_type", 
        const=backend.ConversionType.LINEARIZE, default=backend.ConversionType.BOOKLETIZE,
        help=_("convert a booklet to single pages"))
    parser.add_option ("-n", "--no-reorganisation",
        action="store_const", dest="conv_type", 
        const=backend.ConversionType.REDUCE, default=backend.ConversionType.BOOKLETIZE,
        help=_("don't do any reorganisation (will only scale and assemble pages)"))
    parser.add_option ("-c", "--copy-pages",
        action="store_true", dest="copy_pages",
        default=False,
        help=_("Copy the same group of input pages on one output page"))
    parser.add_option ("-p", "--pages-per-sheet", 
        dest="pages_per_sheet", 
        default="2x1", 
        help=_("number of pages per sheet, in the format HORIZONTALxVERTICAL, e.g. 2x1"))
    parser.add_option ("-f", "--format", 
        dest="output_format", 
        default=None,
        help=_("output page format, e.g. A4 or A3R"))
    parser.add_option ("-k", "--keep",
        action="store_false", dest="overwrite",
        default=True,
        help=_("do not overwrite output file if it exists"))
    
    (options, args) = parser.parse_args()
    
    if len(args) >= 1:
        infile = args[0]
    
    preferences = backend.ConverterPreferences()
        
    if infile:
        preferences.infile_name = infile
    if options.outfile:
        preferences.outfile_name = options.outfile
    if options.conv_type:
        preferences.conversion_type = options.conv_type
    if options.output_format:
        preferences.paper_format = options.output_format
    if options.pages_per_sheet:
        preferences.layout = options.pages_per_sheet
    if options.copy_pages:
        preferences.copy_pages = True
    
    if options.gui:
        ui = gui.BookletImposerUI(preferences)
        gui.Gtk.main()
    else:
        if not preferences.infile_name:
            print _("ERROR: In automatic mode, you must provide a file to process.")
            return
        def overwrite_callback(filename):
            return options.overwrite
        try:
            converter = preferences.create_converter(overwrite_callback)
        except pdfimposer.UserInterruptError:
            return
        def progress_callback(message, progress):
            print(_("%i%%: %s") % (progress*100, message))
        converter.set_progress_callback(progress_callback)
        converter.run()
    return 0 
    
if __name__ == "__main__":
    main()
