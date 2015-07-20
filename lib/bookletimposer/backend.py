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
# backend.py
#
# This file contains backend that should not be part of the pdfimposer
# python module.
#
########################################################################

import pdfimposer
import os.path
import re

class BookletImposerError(pdfimposer.PdfConvError):
    """The base class for all exceptions raised by BookletImposer.

    The attribute "message" contains a message explaining the cause of the
    error.
    """

class MissingInputFileError(BookletImposerError):
    """Excpetion raised when trying to create a converter withot an input file.

    An input file is required to create a converter."
    """

class ConversionType:
    """The conversion type constants"""
    BOOKLETIZE = 1
    """The conversion from a linear document to a booklet"""
    LINEARIZE = 2
    """The conversion from a booklet to a linear document"""
    REDUCE = 3
    """The conversion from multiple input pages to one output page"""

class ConverterPreferences(object):
    def __init__(self):
        self._infile_name = None
        self._conversion_type = None
        self.copy_pages = None
        self.layout = None
        self.paper_format = None
        self.paper_orientation = None
        self.outfile_name = None
        self.__outfile_name_changed = False

    @property
    def infile_name(self):
        return self._infile_name

    @infile_name.setter
    def infile_name(self, value):
        assert value == None or os.path.isfile(value)
        self._infile_name = value
        # XXX: duplicate code with pfdimposer.FileConverter.__set_infile_name
        #      but the least one is called only on FileConverer instanciation
        #      and we need the proposal before to display it in the UI
        if not self.__outfile_name_changed:
            result = re.search("(.+)\.\w*$", value)
            if result:
                self._outfile_name = result.group(1) + '-conv.pdf'
            else:
                self._outfile_name = value + '-conv.pdf'

    @property
    def conversion_type(self):
        return self._conversion_type

    @conversion_type.setter
    def conversion_type(self, value):
        assert value == None or \
               value == ConversionType.BOOKLETIZE or \
               value == ConversionType.LINEARIZE or \
               value == ConversionType.REDUCE
        self._conversion_type = value

    @property
    def copy_pages(self):
        return self._copy_pages

    @copy_pages.setter
    def copy_pages(self, value):
        self._copy_pages = bool(value)

    @property
    def layout(self):
        return self._layout

    @layout.setter
    def layout(self, value):
        # XXX : verify value
        self._layout = value

    @property
    def paper_format(self):
        return self._paper_format

    @paper_format.setter
    def paper_format(self, value):
        # XXX : verify value
        self._paper_format = value

    @property
    def paper_orientation(self):
        return self._paper_orientation

    @paper_orientation.setter
    def paper_orientation(self, value):
        # XXX : verify value
        self._paper_orientation = value

    @property
    def outfile_name(self):
        return self._outfile_name

    @outfile_name.setter
    def outfile_name(self, value):
        assert value == None or \
            not os.path.dirname(value) or \
            os.path.exists(os.path.dirname(value))
        self.__outfile_name_changed = True
        self._outfile_name = value

    def __str__(self):
        string = "ConverterPreferences object:\n"
        if self._infile_name:
            string += "    infile_name: %s\n" % self._infile_name
        if self._infile_name:
            string += "    outfile_name: %s\n" % self._outfile_name
        if self._conversion_type:
            string += "    conversion_type: %s\n" % self._conversion_type
        if self._layout:
            string += "    layout: %s\n" % self._layout
        if self._paper_format:
            string += "    paper_format: %s\n" % self._paper_format
        if self._paper_orientation:
            string += "    paper_orientation: %s\n" % self._paper_orientation
        if self._copy_pages:
            string += "    copy_pages: %s\n" % self._copy_pages
        return string

    def create_converter(self, overwrite_outfile_callback=None):
        if not self._infile_name:
            raise MissingInputFileError
            return None
        elif self._outfile_name:
            converter = TypedFileConverter(self._infile_name, self._outfile_name,
                overwrite_outfile_callback=overwrite_outfile_callback)
        else:
            converter = TypedFileConverter(self._infile_name,
                overwrite_outfile_callback=overwrite_outfile_callback)
        if self._conversion_type: converter.set_conversion_type(self._conversion_type)
        if self._layout: converter.set_layout(self._layout)
        if self._paper_format: converter.set_output_format(self._paper_format)
        if self._paper_orientation:
            converter._set_output_orientation(self._paper_orientation)
        if self._copy_pages: converter.set_copy_pages(self._copy_pages)
        return converter

class TypedFileConverter(pdfimposer.FileConverter):
    """A FileConverter that stores the conversion type.

    """
    def __init__(self,
                 infile_name=None,
                 outfile_name=None,
                 conversion_type=ConversionType.BOOKLETIZE,
                 layout='2x1',
                 format='A4',
                 copy_pages=False,
                 overwrite_outfile_callback=None):

        """Create a TypedFileConverter.

        :Parameters:
          - `infile_name`: The name to the input PDF file.
          - `outfile_name`: The name of the file where the output PDF
            should de written. If ommited, defaults to the
            name of the input PDF postponded by '-conv'.
          - `conversion_type`: The type of the conversion that will be performed
            when caling run() (see set_converston_type).
          - `layout`: The layout of input pages on one output page (see
            set_layout).
          - `format`: The format of the output paper (see set_output_format).
          - `copy_pages`: Wether the same group of input pages shoud be copied
            to fill the corresponding output page or not (see
            set_copy_pages).
        """
        
        pdfimposer.FileConverter.__init__(self, infile_name, outfile_name,
                                         layout, format, copy_pages, overwrite_outfile_callback)
        self._conversion_type = conversion_type

    # CONVERSION FUNCTIONS
    # ====================

    def run(self):
        """Perform the actual conversion.

        This method launches the actual conversion, using the parameters set
        before.
        """
        if self.get_conversion_type() == ConversionType.BOOKLETIZE:
            self.bookletize()
        elif self.get_conversion_type() == ConversionType.LINEARIZE:
            self.linearize()
        elif self.get_conversion_type() == ConversionType.REDUCE:
            self.reduce()

    # GETTERS AND SETTERS SECTION
    # ===========================

    def set_conversion_type(self, type):
        """Set conversion that will be performed when caling run().

        :Parameters:
          - `type`: A constant from the ConversionType class.
        """
        assert(type == ConversionType.BOOKLETIZE or \
               type == ConversionType.LINEARIZE or \
               type == ConversionType.REDUCE)
        self._conversion_type = type

    def get_conversion_type(self):
        """
        Get conversion that will be performed when caling run().

        :Returns:
            A constant from ConversionType class.
        """
        return self._conversion_type


