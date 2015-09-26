#!/usr/bin/env python3
# -*- coding: utf-8  -*-
#
#  charts.py
#
#  Copyright 2015 GOLDERWEB – Jonathan Golder <jonathan@golderweb.de>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
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
Provides a class for handling chart lists
"""

from datetime import datetime, timedelta
import locale

from isoweek import Week

import pywikibot  # noqa
import mwparserfromhell as mwparser


class Charts:
    """
    Class for handling chart lists
    """
    
    def __init__( self ):
        """
        Generate a new ChartsList object based on given pywikibot page object
    
        @param    page    page    Pywikibot/MediaWiki page object for page
        """
        
        # Set locale to 'de_DE.UTF-8'
        locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
        
        self.site = pywikibot.Site()
        self.changed = None
        # Safe the pywikibot page object
        # self.page = page
        
        self.open_overview()
        
        self.parse_overview()
        
        if self.changed:
            self.save_overview()

    def parse_charts_list( self, page ):
        """
        Handles the parsing process
        """
        
        # Parse charts list with mwparser
        wikicode = mwparser.parse( page.text )
        
        # Select the section "Singles"
        singles_section = wikicode.get_sections( matches="Singles" )[0]
        
        # Select the last occurence of template "Nummer-eins-Hits Zeile" in
        # "Singles"-section
        last_entry = singles_section.ifilter_templates(
            matches="Nummer-eins-Hits Zeile" )
        for last in last_entry:
            pass
        
        # Detect weather we have a date or a weeknumber for Template Param
        # "Chartein"
        if( last.get("Chartein").value.strip().isnumeric() ):
            chartein = last.get("Chartein").value.strip()
        else:
            chartein = datetime.strptime( last.get("Chartein").value.strip(),
                                          "%Y-%m-%d" )
        
        title = last.get("Titel").value.strip()
        interpret = last.get("Interpret").value.strip()
        
        # Return collected data as tuple
        return ( chartein, title, interpret )
    
    def parse_overview( self ):
        """
        Parses the given Charts-Overview-Page and returns the updated version
        """
        
        # Parse text with mwparser to get access to nodes
        wikicode = mwparser.parse( self.overview_text )
            
        # Get mwparser.template objects for Template "/Eintrag"
        for country in wikicode.ifilter_templates( matches="/Eintrag" ):
            
            # Get mwparser.wikilink object
            for link in country.get("Liste").value.ifilter_wikilinks():
                # Create Page-Object for Chartslist
                list_page = pywikibot.Page( self.site, link.title )
                # Only use first wikilink in Template Param "Liste"
                break
            
            # Check if we have a saved revid
            if not country.has( "Liste Revision" ):
                try:
                    country.add( "Liste Revision", 0, before="Interpret" )
                except ValueError:
                    country.add( "Liste Revision", 0 )
            
            # Check if saved revid is unequal current revid
            if( int( str( country.get( "Liste Revision" ).value ) ) !=
                list_page.latest_revision_id ):
            
                    country = self.update_overview( country, list_page )
            
        # If any param of any occurence of Template "/Eintrag" has changed,
        # Save new version
        # We need to convert mwparser-objects to string before saving
        self.overview_text = str( wikicode )
    
    def open_overview( self ):
        """
        Opens the Charts-Overview-Page
        """
        with open( "/home/joni/GOLDERWEB/Daten/Projekte/05_Wikimedia/62_BOT/bot/charts/test-data.wiki", "r" ) as fr:  # noqa
            
            self.overview_text = fr.read()
    
    def update_overview( self, country, list_page ):  # noqa
        """
        Updates the templates given in county using data from given list_page
        
        @param    country    wikicode-object with Template for country
        @param    list_page  pywikibot-page-object for list-page
        
        @returns wikicode-object with updated Template for country
        """
        
        # Parse linked charts list for the country
        data = self.parse_charts_list( list_page )
                    
        # Update "Liste Revision" param
        self.changed = True
        country.get( "Liste Revision" ).value = str(
            list_page.latest_revision_id )
        
        # For some countries we have weeknumbers instead of dates
        if( isinstance( data[0], str ) ):
            
            # Slice year out of link destination
            year = int( list_page.title()[-5:-1] )
            
            # Check if we have a param "Wochentag", otherwise add
            if not country.has( "Wochentag" ):
                country.add( "Wochentag", "" )
            
            if( str( country.get( "Wochentag" ).value ).isnumeric() ):
                days = int( str( country.get( "Wochentag" ).value ) )
            else:
                days = 0
            
            # Calculate date of monday in given week and add number of
            # days given in Template parameter "Wochentag" with monday
            # as day (zero)
            # We need double conversion since wikicode could not be casted
            # as int directly
            date = ( Week( year, int( data[0] ) ).monday() +
                     timedelta( days=days ) )
                     
        # Param Chartein contains a regular date
        else:
            date = data[0]
        
        # Check if param "Chartein" is present
        if not country.has( "Chartein" ):
            try:
                country.add( "Chartein", "", before="Wochentag" )
            except ValueError:
                country.add( "Chartein", "" )
        
        # Check if date has changed
        if( date.strftime( "%d. %B" ).lstrip( "0" ) !=
            country.get("Chartein").value ):
                self.changed = True
                country.get("Chartein").value = date.strftime( "%d. %B"
                                                               ).lstrip( "0" )
        
        # Check if param "Titel" is present
        if not country.has( "Titel" ):
            country.add( "Titel", "", before="Chartein" )
        
        # Check if Titel has changed
        if( data[1] != country.get( "Titel" ).value ):
            self.changed = True
            country.get( "Titel" ).value = data[1]
        
        # Check if param "Intepret" is present
        if not country.has( "Interpret" ):
            country.add( "Interpret", "", before="Titel" )
        
        # Check if Interpret has changed
        if( data[2] != country.get( "Interpret" ).value ):
            self.changed = True
            country.get( "Interpret" ).value = data[2]
    
    def save_overview( self ):
        """
        Saves the current version of overview-text
        """
        with open( "/home/joni/GOLDERWEB/Daten/Projekte/05_Wikimedia/62_BOT/bot/charts/test-data.wiki", "w" ) as fw:  # noqa
            fw.write( self.overview_text )


def main():
    Charts()

if( __name__ == "__main__" ):
    main()
