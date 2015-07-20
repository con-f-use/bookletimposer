#!/usr/bin/env python
# -*- coding: UTF-8 -*-

########################################################################
# 
# pdfimposer - achieve some basic imposition on PDF documents
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
# pdfimposer.py
#
# This python module enables to change PDF page layout. It is the backend
# of BookletImposer, but is designed to be easily usable by from any python
# script.
#
########################################################################

"""
Converts PDF documents between different page layouts.

This module enables to:
 - convert linear (page by page) PDF documents to booklets;
 - revert booklets to linear documents;
 - reduce multiple input PDF pages and put them on one single output page.

The `StreamConverter` class works on StreamIO, while the `FileConverter`
class works on files.

Some convenience functions are also provided.
"""
# XXX: File should be ASCII

from abc import ABCMeta, abstractmethod

import re
import sys
import os
import types

import pyPdf
import pyPdf.generic
import pyPdf.pdf

# XXX: Fix these translatable strings
try:
    _
except NameError:
    _ = lambda x: x

__docformat__ = "restructuredtext"

########################################################################

# CONSTANTS

class PageOrientation:
    """The page orientation constants"""
    PORTRAIT = False
    """The portrait orientation"""
    LANDSCAPE = True
    """The lanscape orientation"""

########################################################################

class PdfConvError(Exception):
    """
    The base class for all exceptions raised by PdfImposer.

    The attribute "message" contains a message explaining the cause of the
    error.
    """
    def __init__(self, message=None):
        Exception.__init__(self)
        self.message = message

########################################################################

class MismachingOrientationsError(PdfConvError):
    """
    This exception is raised if the required layout is incompatible with
    the input page orientation.

    The attribute "message" contains the problematic layout.
    """
    def __str__(self):
        return _("The layout %s is incompatible with the input page orientation") \
            % self.message

########################################################################

class UnknownFormatError(PdfConvError):
    """
    This exception is raised when the user tries to set an unknown page
    format.

    The attribute "message" contains the problematic format.
    """
    def __str__(self):
        return _('The page format "%s" is unknown') % self.message

########################################################################


class UserInterruptError(PdfConvError):
    """
    This exception is raised when the user interrupts the conversion.
    """
    def __str__(self):
        return _('User interruption') % self.message

########################################################################

