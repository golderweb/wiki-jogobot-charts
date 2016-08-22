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

from datetime import datetime, timedelta

# import pywikibot
import mwparserfromhell as mwparser

import jogobot

from countrylist import CountryList, CountryListError


class SummaryPage():
    """
    Handles summary page related actions
    """

    def __init__( self, text, force_reload=False ):
        """
        Create Instance

        @param text: Page Text of summarypage
        @type text: str
        @param force-reload: If given, countrylists will be always parsed
                             regardless if needed or not
        @type force-reload: bool

        """

        # Parse Text with mwparser
        self.wikicode = mwparser.parse( text )

        # Force parsing of countrylist
        self.force_reload = force_reload

    def treat( self ):
        """
        Handles parsing/editing of text
        """

        # Get mwparser.template objects for Template "/Eintrag"
        for entry in self.wikicode.filter_templates( matches="/Eintrag" ):

            # Instantiate SummaryPageEntry-object
            summarypageentry = SummaryPageEntry(entry,
                                                force_reload=self.force_reload)

            # Treat SummaryPageEntry-object
            summarypageentry.treat()

            # Get result
            # We need to replace origninal entry since objectid changes due to
            # recreation of template object and reassignment won't be reflected
            self.wikicode.replace(entry, summarypageentry.get_entry().template)

    def get_new_text( self ):
        """
        If writing page is needed, return new text, otherwise false
        """

        # Get information wether writing is needed from class attribute
        if SummaryPageEntry.write_needed:

            # Convert wikicode back to string and return
            return str( self.wikicode )

        return False


