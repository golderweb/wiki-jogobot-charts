#!/usr/bin/env python3
# -*- coding: utf-8  -*-
#
#  countrylist.py
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
Provides a class for handling charts list per country and year
"""

import locale
from datetime import datetime

from isoweek import Week

import pywikibot
import mwparserfromhell as mwparser


class CountryList():
    """
    Handles charts list per country and year
    """

    def __init__( self, wikilink ):
        """
        Generate new instance of class

        Checks wether page given with country_list_link exists

        @param    wikilink    Wikilink object by mwparser linking CountryList

        @returns  self        Object representing CountryList
                  False       if page does not exists
        """

        # Generate pywikibot site object
        # @TODO: Maybe store it outside???
        self.site = pywikibot.Site()

        # Set locale to 'de_DE.UTF-8'
        locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

        # Generate pywikibot page object
        self.page = pywikibot.Page( self.site, wikilink.title )

        # Store given wikilink for page object
        self.wikilink = wikilink

        # Check if page exits
        if not self.page.exists():
            return False

        # Initialise attributes
        __attr = (  "wikicode", "entry", "chartein", "_chartein_raw",
                    "_titel_raw", "titel", "interpret", "_interpret_raw" )
        for attr in __attr:
            setattr( self, attr, None )

        self.parsed = False

        # Try to find year
        self.find_year()

    def is_parsing_needed( self, revid ):
        """
        Check if current revid of CountryList differs from given one

        @param    int         Revid to check against

        @return   True        Given revid differs from current revid
                  False       Given revid is equal to current revid
        """

        if revid != self.page.latest_revision_id:
            return True
        else:
            return False

    def find_year( self ):
        """
        Try to find the year related to CountryList
        """
        self.year = datetime.now().year

        # Check if year is in page.title, if not try last year
        if str( self.year ) not in self.page.title():
            self.year -= 1
        # If last year does not match, raise YearError
        if str( self.year ) not in self.page.title():
            raise CountryListError( "CountryList year is errorneous!" )

    def parse( self ):
        """
        Handles the parsing process
        """

        # Parse page with mwparser
        self.generate_wikicode()

        # Select lastest entry
        self.get_latest_entry()

        # Prepare chartein, titel, interpret
        self.prepare_chartein()
        self.prepare_titel()
        self.prepare_interpret()

        # For easy detecting wether we have parsed self
        self.parsed = True

    def detect_belgian( self ):
        """
        Detect wether current entry is on of the belgian (Belgien/Wallonien)
        """
        # Check if begian province name is in link text or title
        if( "Wallonien" in str( self.wikilink.text ) or
            "Wallonien" in str( self.wikilink.title) ):
                return "Wallonie"
        elif( "Flandern" in str( self.wikilink.text ) or
              "Flandern" in str( self.wikilink.title) ):
                return "Flandern"
        else:
            return None

    def generate_wikicode( self ):
        """
        Runs mwparser on page.text to get mwparser.objects
        """

        self.wikicode = mwparser.parse( self.page.text )

    def get_latest_entry( self ):
        """
        Get latest list entry template object
        """

        # Select the section "Singles"
        # For belgian list we need to select subsection of country
        belgian = self.detect_belgian()

        if belgian:
            singles_section = self.wikicode.get_sections(
                matches=belgian )[0].get_sections( matches="Singles" )[0]
        else:
            singles_section = self.wikicode.get_sections(matches="Singles")[0]

        # Since we have multiple categories in some countrys we need
        # to select the first wrapping template
        try:
            wrapping = next( singles_section.ifilter_templates(
                matches="Nummer-eins-Hits" ) )
        except StopIteration:
                raise CountryListError( "Wrapping template is missing!")

        # Select the last occurence of template "Nummer-eins-Hits Zeile" in
        # Wrapper-template
        for self.entry in wrapping.get("Inhalt").value.ifilter_templates(
                matches="Nummer-eins-Hits Zeile" ):
                    pass

        # Check if we have found something
        if not self.entry:
            raise CountryListError( self.page.title() )

    def get_year_correction( self ):
        """
        Reads value of jahr parameter for correcting week numbers near to
        year changes
        """
        # If param is present return correction, otherwise null
        if self.entry.has( "Jahr" ):

            # Read value of param
            jahr = self.entry.get( "Jahr" ).strip()

            if jahr == "+1":
                return 1
            elif jahr == "-1":
                return -1

        # None or wrong parameter value
        return 0

    def prepare_chartein( self ):
        """
        Checks wether self._chartein_raw is a date or a week number and
        calculates related datetime object
        """

        # If self._chartein_raw is not set, get it
        if not self._chartein_raw:
            self.get_chartein_value()

        # Detect weather we have a date or a weeknumber for Template Param
        # "Chartein"
        # Numeric string means week number
        if( self._chartein_raw.isnumeric() ):

            # Calculate date of monday in given week and add number of
            # days given in Template parameter "Korrektur" with monday
            # as day (zero)
            self.chartein = ( Week( self.year + self.get_year_correction(),
                                    int( self._chartein_raw ) ).monday() )
        # Complete date string present
        else:
            self.chartein = datetime.strptime( self._chartein_raw,
                                               "%Y-%m-%d" )

    def get_chartein_value( self ):
        """
        Reads value of chartein parameter
        If param is not present raise Error
        """
        if self.entry.has( "Chartein" ):
            self._chartein_raw = self.entry.get("Chartein").value.strip()
        else:
            raise CountryListEntryError( "Template Parameter 'Chartein' is \
missing!" )

    def prepare_titel( self ):
        """
        Loads and prepares Titel of latest entry
        """

        # If self._titel_raw is not set, get it
        if not self._titel_raw:
            self.get_titel_value()

        # Try to find a wikilink for Titel on countrylist
        if "[[" not in self._titel_raw:
            self.titel = self._search_links( str(self._titel_raw) )
        else:
            self.titel = self._titel_raw

    def get_titel_value( self ):
        """
        Reads value of Titel parameter
        If param is not present raise Error
        """
        if self.entry.has( "Titel" ):
            self._titel_raw = self.entry.get("Titel").value.strip()
        else:
            raise CountryListEntryError( "Template Parameter 'Titel' is \
missing!" )

    def prepare_interpret( self ):
        """
        Loads and prepares Interpret of latest entry
        """

        # If self._interpret_raw is not set, get it
        if not self._interpret_raw:
            self.get_interpret_value()

        # Work with interpret value to add missing links
        # Split it in words
        words = self._interpret_raw.split()

        # Interpret name separating words
        seps = ( "feat.", "&" )

        # Create empty list for concatenated interpret names
        parts = [ " ", ]
        # Another list for managing indexes which need to be worked on
        indexes = list()
        index = 0

        # Reconcatenate interpret names
        for word in words:

            # Name parts
            if word not in seps:
                parts[-1] += (" " + word)

                # Remove unnecessary whitespace
                parts[-1] = parts[-1].strip()

                # We only need to work on it, if no wikilink is present
                if index not in indexes and "[[" not in parts[-1]:
                    indexes.append( index )
            else:
                # Count up index 2 times ( Separator + next Name )
                index += 2
                parts.append( word )
                parts.append( " " )

        # If we have indexes without links, search for links
        if indexes:

            parts = self._search_links( parts, indexes )

            # Join the collected links
            sep = " "
            self.interpret = sep.join( parts )

        # Nothing to do, just use raw
        else:
            self.interpret = self._interpret_raw

    def get_interpret_value( self ):
        """
        Reads value of Interpret parameter
        If param is not present raise Error
        """
        if self.entry.has( "Interpret" ):
            self._interpret_raw = self.entry.get("Interpret").value.strip()
        else:
            raise CountryListEntryError( "Template Parameter 'Interpret' is \
missing!" )

    def _search_links( self, keywords, indexes=None ):
        """
        Search matching wikilinks for keyword(s) in CountryList's wikicode

        @param keywords: One or more keywords to search for
        @type keywords: str, list
        @param indexes: List with numeric indexes for items of keywords to work
                        on only
        @type indexes: list of ints
        @return: List or String with replaced keywords
        @return type: str, list
        """

        # Maybe convert keywords string to list
        if( isinstance( keywords, str ) ):
            keywords = [ keywords, ]
            string = True
        else:
            string = False

        # If indexes worklist was not provided, work on all elements
        if not indexes:
            indexes = list(range( len( keywords ) ))

        # Iterate over wikilinks of refpage and try to find related links
        for wikilink in self.wikicode.ifilter_wikilinks():

            # Iterate over interpret names
            for index in indexes:

                # Check wether wikilink matches
                if( keywords[index] == wikilink.text or
                    keywords[index] == wikilink.title ):

                    # Overwrite name with complete wikilink
                    keywords[index] = str( wikilink )

                    # Remove index from worklist
                    indexes.remove( index )

                    # Other indexes won't also match
                    break

            # If worklist is empty, stop iterating over wikilinks
            if not indexes:
                break

        # Choose wether return list or string based on input type
        if not string:
            return keywords
        else:
            return str(keywords[0])


class CountryListError( Exception ):
    """
    Handles errors occuring in class CountryList
    """
    pass


class CountryListEntryError( CountryListError ):
    """
    Handles errors occuring in class CountryList related to entrys
    """
    pass