class AbstractConverter(object):
    """
    The base class for all pdfimposer converter classes.

    It is an abstract class, with some abstract functions which should be
    overriden :
    - get_input_height
    - get_input_width
    - get_page_count
    - bookletize
    - linearize
    - reduce
    """
    __metaclass__ = ABCMeta

    page_formats = {
        "A3":(841,1190),
        "A3":(842,1192),
        "A4":(595,841),
        "A4":(595,842),
        "A5":(420,595), 
        }

    def __init__(self, 
                 layout='2x1',
                 format='A4',
                 copy_pages=False):
        """
        Create an AbstractConverter instance.

        :Parameters:
          - `layout` The layout of input pages on one output page
            (see set_layout).
          - `format` The format of the output paper (see
            set_output_format).
          - `copy_pages` Wether the same group of input pages
            shoud be copied to fill the corresponding output page or not
            (see set_copy_pages).
        """
        self.layout = None
        self.output_format = None
        self.output_orientation = None

        self.set_layout(layout)
        self.set_output_format(format)
        self.set_copy_pages(copy_pages)

        def default_progress_callback(msg, prog):
            print "%s (%i%%)" % (msg, prog*100)

        self.set_progress_callback(default_progress_callback)

    # GETTERS AND SETTERS
    # ===================

    def set_output_height(self, height):
        """
        Set the height of the output page.

        :Parameters:
          - `height` The height of the output page in defalut user
            space units.
        """
        self.__output_height = int(height)

    def get_output_height(self):
        """
        Get the height of the output page.

        :Returns:
            The height of the output page in defalut user space units.
        """
        return self.__output_height

    def set_output_width(self, width):
        """
        Set the width of the output page.

          - `width` The height of the output page in defalut user space units.
        """
        self.__output_width = int(width)

    def get_output_width(self):
        """
        Get the width of the output page.

        :Returns:
            The width of the output page in defalut user space units.
        """
        return self.__output_width

    def set_pages_in_width(self, num):
        """
        Set the number of input pages to put in the width on one output page.

        :Parameters:
          - `num` An integer representing the number of pages in width.
        """
        self.__pages_in_width = int(num)

    def get_pages_in_width(self):
        """
        Get the number of input pages to put in the width on one output page.

        :Returns:
            An integer representing the number of pages in width.
        """
        return self.__pages_in_width

    def set_pages_in_height(self, num):
        """
        Set the number of input pages to put in the height on one output page.

        :Parameters:
          - `num` An integer representing the number of pages in height.
        """
        self.__pages_in_height = int(num)

    def get_pages_in_height(self):
        """
        Get the number of input pages to put in the height on one output page.

        :Returns:
            An integer representing the number of pages in height.
        """
        return self.__pages_in_height

    def set_copy_pages(self, copy_pages):
        """
        Set wether the same group of input pages shoud be copied to fill the
        corresponding output page or not.

        :Parameters:
          - `copy_pages` True to get copies of the same group of input page
            on one output page. False to get diffrent groups of
            input pages on one output page.
        """
        self.__copy_pages = bool(copy_pages)

    def get_copy_pages(self):
        """
        Get wether the same group of input pages will be copied to fill the
        corresponding output page or not.

        :Returns:
            True if copies of the same group of input page will get
            copied on one output page. False if diffrent groups of
            input pages will go on one output page.
        """
        return self.__copy_pages

    def set_progress_callback(self, progress_callback):
        """
        Register a progress callback function.

        Register a callback function that will be called to inform on the
        progress of the conversion.

        :Parameters:
          - `progress_callback` The callback function which is called to
            return the conversion progress. Its signature
            must be : a string for the progress message;
            a number in the range [0, 1] for the progress.
        """
        assert(type(progress_callback) is types.FunctionType)
        self.__progress_callback = progress_callback

    def get_progress_callback(self):
        """
        Get the progress callback function.

        Get the callback function that will be called to inform on the
        progress of the conversion.

        :Returns:
            The callback function which is called to
            return the conversion progress.
        """
        return self.__progress_callback

    # SOME GETTERS THAT CALCULATE THE VALUE THEY RETURN FROM OTHER VALUES
    # ===================================================================
    def get_input_size(self):
        """
        Return the page size of the input document.

        :Returns:
            A tuple (width, height) representing the page size of
            the input document expressed in default user space units.
        """
        return (self.get_input_width(), self.get_input_height())

    @abstractmethod
    def get_input_height(self):
        """
        Return the page height of the input document.

        :Returns:
            The page height of the input document expressed in default
            user space units.
        """
        raise NotImplementedError("get_input_height must be implemented in a subclass.")

    @abstractmethod
    def get_input_width(self):
        """
        Return the page width of the input document.

        :Returns:
            The page width of the input document expressed in default
            user space units.
        """
        raise NotImplementedError("get_input_width must be implemented in a subclass.")

    def get_input_orientation(self):
        """
        Return the page orientation of the input document.

        :Returns:
            A constant from PageOrientation, or None (if square paper).
        """
        if self.get_input_height() > self.get_input_width():
            return PageOrientation.PORTRAIT
        elif self.get_input_height() < self.get_input_width():
            return PageOrientation.LANDSCAPE
        else:
            #XXX: is square
            return None

    def set_layout(self, layout):
        """
        Set the layout of input pages on one output page.

        :Parameters:
          - `layout` A string of the form WxH, where W is the number of input
            pages to put on the width of the output page and H is
            the number of input pages to put in the height of an
            output page.
        """
        pages_in_width, pages_in_height = layout.split('x')
        self.set_pages_in_width(int(pages_in_width))
        self.set_pages_in_height(int(pages_in_height))

    def get_layout(self):
        """
        Return the layout of input pages on one output page.

        :Returns:
            A string of the form WxH, where W is the number of input pages
            to put on the width of the output page and H is the number of
            input pages to put in the height of an output page.
        """
        return str(self.get_pages_in_width()) + 'x' + str(self.get_pages_in_height())

    def get_pages_in_sheet(self):
        """
        Calculate the number of input page that will be put on one output page.

        :Returns:
            An integer representing the number of input pages on one
            output page.
        """
        return self.get_pages_in_width() * self.get_pages_in_height()

    def set_output_format(self, format):
        """
        Set the format of the output paper.

        :Parameters:
          - `format` A string representing name ot the the desired paper
            format, among the keys of page_formats (e.g. A3, A4, A5).

        :Raises UnknonwFormatError: if the given paper format is not recognized.
        """
        try:
            width, height = AbstractConverter.page_formats[format]
            self.set_output_height(height)
            self.set_output_width(width)
        except KeyError:
            raise UnknownFormatError(format)

    def get_output_format(self):
        """
        Return the format of the output paper.

        :Returns:
            A string representing the name of the paper format
            (e.g. A3, A4, A5).
        """
        for output_format in AbstractConverter.page_formats.keys():
            if AbstractConverter.page_formats[output_format] == \
                (self.get_output_width, self.get_output_height):
                return output_format

    def get_input_format(self):
        """
        Return the format of the input paper

        :Returns:
            A string representing the name of the paper format
            (e.g. A3, A4, A5).
        """
        width, height = self.get_input_size()
        if self.get_input_orientation() == PageOrientation.LANDSCAPE:
            size = height, width
        else:
            size = width, height
        for k in self.page_formats.keys():
            if self.page_formats[k] == size:
                return k

    @abstractmethod
    def get_page_count(self):
        """
        Return the number of pages of the input document.

        :Returns:
            The number of pages of the input document.
        """
        raise NotImplementedError("get_page_count must be implemented in a subclass.")

    def get_reduction_factor(self):
        """
        Calculate the reduction factor.

        :Returns:
            The reduction factor to be applied to an input page to
            obtain its size on the output page.
        """
        return float(self.get_output_width()) / \
            (self.get_pages_in_width() * self.get_input_width())

    def get_increasing_factor(self):
        """
        Calculate the increasing factor.

        :Returns:
            The increasing factor to be applied to an input page to
            obtain its size on the output page.
        """
        return float(self.get_pages_in_width() * self.get_output_width()) / \
            self.get_input_width()

    def _set_output_orientation(self, output_orientation):
        """
        Set the orientation of the output paper.

        WARNING: in the current implementation, the orientation of the
        output paper may be automatically adjusted, even if ti was set
        manually.

        :Parameters:
          - `output_orientation` A constant from PageOrientation,
            or None (if square paper).
        """
        output_orientation = bool(output_orientation)

        w = self.get_output_width()
        h = self.get_output_height()

        if (output_orientation == PageOrientation.PORTRAIT and w > h) or \
           (output_orientation == PageOrientation.LANDSCAPE and h > w):
            self.set_output_height(w)
            self.set_output_width(h)

    def _get_output_orientation(self):
        """
        Return the orientation of the output paper.

        WARNING: in the current implementation, the orientation of the
        output paper may be automatically adjusted, even if it was set
        manually.

        :Returns:
            A constant among from PageOrientation, or None (if square paper).
        """
        if self.get_output_height() > self.get_output_width():
            return PageOrientation.PORTRAIT
        elif self.get_output_height() < self.get_output_width():
            return PageOrientation.LANDSCAPE
        else:
            return None

    # CONVERSION FUNCTIONS
    # ====================

    @abstractmethod
    def bookletize(self):
        """
        Convert a linear document to a booklet.

        Convert a linear document to a booklet, arranging the pages as
        required.
        """
        raise NotImplementedError("bookletize must be implemented in a subclass.")

    @abstractmethod
    def linearize(self):
        """
        Convert a booklet to a linear document.

        Convert a booklet to a linear document, arranging the pages as
        required.
        """
        raise NotImplementedError("linearize must be implemented in a subclass.")

    @abstractmethod
    def reduce(self):
        """
        Put multiple input pages on one output page.
        """
        raise NotImplementedError("reduce must be implemented in a subclass.")