class SummaryPageEntry():
    """
    Provides a generic wrapper for summary page entry template
    """

    write_needed = False

    def __init__( self, entry, force_reload=False ):
        """
        Constructor

        @param entry: Entry template of summarypage entry
        @type text: mwparser.template
        @param force-reload: If given, countrylists will be always parsed
                             regardless if needed or not
        @type force-reload: bool
        """
        self.old_entry = SummaryPageEntryTemplate( entry )
        self.new_entry = SummaryPageEntryTemplate( )

        # Force parsing of countrylist
        self.force_reload = force_reload

    def treat( self ):
        """
        Controls parsing/update-sequence of entry
        """
        # Get CountryList-Object
        self.get_countrylist()

        # Check if parsing country list is needed
        if( self.countrylist.parsed):

            self.correct_chartein()

            self.update_params()

        self.is_write_needed()

    def get_countrylist( self ):
        """
        Get the CountryList-Object for current entry
        """

        # Get wikilink to related countrylist
        self.get_countrylist_wikilink()

        # Get saved revision of related countrylist
        self.get_countrylist_saved_revid()

        # Get current year
        current_year = datetime.now().year

        # If list is from last year, replace year
        if (current_year - 1) in self.countrylist_wikilink.title:
            jogobot.output( "Trying to use new years list for [[{page}]]"
                            .format( page=self.countrylist_wikilink.title ) )

            self.countrylist_wikilink.title.replace( (current_year - 1),
                                                     current_year )

        # Try to get current years list
        try:
            self.countrylist = CountryList( self.countrylist_wikilink )

            self.maybe_parse_countrylist()

        # Maybe fallback to last years list
        except CountryListError:

            # If list is from last year, replace year
            if (current_year ) in self.countrylist_wikilink.title:
                jogobot.output( "New years list for [[{page}]] does not " +
                                "exist, fall back to old list!".format(
                                    page=self.countrylist_wikilink.title ) )

                self.countrylist_wikilink.title.replace( current_year,
                                                         (current_year - 1) )

            self.countrylist = CountryList( self.countrylist_wikilink )

            self.maybe_parse_countrylist()

            if not self.countrylist:
                raise SummaryPageEntryError( "CountryList does not exists!" )

    def maybe_parse_countrylist( self ):
        """
        Parse countrylist if page-object exists and if parsing is needed or
        param -force-reload is set
        """

        # Fast return if no countrylist-object
        if not self.countrylist:
            return

        # Parse if needed or forced
        if( self.countrylist.is_parsing_needed( self.countrylist_revid ) or
            self.force_reload ):
                self.countrylist.parse()

    def get_countrylist_wikilink( self ):
        """
        Load wikilink to related countrylist
        """
        if self.old_entry.Liste:
            try:
                self.countrylist_wikilink = next(
                    self.old_entry.Liste.ifilter_wikilinks() )
            except StopIteration:
                raise SummaryPageEntryError(
                    "Parameter Liste does not contain valid wikilink!" )
        else:
            raise SummaryPageEntryError( "Parameter Liste is not present!")

    def get_countrylist_saved_revid( self ):
        """
        Load saved revid of related countrylist if Param is present
        """
        if self.old_entry.Liste_Revision:
            self.countrylist_revid = int(self.old_entry.Liste_Revision.strip())
        else:
            self.countrylist_revid = 0

    def update_params( self ):
        """
        Updates values of Parameters of template
        """

        self.new_entry.Liste = self.countrylist_wikilink
        self.new_entry.Liste_Revision = \
            self.countrylist.page.latest_revision_id
        self.new_entry.Interpret = self.countrylist.interpret
        self.new_entry.Titel = self.countrylist.titel
        self.new_entry.Chartein = self._corrected_chartein

        if self.old_entry.Korrektur:
            self.new_entry.Korrektur = self.old_entry.Korrektur
        else:
            self.new_entry.Korrektur = ""

        if self.old_entry.Hervor:
            self.new_entry.Hervor = self.old_entry.Hervor
        else:
            self.new_entry.Hervor = ""

    def correct_chartein( self ):
        """
        Calulates the correct value of chartein, based on the chartein value
        from countrylist entry and param Korrektur of summarypage entry
        """
        # If param Korrektur is present extract the value
        if self.old_entry.Korrektur:
            # If Korrektur is (after striping) castable to int use it
            try:
                days = int( str( self.old_entry.Korrektur ).strip() )
            # Otherwise, if casting fails, ignore it
            except ValueError:
                days = 0
        else:
            days = 0

        corrected = self.countrylist.chartein + timedelta( days=days )
        self._corrected_chartein = corrected.strftime( "%d. %B" ).lstrip( "0" )

    def is_write_needed( self ):
        """
        Detects wether writing of entry is needed and stores information in
        Class-Attribute
        """
        type( self ).write_needed = ( ( self.old_entry != self.new_entry ) and
                                      self.countrylist.parsed or
                                      type( self ).write_needed )

    def get_entry( self ):
        """
        Returns the new entry if CountryList was parsed otherwise returns the
        old one
        """
        if( self.countrylist.parsed):
            return self.new_entry
        else:
            return self.old_entry


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

        @param template_obj Object of SummmaryPageEntry Template
        @type template_obj: mwparser.template
        """

        # Check if object was given
        if( template_obj ):

            # Check if object has correct type
            if isinstance( template_obj,
                           mwparser.nodes.template.Template ):

                self.template = template_obj
                self.__initial = False

            # Otherwise raise error
            else:
                raise SummaryPageEntryTemplateError( "Wrong type given" )

        # Otherwise initialise template
        else:
            self.__initial_template()
            self.__initial = True

    def __initial_template( self ):
        """
        Builds the initial template
        """

        self.template = next( mwparser.parse( "{{Portal:Charts und Popmusik/\
Aktuelle Nummer-eins-Hits/Eintrag|Liste=|Liste_Revision=|Interpret=|Titel=NN\
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
            if( initial.template.get( param ).value.strip() !=
                cmpto.template.get( param ).value.strip() ):
                    return True

        # If not returned True until now
        return False


class SummaryPageError( Exception ):
    """
    Handles errors occuring in class SummaryPage
    """
    pass


class SummaryPageEntryError( SummaryPageError ):
    """
    Handles errors occuring in class SummaryPageEntry
    """
    pass


class SummaryPageEntryTemplateError( SummaryPageError ):
    """
    Handles errors occuring in class SummaryPageEntryTemplate
    """
    pass
