#!/usr/bin/env python3
# -*- coding: utf-8  -*-
#
#  summarypage.py
#
#  Copyright 2015 GOLDERWEB – Jonathan Golder <jonathan@golderweb.de>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
"""
Provides classes for handling Charts summary page
"""

import locale
from datetime import datetime, timedelta

import pywikibot
import mwparserfromhell as mwparser

from countrylist import CountryList

class SummaryPage():
    """
    Handles summary page related actions
    """
    pass


class SummaryPageEntry():
    """
    Provides a generic wrapper for summary page entry template
    """

    write_needed = False

    def __init__( self, entry ):
        """
        Constructor
        """
        self.old_entry = SummaryPageEntryTemplate( entry )
        self.new_entry = SummaryPageEntryTemplate( )


class SummaryPageEntryTemplate():
    """
    Interface class for mwparser.template to simply use template params as
    Properties
    """

    # Classatribute
    params = ( "Liste", "Liste_Revision", "Interpret", "Titel", "Chartein",
               "Korrektur", "Hervor" )

    def __init__( self, template_obj=None ):
        """
        Creates Instance of Class for given mwparser.template object of
        SummmaryPageEntry Template. If no object was given create empty one.

        @param    template_obj    mw.parser.template   Object of
                                  SummmaryPageEntry Template
        """

        # Check if object was given
        if( template_obj ):

            # Check if object has correct type
            if isinstance( template_obj,
                           mwparser.nodes.template.Template ):

                self.template = template_obj;
                self.__initial = False;

            # Otherwise raise error
            else:
                raise SummaryPageEntryTemplateError( "Wrong type given" );

        # Otherwise initialise template
        else:
            self.__initial_template()
            self.__initial = True;

    def __initial_template( self ):
        """
        Builds the initial template
        """

        self.template = next( mwparser.parse(
"{{/Eintrag|Liste=|Liste_Revision=|Interpret=|Titel=NN\
|Chartein=|Korrektur=|Hervor=}}" ).ifilter_templates() )

    def __getattr__( self, name ):
        """
        Special getter for template params
        """
        if name in type(self).params:

            if( self.template.has( name ) ):
                return self.template.get( name ).value
            else:
                return False

        else:
            raise AttributeError

    def __setattr__( self, name, value ):
        """
        Special setter for template params
        """
        if name in type(self).params:

            self.__dict__[ 'template' ].add( name, value )

        else:
            object.__setattr__(self, name, value)

    def __ne__( self, other ):
        """
        Checks wether all Template param values except for Liste_Revision are
        equal
        """

        # Detect which of the two was initialised (without)
        # If none raise error
        if( self.__initial ):
            initial = self
            cmpto = other
        elif( other.__initial ):
            initial = other
            cmpto = self
        else:
            raise SummaryPageEntryTemplateError(
"One of the compared instances must have been initial!" )

        # Iterate over each param
        for param in initial.template.params:

            # Slice out only Param.name
            param = param[:param.find("=")].strip()

            # If param is missing, writing is needed
            if not cmpto.template.has( param ):
                return True

            # Do not compare List Revisions (not just write about Revids)
            if param == "Liste_Revision":
                continue

            # Compare other param values, if one unequal write is needed
            if initial.template.get( param ).value.strip() != \
                cmpto.template.get( param ).value.strip():
                    return True

        # If not returned True until now
        return False