########################################################################

class StreamConverter(AbstractConverter):
    """
    This class performs conversions on file-like objects (e.g. a StreamIO).
    """

    def __init__(self,
                 input_stream, 
                 output_stream,
                 layout='2x1',
                 format='A4',
                 copy_pages=False):
        """
        Create a StreamConverter.

        :Parameters:
          - `input_stream` The file-like object from which tne input PDF
            document should be read.
          - `output_stream` The file-like object to which tne output PDF
            document should be written.
          - `layout` The layout of input pages on one output page (see
            set_layout).
          - `format` The format of the output paper (see set_output_format).
          - `copy_pages` Wether the same group of input pages shoud be copied
            to fill the corresponding output page or not (see
            set_copy_pages).
        """

        AbstractConverter.__init__(self, layout, format, 
                                   copy_pages)

        

        self._output_stream = output_stream
        self._input_stream = input_stream

        self._inpdf = pyPdf.PdfFileReader(input_stream)

    def get_input_height(self):
        page = self._inpdf.getPage(0)
        height = page.mediaBox.getHeight()
        return int(height)

    def get_input_width(self):
        page = self._inpdf.getPage(0)
        width = page.mediaBox.getWidth()
        return int(width)

    def get_page_count(self):
        return self._inpdf.getNumPages()

    def __fix_page_orientation(self, cmp):
        """
        Adapt the output page orientation.

        :Parameters:
          - `cmp` A comparator function. Takes: number of pages on one
            direction (int), number of pages on the other direction
            (int). Must return: the boolean result of the comparaison.

        :Raises MismachingOrientationsError: if the required layout is
            incompatible with the input page orientation.
        """
        if cmp(self.get_pages_in_width(), self.get_pages_in_height()):
            if self.get_input_orientation() == PageOrientation.PORTRAIT:
                if self._get_output_orientation() == PageOrientation.PORTRAIT:
                    self._set_output_orientation(PageOrientation.LANDSCAPE)
            else:
                raise MismachingOrientationsError(self.get_layout())
        elif cmp(self.get_pages_in_height(), self.get_pages_in_width()):
            if self.get_input_orientation() == PageOrientation.LANDSCAPE:
                if self._get_output_orientation() == PageOrientation.LANDSCAPE:
                    self._set_output_orientation(PageOrientation.PORTRAIT)
            else:
                raise MismachingOrientationsError(self.get_layout())
        else:
            if self.get_input_orientation() == PageOrientation.LANDSCAPE:
                if self._get_output_orientation() == PageOrientation.PORTRAIT:
                    self._set_output_orientation(PageOrientation.LANDSCAPE)
            else:
                if self._get_output_orientation() == PageOrientation.LANDSCAPE:
                    self._set_output_orientation(PageOrientation.PORTRAIT)

    def __fix_page_orientation_for_booklet(self):
        """
        Adapt the output page orientation to impose
        """
        def __is_two_times(op1, op2):
            if op1 == 2 * op2:
                return True
            else:
                return False
        self.__fix_page_orientation(__is_two_times)

    def __fix_page_orientation_for_linearize(self):
        """
        Adapt the output page orientation to linearize
        """
        def __is_half(op1, op2):
            if op2 == 2 * op1:
                return True
            else:
                return False
        self.__fix_page_orientation(__is_half)

    def __get_sequence_for_booklet(self):
        """
        Calculates the page sequence to impose a booklet.

        :Returns:
            A list of page numbers representing sequence of pages to
            impose a booklet. The list might contain None where blank
            pages should be added.
        """
        n_pages = self.get_page_count()
        pages = range(0, n_pages)

        # Check for missing pages
        if (n_pages % 4) == 0:
            n_missing_pages = 0
        else:
            n_missing_pages = 4 - (n_pages % 4)
            # XXX: print a warning if input page number not diviable by 4?

        # Add reference to the missing empty pages to the pages sequence
        for missing_page in range(0, n_missing_pages):
            pages.append(None)

        def append_and_copy(list, pages):
            """
            Append pages to the list and copy them if needed
            """
            if self.get_copy_pages():
                for i in range(self.get_pages_in_sheet() / 2):
                    list.extend(pages)
            else:
                list.extend(pages)

        # Arranges the pages in booklet order
        sequence = []
        while pages:
            append_and_copy(sequence, [pages.pop(), pages.pop(0)])
            append_and_copy(sequence, [pages.pop(0), pages.pop()])

        return sequence

    def __get_sequence_for_linearize(self, booklet=True):
        """
        Calculates the page sequence to lineraize a booklet.

        :Returns:
            A list of page numbers representing sequence of pages to
            be extracted to linearize a booklet.
        """
        # XXX: is booklet argument useful?

        def append_and_remove_copies(list, pages):
            sequence.extend(pages)
            if self.get_copy_pages():
                for copy in range(self.get_pages_in_sheet() - len(pages)):
                    sequence.append(None)

        if booklet:
            sequence = []
            try :
                for i in range(0, self.get_page_count() *
                               self.get_pages_in_sheet(), 4):
                    append_and_remove_copies(sequence, [i / 2, i / 2])
                    append_and_remove_copies(sequence, [i / 2 + 1, i / 2 + 2])
            except IndexError :
                # XXX: Print a warning
                pass
        else:
            sequence = range(0, self.get_page_count() * self.get_pages_in_sheet())
        return sequence

    def __get_sequence_for_reduce(self):
        """
        Calculates the page sequence to linearly impose reduced pages.

        :Returns:
            A list of page numbers representing sequence of pages to
            impose reduced pages. The list might contain None where blank
            pages should be added.
        """
        if self.get_copy_pages():
            sequence = []
            for page in range(self.get_page_count()):
                for copy in range(self.get_pages_in_sheet()):
                    sequence.append(page)
        else:
            sequence = range(self.get_page_count())
            if len(sequence) % self.get_pages_in_sheet() != 0:
                for missing_page in range(self.get_pages_in_sheet() -
                        (len(sequence) % self.get_pages_in_sheet())):
                    sequence.append(None)
        return sequence

    def __write_output_stream(self, outpdf):
        """
        Writes output to the stream.

        :Parameters:
          - `outpdf` the object to write to the stream. This object must have a
            write() method.
        """
        self.get_progress_callback()(_("writing converted file"), 1)
        outpdf.write(self._output_stream)
        self.get_progress_callback()(_("done"), 1)

    def __do_reduce(self, sequence):
        """
        Do actual imposition job.

        :Parameters:
          - `sequence` a list of page numbers repersenting the sequence of
            pages to impose. None means blank page.

        """
        # XXX: Translated progress messages
        self.__fix_page_orientation_for_booklet()
        outpdf = pyPdf.PdfFileWriter()

        current_page = 0
        while current_page < len(sequence):
            self.get_progress_callback()(
                _("creating page %i") %
                    ((current_page + self.get_pages_in_sheet()) /
                        self.get_pages_in_sheet()),
                float(current_page) / len(sequence)
                )
            page = outpdf.addBlankPage(self.get_output_width(), 
                self.get_output_height())
            for vert_pos in range(0, self.get_pages_in_height()):
                for horiz_pos in range(0, self.get_pages_in_width()):
                    if current_page < len(sequence) and sequence[current_page] is not None:
                        page.mergeScaledTranslatedPage(
                            self._inpdf.getPage(sequence[current_page]),
                            self.get_reduction_factor(), 
                            horiz_pos*self.get_output_width() / \
                                self.get_pages_in_width(),
                            self.get_output_height() - ( 
                                (vert_pos + 1) * self.get_output_height() / \
                                self.get_pages_in_height())
                            )
                    current_page += 1
            page.compressContentStreams()
        self.__write_output_stream(outpdf)

    def bookletize(self):
        self.__do_reduce(self.__get_sequence_for_booklet())

    def reduce(self):
        self.__do_reduce(self.__get_sequence_for_reduce())

    def linearize(self, booklet=True):
        # XXX: Translated progress messages
        # XXX: Wrong zoom factor e.g. when layout is 2x1

        self.__fix_page_orientation_for_linearize()
        sequence = self.__get_sequence_for_linearize()
        outpdf = pyPdf.PdfFileWriter()

        output_page = 0
        for input_page in range(0, self.get_page_count()):
            for vert_pos in range(0, self.get_pages_in_height()):
                for horiz_pos in range(0, self.get_pages_in_width()):
                    if sequence[output_page] is not None:
                        self.get_progress_callback()(
                            _("extracting page %i") % (output_page + 1),
                            float(output_page) / len(sequence))
                        page = outpdf.insertBlankPage(self.get_output_width(),
                                                      self.get_output_height(),
                                                      sequence[output_page])
                        page.mergeScaledTranslatedPage(
                            self._inpdf.getPage(input_page),
                            self.get_increasing_factor(),
                            - horiz_pos * self.get_output_width(),
                            (vert_pos - self.get_pages_in_height() + 1) * \
                                self.get_output_height()
                            )
                        page.compressContentStreams()
                    output_page += 1
        self.__write_output_stream(outpdf)

