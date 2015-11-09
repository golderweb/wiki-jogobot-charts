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

