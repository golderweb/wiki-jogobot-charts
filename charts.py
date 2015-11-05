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

import pywikibot
from pywikibot import pagegenerators
import mwparserfromhell as mwparser

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class Charts:
    """
    Class for handling chart lists
    """
    
    def __init__( self, generator, dry ):
        """
        Constructor.

        @param generator: The page generator that determines on which pages
                              to work.
        @type generator: generator.
        @param dry: If True, doesn't do any real changes, but only shows
                    what would have been changed.
        @type dry: boolean.
        """
        
        self.generator = generator
        self.dry = dry

        # Set the edit summary message
        self.site = pywikibot.Site()
        self.summary = "Bot: Aktualisiere Übersichtsseite Nummer-eins-Hits"
        
        # Set attribute to detect wether there was a real change
        self.changed = None
        
        # Set locale to 'de_DE.UTF-8'
        locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

    def run(self):
        """Process each page from the generator."""
        for page in self.generator:
            self.treat(page)
            
    def treat(self, page):
        """Load the given page, does some changes, and saves it."""
        text = self.load(page)
        if not text:
            return

        ################################################################
        # NOTE: Here you can modify the text in whatever way you want. #
        ################################################################

        # If you find out that you do not want to edit this page, just return.
        # Example: This puts the text 'Test' at the beginning of the page.
               
        text = self.parse_overview( text )

        if not self.save(text, page, self.summary, False):
            pywikibot.output(u'Page %s not saved.' % page.title(asLink=True))

    def load(self, page):
        """Load the text of the given page."""
        try:
            # Load the page
            text = page.get()
        except pywikibot.NoPage:
            pywikibot.output(u"Page %s does not exist; skipping."
                             % page.title(asLink=True))
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"Page %s is a redirect; skipping."
                             % page.title(asLink=True))
        else:
            return text
        return None

    def save(self, text, page, comment=None, minorEdit=True,
             botflag=True):
        """Update the given page with new text."""
        # only save if something was changed (and not just revision)
        if text != page.get() and self.changed:
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                             % page.title())
            # show what was changed
            pywikibot.showDiff(page.get(), text)
            pywikibot.output(u'Comment: %s' % comment)
            if not self.dry:
                if True or pywikibot.input_yn(
                        u'Do you want to accept these changes?',
                        default=False, automatic_quit=False):
                    try:
                        page.text = text
                        # Save the page
                        page.save(summary=comment or self.comment,
                                  minor=minorEdit, botflag=botflag)
                    except pywikibot.LockedPage:
                        pywikibot.output(u"Page %s is locked; skipping."
                                         % page.title(asLink=True))
                    except pywikibot.EditConflict:
                        pywikibot.output(
                            u'Skipping %s because of edit conflict'
                            % (page.title()))
                    except pywikibot.SpamfilterError as error:
                        pywikibot.output(
                            u'Cannot change %s because of spam blacklist \
entry %s'
                            % (page.title(), error.url))
                    else:
                        return True
        return False
    
    def parse_charts_list( self, page, belgien=False ):
        """
        Handles the parsing process
        """
        
        # Parse charts list with mwparser
        wikicode = mwparser.parse( page.text )
        
        # Select the section "Singles"
        if belgien:
            singles_section = wikicode.get_sections(
                matches=belgien )[0].get_sections( matches="Singles" )[0]
        else:
            singles_section = wikicode.get_sections( matches="Singles" )[0]
        
        # Select the last occurence of template "Nummer-eins-Hits Zeile" in
        # "Singles"-section
        entries = singles_section.filter_templates(
            matches="Nummer-eins-Hits Zeile" )
        
        # Check, wether we found some entries
        if not entries:
            raise ChartsListError( page.title() )
        else:
            last = entries[-1]
        
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
    
    def parse_overview( self, text ):
        """
        Parses the given Charts-Overview-Page and returns the updated version
        """
        
        # Parse text with mwparser to get access to nodes
        wikicode = mwparser.parse( text )
            
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
            
            # Check if saved revid is unequal to current revid
            if( str( country.get( "Liste Revision" ).value ) !=
                list_page.latest_revision_id ):
                    
                    country = self.update_overview( country, list_page )
            
        # If any param of any occurence of Template "/Eintrag" has changed,
        # Save new version
        # We need to convert mwparser-objects to string before saving
        return str( wikicode )
    
    def update_overview( self, country, list_page ):  # noqa
        """
        Updates the templates given in county using data from given list_page
        
        @param    country    wikicode-object with Template for country
        @param    list_page  pywikibot-page-object for list-page
        
        @returns wikicode-object with updated Template for country
        """
        
        # Parse linked charts list for the country
        if "Wallonien" in str( country.get( "Liste" ).value ):
            belgien = "Wallonie"
        elif "Flandern" in str( country.get( "Liste" ).value ):
            belgien = "Flandern"
        else:
            belgien = None
            
        data = self.parse_charts_list( list_page, belgien )
                    
        # Update "Liste Revision" param
        country.get( "Liste Revision" ).value = str(
            list_page.latest_revision_id )
        
        # If param Korrektur is present extract the value
        if( country.has( "Korrektur" ) and
            str( country.get( "Korrektur" ).value ).isnumeric() ):
                days = int( str( country.get( "Korrektur" ).value ) )
        else:
            days = 0
        
        # For some countries we have weeknumbers instead of dates
        if( isinstance( data[0], str ) ):
            
            
            
            # Calculate date of monday in given week and add number of
            # days given in Template parameter "Korrektur" with monday
            # as day (zero)
            date = ( Week( year, int( data[0] ) ).monday() +
                     timedelta( days=days ) )
                     
        # Param Chartein contains a regular date
        else:
            date = data[0] + timedelta( days=days )
        
        # Check if param "Chartein" is present
        if not country.has( "Chartein" ):
            try:
                country.add( "Chartein", "", before="Korrektur" )
            except ValueError:
                country.add( "Chartein", "" )
        
        # Check if date has changed
        if( date.strftime( "%d. %B" ).lstrip( "0" ) !=
            country.get("Chartein").value ):
                country.get("Chartein").value = date.strftime( "%d. %B"
                                                               ).lstrip( "0" )
                self.changed = True
        
        # Check if param "Titel" is present
        if not country.has( "Titel" ):
            country.add( "Titel", "", before="Chartein" )
        
        # Check if Titel has changed
        if( data[1] != country.get( "Titel" ).value ):
            country.get( "Titel" ).value = data[1]
            self.changed = True
        
        # Check if param "Intepret" is present
        if not country.has( "Interpret" ):
            country.add( "Interpret", "", before="Titel" )
        
        # Check if Interpret has changed
        if( data[2] != country.get( "Interpret" ).value ):
            country.get( "Interpret" ).value = data[2]
            self.changed = True