########################################################################

class FileConverter(StreamConverter):
    """
    This class performs conversions on true files.
    """
    def __init__(self,
                 infile_name,
                 outfile_name=None,
                 layout='2x1',
                 format='A4',
                 copy_pages=False,
                 overwrite_outfile_callback=None):
        """
        Create a FileConverter.

        :Parameters:
          - `infile_name` The name to the input PDF file.
          - `outfile_name` The name of the file where the output PDF
            should de written. If ommited, defaults to the
            name of the input PDF postponded by '-conv'.
          - `layout` The layout of input pages on one output page (see
            set_layout).
          - `format` The format of the output paper (see set_output_format).
          - `copy_pages` Wether the same group of input pages shoud be copied
            to fill the corresponding output page or not (see
            set_copy_pages).
          - `overwrite_outfile_callback` A callback function which is called
            if outfile_name already exists when trying to open it. Its
            signature must be : take a string for the outfile_name as an argument;
            return False not to overwrite the file. If ommited, existing file
            would be overwritten without confirmation.

        """
        # sets [input, output]_stream to None so we can test their presence
        # in __del__
        self._input_stream = None
        self._output_stream = None

        # outfile_name is set if provided
        if outfile_name:
            self.__set_outfile_name(outfile_name)
        else:
            self.__set_outfile_name(None)
          
        # Then infile_nameis set, so if outfile_name was not provided we
        # can create it from infile_name
        self.__set_infile_name(infile_name)

        # Setup callback to ask for confirmation before overwriting outfile
        if overwrite_outfile_callback:
            assert(type(overwrite_outfile_callback) is types.FunctionType)
        else:
            overwrite_outfile_callback = lambda filename: True

        # Now initialize a streamConverter
        self._input_stream = open(self.get_infile_name(), 'rb')
        outfile_name = self.get_outfile_name()
        if (os.path.exists(outfile_name) and not
                overwrite_outfile_callback(os.path.abspath(outfile_name))):
            raise UserInterruptError()
        self._output_stream = open(outfile_name, 'wb')
        StreamConverter.__init__(self, self._input_stream, self._output_stream,
                                 layout, format, copy_pages)

    def __del__(self):
        if self._input_stream:
            try:
                self._input_stream.close()
            except IOError:
                # XXX: Do something better
                pass
        if self._output_stream:
            try:
                self._output_stream.close()
            except IOError:
                # XXX: Do something better
                pass


    # GETTERS AND SETTERS SECTION
    # ===========================

    def __set_infile_name(self, name):
        """
        Sets the name of the input PDF file. Also set the name of output PDF
        file if not already set.

        :Parameters:
          - `name` the name of the input PDF file.
        """
        self.__infile_name = name

        if not self.__outfile_name:
            result = re.search("(.+)\.\w*$", name)
            if result:
                self.__outfile_name = result.group(1) + '-conv.pdf'
            else:
                self.__outfile_name = name + '-conv.pdf'

    def get_infile_name(self):
        """
        Get the name of the input PDF file.

        :Returns:
            The name of the input PDF file.
        """
        return self.__infile_name

    def __set_outfile_name(self, name):
        """
        Sets the name of the output PDF file.

        :Parameters:
          - `name` the name of the output PDF file.
        """
        self.__outfile_name = name

    def get_outfile_name(self):
        """
        Get the name of the output PDF file.

        :Returns:
            The name of the output PDF file.
        """
        return self.__outfile_name


