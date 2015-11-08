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
        """
        
        self.site = pywikibot.Site()
        
        # Set locale to 'de_DE.UTF-8'
        locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
        
        self.page = pywikibot.Page( self.site, wikilink.title )
        
        if not self.page.exists():
            return False
