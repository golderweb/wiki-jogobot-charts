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

        # Try to find year
        self.find_year()

    def parsing_needed( self, revid ):
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
            raise CountryListYearError

    def detect_belgian( self ):
        """
        Detect wether current entry is on of the belgian (Belgien/Wallonien)
        """
        # Check if begian province name is in link text or title
        if "Wallonien" in str( self.wikilink.text ) \
            or "Wallonien" in str( self.wikilink.title):
                return "Wallonie"
        elif "Flandern" in str( self.wikilink.text ) \
            or "Flandern" in str( self.wikilink.title):
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
            singles_section = self.wikicode.get_sections( matches="Singles" )[0]

        # Select the last occurence of template "Nummer-eins-Hits Zeile" in
        # "Singles"-section
        for self.entry in singles_section.ifilter_templates(
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