# Convenience functions
# =====================

def bookletize_on_stream(input_stream, 
                         output_stream,
                         layout='2x1',
                         format='A4',
                         copy_pages=False):
    """
    Convert a linear document to a booklet.

    Convert a linear document to a booklet, arranging the pages as
    required.

    This is a convenience function around StreamConverter

    :Parameters:
      - `input_stream` The file-like object from which tne input PDF
        document should be read.
      - `output_stream` The file-like object to which tne output PDF
        document should be written.
      - `layout` The layout of input pages on one output page (see
        set_layout).
      - `format` The format of the output paper (see set_output_format).
      - `copy_pages` Wether the same group of input pages shoud be copied
        to fill the corresponding output page or not (see
        set_copy_pages).
    """
    StreamConverter(layout, format, copy_pages,
                    input_stream, output_stream()).bookletize()

def bookletize_on_file(input_file, 
                       output_file=None,
                       layout='2x1',
                       format='A4',
                       copy_pages=False):
    """
    Convert a linear PDF file to a booklet.

    Convert a linear PDF file to a booklet, arranging the pages as
    required.

    This is a convenience function around FileConverter

    :Parameters:
      - `input_file` The name to the input PDF file.
      - `output_file` The name of the file where the output PDF
        should de written. If ommited, defaults to the
        name of the input PDF postponded by '-conv'.
      - `layout` The layout of input pages on one output page (see
        set_layout).
      - `format` The format of the output paper (see set_output_format).
      - `copy_pages` Wether the same group of input pages shoud be copied
        to fill the corresponding output page or not (see
        set_copy_pages).
    """
    FileConverter(input_file, output_file, layout, format,
                  copy_pages).bookletize()

