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

    def __init__( self, generator, always, dry ):
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
        self.always = always

        # Set the edit summary message
        self.site = pywikibot.Site()
        self.summary = "Bot: Aktualisiere Übersichtsseite Nummer-eins-Hits"

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
        if text != page.get():
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                             % page.title())
            # show what was changed
            pywikibot.showDiff(page.get(), text)
            pywikibot.output(u'Comment: %s' % comment)
            if not self.dry:
                if self.always or pywikibot.input_yn(
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

    def parse_overview( self, text ):
        """
        Parses the given Charts-Overview-Page and returns the updated version
        """

        # Parse text with mwparser to get access to nodes
        wikicode = mwparser.parse( text )

        # Get mwparser.template objects for Template "/Eintrag"
        for entry in wikicode.ifilter_templates( matches="/Eintrag" ):

            # Maybe complete entry template
            self.entry_template_complete( entry )

            # Extract saved revision_id
            ref_list_revid = int(str( entry.get( "Liste Revision" ).value ))

            # Parse ref list
            data = self.parse_ref_list( self.get_entry_ref_list( entry ),
                                        ref_list_revid )

            # Check that parsing was not short circuited
            if data:
                data = self.calculate_chartein( entry, data )

                entry = self.entry_changed( entry, data )

            #~ # Check if saved revid is unequal to current revid
            #~ if( str( country.get( "Liste Revision" ).value ) !=
                #~ list_page.latest_revision_id ):
                    #~
                    #~ country = self.update_overview( country, list_page )

        # If any param of any occurence of Template "/Eintrag" has changed,
        # Save new version
        # We need to convert mwparser-objects to string before saving
        return str( wikicode )

    def parse_ref_list( self, ref_list_link , ref_list_revid):
        """
        Handles the parsing process of ref list
        """

        # Create Page-Object for Chartslist
        ref_list_page = pywikibot.Page( self.site, ref_list_link.title )

        # Short circuit if current revision is same than saved
        if( ref_list_page.latest_revision_id ==  ref_list_revid ):
            return False

        # We need the year related to ref_list_link
        year = int(ref_list_page.title()[-5:-1])

        # Parse charts list with mwparser
        wikicode = mwparser.parse( ref_list_page.text )

        # Detect if we are on begian list
        belgian = self.detect_belgium( ref_list_link )

        # Select the section "Singles"
        # For belgian list we need to select subsection of country
        if belgian:
            singles_section = wikicode.get_sections(
                matches=belgian )[0].get_sections( matches="Singles" )[0]
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

            # Maybe there is a year correction for weeknumber
            if last.has( "Jahr" ):
                if last.get("Jahr").value.strip() == "+1":
                    year = year + 1
                elif last.get("Jahr").value.strip() == "-1":
                    year = year - 1

            chartein = ( year, chartein )
        else:
            chartein = datetime.strptime( last.get("Chartein").value.strip(),
                                          "%Y-%m-%d" )

        title = last.get("Titel").value.strip()
        interpret = last.get("Interpret").value.strip()

        # Return collected data as tuple
        return ( chartein, title, interpret, ref_list_page.latest_revision_id )

    def detect_belgium( self, ref_list_link ):
        """
        Detect wether current entry is on of the belgian (Belgien/Wallonien)
        """
        # Parse linked charts list for the country
        if "Wallonien" in str( ref_list_link.text ) \
            or "Wallonien" in str( ref_list_link.title):
                return "Wallonie"
        elif "Flandern" in str( ref_list_link.text ) \
            or "Flandern" in str( ref_list_link.title):
                return "Flandern"
        else:
            return None

    def update_overview( self, country, list_page ):  # noqa
        """
        Updates the templates given in county using data from given list_page

        @param    country    wikicode-object with Template for country
        @param    list_page  pywikibot-page-object for list-page

        @returns wikicode-object with updated Template for country
        """

        data = self.parse_charts_list( ref_list_link, belgien )

    def get_entry_ref_list( self, entry ):
        """
        """
        # Get mwparser.wikilink object
        return next( entry.get("Liste").value.ifilter_wikilinks() )

    def calculate_chartein( self, entry, data ):
        """
        Calculates the correct value for param chartein in entry
        """
        # If param Korrektur is present extract the value
        if( entry.has( "Korrektur" ) ):
            # If Korrektur is (after striping) castable to int use it
            try:
                days = int( str( entry.get( "Korrektur" ).value ).strip() )
            # Otherwise, if casting fails, ignore it
            except ValueError:
                days = 0
        else:
            days = 0

        # For some countries we have weeknumbers instead of dates
        if( isinstance( data[0], tuple ) ):

            # Calculate date of monday in given week and add number of
            # days given in Template parameter "Korrektur" with monday
            # as day (zero)
            date = ( Week( data[0][0], int( data[0][1] ) ).monday() +
                     timedelta( days=days ) )

        # Param Chartein contains a regular date
        else:
            date = data[0] + timedelta( days=days )

        return (date,)+data[1:]

    def entry_template_complete( self, entry ):
        """
        Checks wether given entry template is complete, otherwise adds missing
        params
        """

        # Check if param "Chartein" is present
        if not entry.has( "Chartein" ):
            try:
               entry.add( "Chartein", "", before="Korrektur" )
            except ValueError:
                entry.add( "Chartein", "" )

        # Check if param "Titel" is present
        if not entry.has( "Titel" ):
            entry.add( "Titel", "", before="Chartein" )

        # Check if param "Intepret" is present
        if not entry.has( "Interpret" ):
            entry.add( "Interpret", "", before="Titel" )

        # Check if we have a saved revid
        if not entry.has( "Liste Revision" ):
            entry.add( "Liste Revision", 0, before="Interpret" )

        return entry

    def entry_changed( self, entry, data ):
        """
        Checks wether given entry has changed
        """

        # Check if date has changed
        if( data[0].strftime( "%d. %B" ).lstrip( "0" ) !=
            entry.get("Chartein").value ):

                entry.get("Chartein").value = data[0].strftime( "%d. %B"
                                                               ).lstrip( "0" )

        # Check if Titel has changed
        if( data[1] != entry.get( "Titel" ).value ):
            entry.get( "Titel" ).value = data[1]

        # Check if Interpret has changed
        if( data[2] != entry.get( "Interpret" ).value ):
            entry.get( "Interpret" ).value = data[2]

        # Update "Liste Revision" param
        entry.get( "Liste Revision" ).value = str(
            data[3] )

        return entry

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

    # If always is True, bot won't ask for confirmation of edit (automode)
    always = False

    # Parse command line arguments
    for arg in local_args:
        if arg.startswith("-dry"):
            dry = True
        elif arg.startswith("-always"):
            always = True
        else:
            genFactory.handleArg(arg)

    if not gen:
        gen = genFactory.getCombinedGenerator()
    if gen:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        gen = pagegenerators.PreloadingGenerator(gen)
        bot = Charts(gen, always, dry)
        bot.run()
    else:
        pywikibot.showHelp()

if( __name__ == "__main__" ):
    main()