class ChartsError( Exception ):
    """
    Base class for all Errors of Charts-Module
    """
    
    def __init__( self, message=None ):
        """
        Handles Instantiation of ChartsError's
        """
        if not message:
            self.message = "An Error occured while executing a Charts action"
        else:
            self.message = message
    
    def __str__( self ):
        """
        Output of error message
        """
        
        return self.message


class ChartsListError( ChartsError ):
    """
    Raised when given ChartsListPage does not contain valid entrys
    """
    
    def __init__( self, givenPage ):
        
        message = "Given CharstListPage ('{given}') does not contain \
valid entries".format( given=givenPage )
        
        super().__init__( message )


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # Process global arguments to determine desired site
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()
    # The generator gives the pages that should be worked upon.
    gen = None
    # If dry is True, doesn't do any real changes, but only show
    # what would have been changed.
    dry = False

    # Parse command line arguments
    for arg in local_args:
        if arg.startswith("-dry"):
            dry = True
        else:
            genFactory.handleArg(arg)

    if not gen:
        gen = genFactory.getCombinedGenerator()
    if gen:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        gen = pagegenerators.PreloadingGenerator(gen)
        bot = Charts(gen, dry)
        bot.run()
    else:
        pywikibot.showHelp()

if( __name__ == "__main__" ):
    main()