def linearize_on_stream(input_stream, 
                        output_stream,
                        layout='2x1',
                        format='A4',
                        copy_pages=False):
    """
    Convert a booklet to a linear document.

    Convert a booklet to a linear document, arranging the pages as
    required.

    This is a convenience function around StreamConverter

    :Parameters:
      - `input_stream` The file-like object from which tne input PDF
        document should be read.
      - `output_stream` The file-like object to which tne output PDF
        document should be written.
      - `layout` The layout of output pages on one input page (see
        set_layout).
      - `format` The format of the output paper (see set_output_format).
      - `copy_pages` Wether the same group of input pages shoud be copied
        to fill the corresponding output page or not (see
        set_copy_pages).
    """
    StreamConverter(input_stream, output_stream, layout,
                    format, copy_pages).linearize()

def linearize_on_file(input_file, 
                      output_file=None,
                      layout='2x1',
                      format='A4',
                      copy_pages=False):
    """
    Convert a booklet to a linear PDF file.

    Convert a booklet to a linear PDF file, arranging the pages as
    required.

    This is a convenience function around FileConverter

    :Parameters:
      - `input_file` The name to the input PDF file.
      - `output_file` The name of the file where the output PDF
        should de written. If ommited, defaults to the
        name of the input PDF postponded by '-conv'.
      - `layout` The layout of input pages on one output page (see
        set_layout).
      - `format` The format of the output paper (see set_output_format).
      - `copy_pages` Wether the same group of input pages shoud be copied
        to fill the corresponding output page or not (see
        set_copy_pages).
    """
    FileConverter(input_file, output_file, layout, format,
                  copy_pages).linearize()

