#!/usr/bin/env python3
# -*- coding: utf-8  -*-
#
#  charts.py
#
#  original version by:
#
#  (C) Pywikibot team, 2006-2014 as basic.py
#
#  Distributed under the terms of the MIT license.
#
#  modified by:
#
#  Copyright 2016 GOLDERWEB – Jonathan Golder <jonathan@golderweb.de>
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
Bot which automatically updates a ChartsSummaryPage like
[[Portal:Charts_und_Popmusik/Aktuelle_Nummer-eins-Hits]] by reading linked
CountryLists

The following parameters are supported:

&params;

-always           If given, request for confirmation of edit is short circuited
                  Use for unattended run
-force-reload     If given, countrylists will be always parsed regardless if
                  needed or not
"""


import locale
import os
import sys

import pywikibot
from pywikibot import pagegenerators

import jogobot

from summarypage import SummaryPage

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class ChartsBot( ):
    """
    Bot which automatically updates a ChartsSummaryPage like
    [[Portal:Charts_und_Popmusik/Aktuelle_Nummer-eins-Hits]] by reading linked
    CountryLists
    """

    def __init__( self, generator, always, force_reload ):
        """
        Constructor.

        @param generator: the page generator that determines on which pages
            to work
        @type generator: generator
        @param always: if True, request for confirmation of edit is short
                        circuited. Use for unattended run
        @type always: bool
        @param force-reload: If given, countrylists will be always parsed
                             regardless if needed or not
        @type force-reload: bool
        """

        self.generator = generator
        self.always = always

        # Force parsing of countrylist
        self.force_reload = force_reload

        # Output Information
        jogobot.output( "Chartsbot invoked" )

        # Set the edit summary message
        self.site = pywikibot.Site()
        self.summary = "Bot: Aktualisiere Übersichtsseite Nummer-eins-Hits"

        # Set locale to 'de_DE.UTF-8'
        locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

    def run(self):
        """Process each page from the generator."""
        # Count skipped pages (redirect or missing)
        skipped = 0
        for page in self.generator:
            if not self.treat(page):
                skipped += 1

        if skipped:
            jogobot.output( "Chartsbot finished, {skipped} page(s) skipped"
                            .format( skipped=skipped ) )
        else:
            jogobot.output( "Chartsbot finished successfully" )

    def treat(self, page):
        """Load the given page, does some changes, and saves it."""
        text = self.load(page)
        if not text:
            return False

        ################################################################
        # NOTE: Here you can modify the text in whatever way you want. #
        ################################################################

        # Initialise and treat SummaryPageWorker
        sumpage = SummaryPage( text, self.force_reload )
        sumpage.treat()

        # Check if editing is needed and if so get new text
        if sumpage.get_new_text():
            text = sumpage.get_new_text()

        if not self.save(text, page, self.summary, False):
            jogobot.output(u'Page %s not saved.' % page.title(asLink=True))

        return True

    def load(self, page):
        """Load the text of the given page."""
        try:
            # Load the page
            text = page.get()
        except pywikibot.NoPage:
            jogobot.output( u"Page %s does not exist; skipping."
                            % page.title(asLink=True), "ERROR" )
        except pywikibot.IsRedirectPage:
            jogobot.output( u"Page %s is a redirect; skipping."
                            % page.title(asLink=True), "ERROR" )
        else:
            return text
        return False

    def save(self, text, page, comment=None, minorEdit=True,
             botflag=True):
        """Update the given page with new text."""
        # only save if something was changed (and not just revision)
        if text != page.get():

            # Show diff only in interactive mode or in verbose mode
            if not self.always or pywikibot.config.verbose_output:

                # Show the title of the page we're working on.
                # Highlight the title in purple.
                jogobot.output( u">>> \03{lightpurple}%s\03{default} <<<"
                                % page.title())
                # show what was changed
                pywikibot.showDiff(page.get(), text)
                jogobot.output(u'Comment: %s' % comment)

            if self.always or pywikibot.input_yn(
                    u'Do you want to accept these changes?',
                    default=False, automatic_quit=False):
                try:
                    page.text = text
                    # Save the page
                    page.save(summary=comment or self.comment,
                              minor=minorEdit, botflag=botflag)
                except pywikibot.LockedPage:
                    jogobot.output( u"Page %s is locked; skipping."
                                    % page.title(asLink=True), "ERROR" )
                except pywikibot.EditConflict:
                    jogobot.output(
                        u'Skipping %s because of edit conflict'
                        % (page.title()), "ERROR")
                except pywikibot.SpamfilterError as error:
                    jogobot.output(
                        u'Cannot change %s because of spam blacklist \
entry %s'
                        % (page.title(), error.url), "ERROR")
                else:
                    return True
        return False


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """

    # Process global arguments to determine desired site
    local_args = pywikibot.handle_args(args)

    # Get the jogobot-task_slug (basename of current file without ending)
    task_slug = os.path.basename(__file__)[:-len(".py")]

    # Before run, we need to check wether we are currently active or not
    try:
        # Will throw Exception if disabled/blocked
        jogobot.is_active( task_slug )

    except jogobot.jogobot.Blocked:
        (type, value, traceback) = sys.exc_info()
        jogobot.output( "\03{lightpurple} %s (%s)" % (value, type ),
                        "CRITICAL" )

    except jogobot.jogobot.Disabled:
        (type, value, traceback) = sys.exc_info()
        jogobot.output( "\03{red} %s (%s)" % (value, type ),
                        "ERROR" )

    # Bot/Task is active
    else:
        # This factory is responsible for processing command line arguments
        # that are also used by other scripts and that determine on which pages
        # to work on.
        genFactory = pagegenerators.GeneratorFactory()
        # The generator gives the pages that should be worked upon.
        gen = None

        # If always is True, bot won't ask for confirmation of edit (automode)
        always = False

        # If force_reload is True, bot will always parse Countrylist regardless
        # if parsing is needed or not
        force_reload = False

        # Parse command line arguments
        for arg in local_args:
            if arg.startswith("-always"):
                always = True
            elif arg.startswith("-force-reload"):
                force_reload = True
            else:
                pass
                genFactory.handleArg(arg)

        if not gen:
            gen = genFactory.getCombinedGenerator()
        if gen:
            # The preloading generator is responsible for downloading multiple
            # pages from the wiki simultaneously.
            gen = pagegenerators.PreloadingGenerator(gen)
            bot = ChartsBot(gen, always, force_reload)
            if bot:
                bot.run()
        else:
            pywikibot.showHelp()

if( __name__ == "__main__" ):
    main()