def reduce_on_stream(input_stream, 
                     output_stream,
                     layout='2x1',
                     format='A4',
                     copy_pages=False):
    """
    Put multiple input pages on one output page.

    This is a convenience function around StreamConverter

    :Parameters:
      - `input_stream` The file-like object from which tne input PDF
        document should be read.
      - `output_stream` The file-like object to which tne output PDF
        document should be written.
      - `layout` The layout of input pages on one output page (see
        set_layout).
      - `format` The format of the output paper (see set_output_format).
      - `copy_pages` Wether the same group of input pages shoud be copied
        to fill the corresponding output page or not (see
        set_copy_pages).
    """
    StreamConverter(input_stream, output_stream, layout, format, 
                    copy_pages).reduce()

def reduce_on_file(input_file, 
                   output_file=None,
                   layout='2x1',
                   format='A4',
                   copy_pages=False):
    """
    Put multiple input pages on one output page.

    This is a convenience function around FileConverter

    :Parameters:
      - `input_file` The name to the input PDF file.
      - `output_file` The name of the file where the output PDF
        should de written. If ommited, defaults to the
        name of the input PDF postponded by '-conv'.
      - `layout` The layout of input pages on one output page (see
        set_layout).
      - `format` The format of the output paper (see set_output_format).
      - `copy_pages` Wether the same group of input pages shoud be copied
        to fill the corresponding output page or not (see
        set_copy_pages).
    """
    FileConverter(input_file, output_file, layout, format,
                  copy_pages).reduce()
