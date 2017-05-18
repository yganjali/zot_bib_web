#!/usr/bin/env python
# coding: utf-8
"""
# A simple way to add a fast, interactive Zotero bibiography in your website.

# This tool will retrieve a set of collections and format an interactive
# bibliography in HTML5.  The bibliography contains BibTeX records and
# abstracts that can be revealed upon clicking.  The output is ready
# to be included in other websites (there are options), and it can be
# easily styles using CSS (see style.css).

# The primary way to configure a web bibliography is via a settings file.
# The file settings.py is loaded by default, if present.
# See settings.example.py for documentation.

# (C) 2014,2015,2016,2017 David Reitter, The Pennsylvania State University
# Released under the GNU General Public License, V.3 or later.

Usage:   zot.py {OPTIONS} [TOPLEVEL_COLLECTION_ID] [OUTPUTFILE]
Example: ./zot.py --group 160464 DTDTV2EP

OPTIONS:
--settings FILE.py   load settings from FILE.  See settings.example.py.
--group GID          set a group library              [library_id; library_type='group']
--user UID           set a user library               [library_id; library_type='user']
--apikey KEY         set Zotero API key               [api_key]
--div                output an HTML fragment          [write_full_html_header=False]
--full               output full html                 [write_full_html_header=True]
--test               implies --full and uses site/ directory
--nocache            do not load nor update cache     [no_cache]

These and additional settings can be loaded from settings.py.

"""


# zot_bib_web

from __future__ import print_function
from __future__ import unicode_literals


####  Program arguments

# zot.py
# zot.py TOPLEVELFILTER
# zot.py TOPLEVELFILTER OUTPUTFILE

#############################################################################

## See settings.example.py for configuration information
## Create settings.py to supply your configuration.

#############################################################################
#############################################################################
#############################################################################
#############################################################################
#############################################################################
#############################################################################
#############################################################################

## The following items are defaults.

__all__ = ['titlestring','bib_style','write_full_html_header', 'stylesheet_url',
           'outputfile', 'category_outputfile_prefix', 'jquery_path', 'number_bib_items',
           'show_copy_button', 'clipboard_js_path', 'copy_button_path', 'show_search_box',
           'show_shortcuts', 'show_links', 'omit_COinS', 'smart_selections',
           'content_filter', 'sort_criteria', 'show_top_section_headings', 'no_cache',
           'language_code', 'sortkeyname_order', 'link_translations']

titlestring = 'Bibliography'
bib_style = 'apa'
write_full_html_header = True
stylesheet_url = "site/style.css"
outputfile = 'zotero-bib.html'
file_outputdir = '' # for associated files
file_output_path = "" # URL path
category_outputfile_prefix = 'zotero'
jquery_path = "site/jquery.min.js"
# jquery_path = "../wp-includes/js/jquery/jquery.js"  # wordpress location
number_bib_items = False
show_copy_button = True
clipboard_js_path = "site/clipboard.min.js"
copy_button_path = "site/clippy.svg"
show_search_box = True
show_shortcuts = ['collection']
show_links = ['abstract', 'url', 'BIB', 'Wikipedia', 'EndNote']
omit_COinS = False
smart_selections = True
content_filter = {'bib': 'fix_bibtex_reference'}  # currently, only this function is supported.

sort_criteria = ['collection', '-year', 'type']
show_top_section_headings = 1

no_cache = False

language_code = 'en'
sortkeyname_order = {}
# Define label for article types and their ordering
# types may occur in libraryCatalog or itemType
# use libraryCatalog to override it in special cases (e.g., archival Conference publications)
sortkeyname_order['en'] = {}
sortkeyname_order['en']['type'] = [
    ('journalArticle', 'Journal Articles'),
    ('archivalConferencePaper', 'Archival Conference Publications'),
    ('conferencePaper', 'Conference and Workshop Papers'),
    ('book', 'Books'),
    ('bookSection', 'Book Chapters'),
    ('edited-volume', "Edited Volumes"),
    ('thesis', 'Theses'),
    ('report', 'Tech Reports'),
    ('attachment', 'Document'),
    ('webpage', 'Web Site'),
    ('presentation', 'Talks'),
    ('computerProgram', 'Computer Programs')]

sortkeyname_order['en']['date'] = sortkeyname_order['en']['year'] = [
    (None, None),  # sort all other values here
    ('in preparation', None),
    ('submitted', None),
    ('in review', None),
    ('accepted', None),
    ('to appear', None),
    ('in press', None)]

sortkeyname_order['de'] = {}
sortkeyname_order['de']['type'] = [
    ('journalArticle', 'Journal-Artikel'),
    ('archivalConferencePaper', u'Konferenz-Veröffentlichungen'),
    ('conferencePaper', 'Konferenz- und Workshop-Papiere'),
    ('book', u'Bücher'),
    ('bookSection', 'Kapitel'),
    ('edited-volume', "Sammlungen (als Herausgeber)"),
    ('thesis', 'Dissertationen'),
    ('report', 'Technische Mitteilungen'),
    ('presentation', u'Vorträge'),
    ('computerProgram', 'Software')]

# Basic translations
link_translations = {}
link_translations['de'] = {'abstract': 'Abstrakt', 'pdf': 'Volltext'}

##### legacy settings
order_by = None  # order in each category: e.g., 'dateAdded', 'dateModified', 'title', 'creator', 'type', 'date', 'publisher', 'publication', 'journalAbbreviation', 'language', 'accessDate', 'libraryCatalog', 'callNumber', 'rights', 'addedBy', 'numItems'
# Note: this does not seem to work with current the Zotero API.
# If set, overrides sort_criteria
sort_order = 'desc'  # "desc" or "asc"
catchallcollection = None
library_id = None
library_type = 'group'
api_key = None
toplevelfilter = None

#############################################################################

__version__ = "2.0.0"

#############################################################################
import sys
import errno
import re


def warning(*objs):
    print("WARNING: ", *objs, file=sys.stderr)


def warn(*objs):
    print(*objs, file=sys.stderr)


from pyzotero import zotero, zotero_errors

try:
    v = float("%d.%02d%02d" % tuple(map(int, zotero.__version__.split(r'.'))))
    if v < 1.0103:
        warning("Pyzotero version is incompatible.  Upgrade to 1.1.3 or later.")
        sys.exit(1)
except SystemExit as e:
    raise e
except:
    warning("Pyzotero version could not be validated. 1.1.3 or later required.")

# redirect warnings (needed for InsecurePlatformWarning on Macs with standard Python)
import logging

logging.basicConfig(filename='zot_warnings.log', level=logging.NOTSET)
logging.captureWarnings(False)

import codecs
from texconv import tex2unicode
import base64

import os

from collections import namedtuple, defaultdict


def load_settings(file="settings.py"):
    try:
        import imp

        # from settings import *
        settings = imp.load_source("settings", file)
        # import settings into local namespace:
        for k, v in settings.__dict__.items():
            if k in globals() and not "__" in k:  # only if default is defined
                globals()[k] = v
                # print(k,v)
        print("Loaded settings from %s." % os.path.abspath(file))

    except ImportError:
        pass
    except IOError:  # no settings file
        warn("%s file not found."%file)


def fetch_tag(tag, default=None):
    result = default
    if tag in sys.argv:
        i = sys.argv.index(tag)
        if len(sys.argv) > i + 1:
            result = sys.argv[i + 1]
            sys.argv = sys.argv[:i] + sys.argv[i + 2:]
        else:
            warn("%s needs a value." % tag)
    return result


def print_usage():
    print(__doc__)


# import argparse
def read_args_and_init():
    global interactive_debugging
    global write_full_html_header, stylesheet_url, outputfile, jquery_path
    global clipboard_js_path, copy_button_path, no_cache, toplevelfilter

    print_usage_and_exit = False

    user = group = api_key = None

    x = fetch_tag("--settings")
    if x:
        load_settings(x)
    else:
        load_settings()

    import_legacy_configuration()

    # To Do: use argparse

    # Parse remaining arguments

    if "--version" in sys.argv:
        print("Zot_bib_web version "+__version__)
        print("Pyzotero version "+zotero.__version__)
        sys.argv.remove('--version')
        
    if "--div" in sys.argv:
        write_full_html_header = False
        sys.argv.remove('--div')
    if "--full" in sys.argv:
        write_full_html_header = True
        sys.argv.remove('--full')
    if "--test" in sys.argv:
        write_full_html_header = True
        stylesheet_url = "site/style.css"
        outputfile = 'zotero-bib.html'
        jquery_path = "site/jquery.min.js"
        clipboard_js_path = "site/clipboard.min.js"
        copy_button_path = "site/clippy.svg"
        sys.argv.remove('--test')
        print("Test mode.  Forcing settings for local testing.")

    if "--nocache" in sys.argv:
        no_cache = True
        sys.argv.remove('--cache')

    if "-i" in sys.argv:
        interactive_debugging = True
        sys.argv.remove('-i')
    else:
        interactive_debugging = False
    if "-h" in sys.argv:
        sys.argv.remove('-h')
        print_usage()
    if "--help" in sys.argv:
        sys.argv.remove('--help')
        print_usage()

    x = fetch_tag("--user")
    if x:
        user = x
        toplevelfilter = None

    x = fetch_tag("--group")
    if x:
        group = x

    api_key = fetch_tag("--apikey", api_key)

    if len(sys.argv) > 1:
        if not sys.argv[1] == "None":
            toplevelfilter = sys.argv[1]
    if len(sys.argv) > 2:
        if not sys.argv[2] == "None":
            outputfile = sys.argv[2]

    # execute
    if user:
        user_collection(user, api_key=api_key, collection=toplevelfilter)
    if group:
        group_collection(group, api_key=api_key, collection=toplevelfilter)

    ###########
    if not include_collections:
        print_usage_and_exit = True
        if len(sys.argv) > 1:
            if user or group:
                warn("No collections found in given libraries.")
            else:
                warn("You must give --user or --group, or add user_collection(..) or group_collection(..) in settings.py.")

    if print_usage_and_exit:
        print_usage()
        sys.exit(1)


###########

def cleanup_lines(string):
    "Remove double line feeds to protect from <P> insertion in Wordpress."
    # Wordpress likes to insert <P>, which is not a good idea here.
    return re.sub(r'\n\s*\n', '\n', string, flags=re.DOTALL)


def generate_base_html():
    global language_code
    # smart selections prevents viewers from copying certain buttons
    # this way, a nice, clean bibliography can be copied right from a browser window
    # this is achieved by displaying the buttons dynamically.
    # caveat - are there accessibility implications?
    possible_items = set(['PDF','PS','DOC','link','Wikipedia','BIB','RIS','EndNote','Abstract', 'File']) # see also button_label_for_object
    blinkitem_css = ""
    for name in possible_items:
        if smart_selections:
            if language_code in link_translations:
                trans = link_translations[language_code].get(name.lower(), name)
            else:
                trans = name
            blinkitem_css += "a.%s::before {content:\"%s\"}\n" % (name, trans)
        else:
            blinkitem_css += "a.%s::before {}\n" % (name)
    blinkitem_css += "a.shortened::before {%s}\n"%('content:"\\229E"' if smart_selections else "")  # hex(8862)

    # Set some (default) styles
    # note - the final style in the style sheet is manipulated by changeCSS
    # this is selected (hack, hack) by index

    style_html = '<style type="text/css" id="zoterostylesheet" ' + ("" if write_full_html_header else "scoped") + """>
.bibshowhide {display:none;}
.bib-venue-short, .bib-venue {display:none;}
""" + blinkitem_css + """
.blink {margin:0;margin-right:15px;padding:0;display:none;}
</style>"""
    script_html = """<script type="text/javascript">
function dwnD(data) {
    filename = "article.ris"
    var pom = document.createElement('a');
    var isSafari = navigator.vendor && navigator.vendor.indexOf('Apple') > -1 && navigator.userAgent && !navigator.userAgent.match('CriOS');
    var mime = (isSafari?"text/plain":"application/x-research-info-systems");
    pom.href = window.URL.createObjectURL(new Blob([atob(data)], {type: mime+";charset=utf-8"}));
    pom.download = filename;
    document.body.appendChild(pom);
    pom.click();
    setTimeout(function(){document.body.removeChild(pom);}, 100);
    return(void(0));}
function showThis(e) {
    elem = e.target;
    if (elem.parentNode) {
	var elems = elem.parentNode.parentNode.getElementsByTagName('*');
	for (i in elems) {
            if((' ' + elems[i].className + ' ').indexOf(' ' + 'bibshowhide' + ' ') > -1)
            { if (elems[i].parentNode != elem.parentNode)
		elems[i].style.display = 'none';
            }}
	elems = elem.parentNode.getElementsByTagName('*');
	for (i in elems) {
            if((' ' + elems[i].className + ' ').indexOf(' ' + 'bibshowhide' + ' ') > -1)
	    { elems[i].style.display = 'block';
	      hideagain = elems[i];
              e.stopPropagation();
	      turnoff = function(e){
		  if (! $.contains(this, e.target))
		      this.style.display = 'none';
		  else
		      $(document).one("click",turnoff_b); // rebind itself
	      }
	      turnoff_b = turnoff.bind(elems[i])
	      $(document).one("click",turnoff_b);
              return(void(0));
            }}}
    return(void(0));}
function changeCSS() {
    if (!document.styleSheets) return;
    var theRules = new Array();
    //ss = document.styleSheets[document.styleSheets.length-1];
    var ss = document.getElementById('zoterostylesheet');
    if (ss) {
	ss = ss.sheet
	if (ss.cssRules)
            theRules = ss.cssRules
	else if (ss.rules)
            theRules = ss.rules
	else return;
	theRules[theRules.length-1].style.display = 'inline';
    }
}
changeCSS();
</script>"""

    if show_copy_button:
        if jquery_path and clipboard_js_path and copy_button_path:
            script_html += """<script type="text/javascript" src="%s"></script>
    <script type="text/javascript" src="%s"></script>
    <script type="text/javascript">
    $(document).ready(function () {
    $('div.bib-item a').click(showThis);
    $("div.bib").append('\\n<button class="btn"><img src="%s" width=13 alt="Copy to clipboard"></button>');
        new Clipboard('.btn',{
text: function(trigger) {
var prevCol = trigger.parentNode.style.color;
trigger.parentNode.style.color="grey";
setTimeout(function(){trigger.parentNode.style.color=prevCol;}, 200);
return trigger.parentNode.childNodes[0].textContent;}});});</script>""" % (
            jquery_path, clipboard_js_path, copy_button_path)
        else:
            warning("show_search_box set, but jquery_path, clipboard_js_path or copy_button_path undefined.")

    credits_html = u'<div id="zbw_credits" style="text-align:right;">A <a href="https://github.com/davidswelt/zot_bib_web">zot_bib_web</a> bibliography.</div>'

    script_html = cleanup_lines(script_html)

    html_header = u''
    html_footer = u''
    if write_full_html_header:
        if stylesheet_url:
            style_html = u"<link rel=\"stylesheet\" type=\"text/css\" href=\"%s\">" % stylesheet_url + style_html
        html_header += u'<!DOCTYPE html><html lang="%s"><head><meta charset="UTF-8"><title>'%language_code + titlestring + u'</title>' + style_html + u'</head><body>'
        html_header += u'<div class="bibliography">' + script_html
        html_footer += credits_html + u'</div>'
        html_header += '<h1 class="title">' + titlestring + "</h1>\n";
        html_footer += u'</body></html>'
    else:
        html_header += u'<div class="bibliography">' + style_html + script_html
        html_footer += credits_html + u'</div>'

    search_box = ""
    if show_search_box or show_shortcuts or show_copy_button:
        search_box += '<script type="text/javascript" src="' + jquery_path + '</script>'

    if show_search_box or show_shortcuts:
        if jquery_path:
            search_box = ''
            if show_search_box:
                search_box += '<form id="pubSearchBox" name="pubSearchBox" style="visibility:hidden;"><input id="pubSearchInputBox" type="text" name="keyword" placeholder="keywords">&nbsp;<input id="pubSearchButton" type="button" value="Search" onClick="searchF()"></form><h2 id="searchTermSectionTitle" class="collectiontitle"></h2>'

            if show_search_box or show_shortcuts:
                search_box += """<script type="text/javascript">
  function getURLParameter(name) {
    return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search)||[,""])[1].replace(/\+/g, '%20'))||null;
  }
  jQuery( document ).ready(function() {
    jQuery('#pubSearchBox,#bib-preamble').css("visibility","visible");
    var kw = getURLParameter("keyword");
    if (kw) {
        jQuery('#pubSearchInputBox').val(kw);
        searchF([kw]);
    }
  });
  jQuery.expr[":"].icontains = jQuery.expr.createPseudo(function(arg) {
    return function( elem ) {
        return jQuery(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
    };});
function searchF(searchTerms, shown, disjunctive) {
  var i=document.pubSearchBox.keyword.value;
  searchTerms = searchTerms || (i!=""&&i.split(" "));
  shown = shown || searchTerms;
  jQuery(".bib-item").css("display", "none");
  var q = ".bib-item";
  if (disjunctive)
  { for (x in searchTerms) {jQuery(".bib-item:icontains('"+searchTerms[x]+"')").css("display", "block");}
  }
  else
  { jQuery.each(searchTerms, function(i,x) {q = q + ":icontains('"+x+"')";});
    jQuery(q).css("display", "block");}
  jQuery("#searchTermSectionTitle").html(searchTerms.length>0?"<a href='#' onclick='searchF([]);'>&#x2715;</a> "+shown:"");
  jQuery(".collectiontitle").parent(".full-bib-section,.short-bib-section").css("display", "block");
  jQuery(".collectiontitle").parent(".full-bib-section,.short-bib-section").each(function(){
    var y = jQuery(this).find(".bib-item:visible");
    if (y.length==0) {jQuery(this).css("display","none");}
  });
}
  jQuery(function() {    // <== Doc ready
  // stackoverflow q 3971524
    var inputVal = jQuery("#pubSearchInputBox").val(),
        timer,
        checkForChange = function() {
            var self = this; // or just use .bind(this)
            if (timer) { clearTimeout(timer); }
            // check for change of the text field after each key up
            timer = setTimeout(function() {
                if(self.value != inputVal) {
                    searchF();
                    inputVal = self.value
                }
            }, 250);
        };
    jQuery("#pubSearchInputBox").bind('keyup paste cut', checkForChange);
});</script>"""
        else:
            warning("show_search_box or show_shortcut are set, but jquery_path undefined.")
    return html_header, search_box, html_footer


try:
    from dateutil.parser import parse
except ImportError:
    parse = False
    pass


def basicparse(value):
    "Parse a date.  Cheap substitute for dateutil.parser. Returns a sortable string."
    value = re.sub(r'(\s|\.|st|nd|rd|th|,)', '-', value)
    value = value.replace('--', '-')
    year = value
    m = re.match(r'\s*(.*)\s*([0-9][0-9][0-9][0-9])\s*(.*)', value)
    if m:
        year = m.group(2)
        if not m.group(1) == '':  # year not already at beginning of string?
            value = m.group(2) + '-' + m.group(1) + m.group(3)  # rough approximation
    else:
        nums = re.split(r'[\s/\.]', value)
        if len(nums) > 1:
            value = "-".join(reversed(nums))
        if len(nums) > 0:
            year = nums[0]
    for i, mo in enumerate(re.split(r' ', "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec")):
        value = value.replace(mo, str(i + 1))
    value = re.sub(r'\b([0-9])\b', r'0\1', value)
    value = re.sub(r'-$', '', value)
    return value, year


SortAndValue = namedtuple('SortAndValue', ['sort','value'])

def sortkeyname(field, value):
    global sortkeyname_dict
    # field may be a single field, or a list of fields
    # value corresponds to field

    sort_prefix = ""

    # value may be none (e.g., for venue)
    # In that case, we will resort to the default entry in sortkeyname

    if value and not is_string(value):  # isinstance(value, list):
        # it's a path of something
        # sorting by all the numbers (if available).
        # e.g., 10.13, and displaying the last entry
        if 'collection' == field:
            return SortAndValue(".".join([str(sortkeyname(field, value2).sort) for value2 in value]), sortkeyname(field, value[-1]).value)
        else:
            return SortAndValue(".".join([str(sortkeyname(field2, value2).sort) for field2, value2 in zip(field, value)]), \
                   sortkeyname(field[-1], value[-1]).value)
    if field == "collection":
        if  Coll.hideSectionTitle(value):
            sort_prefix, name, value = "","",value
        else:
            name = Coll.findName(value)  # value is an ID
            sort_prefix, _, value = collname_split(name)
    if field == "date":
        if parse:
            try:
                dt = parse(value, fuzzy=True)
                sort_prefix = dt.isoformat()
                value = str(dt.year)
            except ValueError:  # dateutil couldn't do it
                sort_prefix, value = basicparse(value)
        else:
            sort_prefix, value = basicparse(value)

    if field in sortkeyname_dict:
        if value in sortkeyname_dict[field]:
            s, value = sortkeyname_dict[field][value]  # this is (sort_number, label)
            sort_prefix = str(s) + " " + sort_prefix
        elif None in sortkeyname_dict[field]:  # default for unknown values
            sort_prefix = str(sortkeyname_dict[field][None][0]) + " " + sort_prefix

    sort_prefix = sort_prefix or ""
    value = value or ""

    return SortAndValue(" ".join([sort_prefix, value.lower()]), value) # sort by value


sort_reverse=[]
def import_legacy_configuration():
    global order_by
    global sort_criteria
    global sort_reverse
    global catchallcollection
    global show_links

    if library_id and library_type:
        if library_type == 'group':
            group_collection(library_id, api_key=api_key, collection=toplevelfilter, top_level=False)
        elif library_type == 'user':
            user_collection(library_id, api_key=api_key, collection=toplevelfilter, top_level=False)
    if catchallcollection:
        warn('catchallcollection setting no longer available. Ignoring.\n'
             'Use & modifier for collection name (e.g., "& Miscellaneous") and,\n'
             'if necessary, the new group_collection or user_collection statement, e.g.:\n'
             'user_collection(library_id, collection = ["%s"])' % catchallcollection)

    if order_by:  # set by user (legacy setting)
        sort_critera = ['collection', order_by]
    else:
        order_by = 'date'

    # find sort order for each criterion
    sort_reverse = []
    for i, c in enumerate(sort_criteria):
        if c[0] == '-':
            sort_criteria[i] = c[1:]
            sort_reverse += [True]
        else:
            sort_reverse += [False]

    show_links = [i.lower() for i in show_links]


def index_configuration():
    global sortkeyname_order
    global sortkeyname_dict
    global language_code
    # Not using OrderedDict (Python 2.7), because it does not actually
    # indicate the index of an item by itself
    if not language_code in sortkeyname_order:
        language_code = 'en'  # fallback - should be present.

    # use val as default if it is given as None
    sortkeyname_dict = {key: {val: (idx, mappedVal or val) for idx, (val, mappedVal) in enumerate(list(the_list))} for
                        key, the_list in sortkeyname_order[language_code].items()}


class ZotItem:
    __classversion__ = 4
    def __init__(self, entries):
        self.__version__ = ZotItem.__classversion__
        self.key = None
        self.creators = None
        self.event = None
        self.section_keyword = set()
        self.url = None
        self.collection = []
        self.type = None
        self.date = None
        self.libraryCatalog = None  # special setting, overrides u'itemType' for our purposes
        self.note = None
        self.journalAbbreviation = None
        self.conferenceName = None
        self.meetingName = None
        self.publicationTitle = None
        self.shortTitle = None
        self.series = None
        self.extra = None
        self.uniqueID = None # will be set by detect_and_merge_doubles
        self.filename = None
        self.parentItem = None
        self.__dict__.update(entries)
        # Will be set later - None is a good default
        self.bib = None
        self.ris = None
        self.html = None
        self.coins = None
        self.wikipedia = None
        self.saved_filename = None
        self.attachments = []

        # populate calculated values
        self.year = self.getYear()
        # allow libraryCatalog to override itemType
        self.type = self.libraryCatalog or self.itemType

    def addAttachment(self, zotItem):
        self.attachments += [zotItem]

    def access(self, key, default=""):
        if key == 'year':
            if self.year:
                return str(self.year)
            if self.date:
                return self.date
        if key == 'venue':
            return self.venue()
        if key == 'venue_short':
            return self.venue_short()
        if key in self.__dict__ and self.__dict__[key]:
            return self.__dict__[key]
        return default  # default
        # raise RuntimeError("access: field %s not found."%key)

    def getYear(self):
        if self.date:
            m = re.search('[0-9][0-9][0-9][0-9]', self.date)
            if m:
                return int(m.group(0))
        return None

    def venue(self):
        return self.publicationTitle or self.conferenceName

    def venue_short(self):
        def maybeshorten(txt):
            if txt:
                m = re.search(r'\(\s*([A-Za-z/]+(\-[A-Za-z]+)?)\s*\-?\s*[0-9]*\s*\)', txt)
                if m:
                    return m.group(1)
                m = re.match(r'^([A-Za-z/]+(\-[A-Za-z]+)?)\s*\-?\s*[0-9]*$', txt)
                if m and len(m.group(1)) < 11:
                    return m.group(1)
                if len(txt) < 11:
                    return txt  # return whole conference if short

        # print(pprint.pformat(self.__dict__))
        return self.journalAbbreviation or maybeshorten(self.conferenceName) or maybeshorten(
            self.meetingName) or maybeshorten(self.publicationTitle) or maybeshorten(self.shortTitle) or maybeshorten(self.series)

    # or self.shortTitle or self.series

    def addSectionKeyword(self, s):
        if not s in self.section_keyword:
            self.section_keyword.add(s)


def write_bib(items, outfile):
    file = codecs.open(outfile, "w", "utf-8")

    for item in items:
        file.write(item)

    file.close()


#  Atom bib entry:
# {u'publisher': u'Routledge Psychology Press', u'author': [{u'given': u'David', u'family': u'Reitter'}], u'collection-title': u'Frontiers of Cognitive Psychology', u'issued': {u'raw': u'January 2017'}, u'title': u'Alignment in Web-based Dialogue: Who Aligns, and how Automatic is it? Studies in Big-Data Computational Psycholinguistics', u'editor': [{u'given': u'Michael N.', u'family': u'Jones'}], u'container-title': u'Big Data in Cognitive Science', u'type': u'chapter', u'id': u'1217393/IVR7H8TD'}





def format_bib(bib):
    return bib.replace("},", "},\n")


def format_ris(bib):
    return bib.replace("\n", "\\n").replace("\r", "\\r")


def fix_bibtex_reference(bib, _thisatom, _allatoms):
    "Fix reference style for BIB entries: use authorYEARfirstword convention."
    sub = re.sub(r'(?<=[a-z\s]{)(?P<name>[^_\s,]+)_(?P<firstword>[^_\s,]+)_(?P<year>[^_\s,]+)(?=\s*,\s*[\r\n])',
                 "\g<name>\g<year>\g<firstword>", bib, count=1)
    return sub or bib


def extract_abstract(bib):
    m = re.match(r'(.*)abstract\s*=\s*{?(.*?)}\s*(,|})(.*)', bib, re.DOTALL | re.IGNORECASE)
    if m:
        a = m.group(2)
        b = m.group(1) + m.group(4)
        a = a.replace("{", "")
        a = a.replace("}", "")
        a = a.replace("\?&", "&amp;")
        a = a.replace("&", "&amp;")
        a = a.replace("<", "&lt;")
        a = a.replace(">", "&gt;")
        a = a.replace("\\textless", "&lt;")
        a = a.replace("\\textgreater", "&gt;")
        a = a.replace("\\textbar", "|")
        return tex2unicode(a), b
    return None, bib


def write_some_html(body, outfile, title=None):
    global html_header
    global html_footer
    file = codecs.open(outfile, "w", "utf-8")
    file.write(html_header)
    if title:
        file.write('<h1 class="title">' + title + "</h1>")
    file.write(body)
    file.write(html_footer)
    file.close()
    print("Output written to %s." % outfile)


def flexible_html_regex(r):  # To Do: request non-HTML output from Zotero instead
    r = re.escape(r)
    r = r.replace("\\&", r"(&amp;|\\&)")
    r = r.replace("\\<", r"(&lt;|\\<)")
    r = r.replace("\\>", r"(&gt;|\\>)")
    r = r.replace(" ", r"\s+")
    r = r.replace(u" ", r"[\s ]+")  # repl string was "ur" - todo: check
    return r


def tryreplacing(source, strings, repl):
    for s in strings:
        if s in source:
            repl2 = repl.replace("\\0", s)
            return source.replace(s, repl2)
        r = flexible_html_regex(s)
        if re.search(r, source):
            repl2 = repl.replace("\\0", s)
            return re.sub(r, repl2, source)
    # print("not successful: ", source, strings)
    return source


try:  # python 2/3 compatibility
    basestring
except NameError:
    basestring = str


def is_string(s):
    return isinstance(s, basestring)


def coll_data(c):
    if not (u'key' in c and u'name' in c) and u'data' in c:
        c = c[u'data']
    return c


def coll_key(c):
    if u'key' in c:
        return c[u'key']
    return c[u'data'][u'key']


def coll_name(c):
    return coll_data(c)[u'name']


def collname_split(name):  # returns sort_prefix,modifiers,value
    m = re.match(r'([0-9]*)([\s\*\-!\^\&]*)\s(.*)', name)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return "", "", name


class Coll:   # To do: make collection an object
    collection_info = {}

    @staticmethod
    def findName(key):
        return Coll.find(key).name  # error out if unsuccessful!

    @staticmethod
    def find(key):
        if key in Coll.collection_info:
            return Coll.collection_info[key]
        return None

    @staticmethod
    def findSimilar(keyword):
        if keyword in Coll.collection_info:
            return [Coll.find(keyword)]
        sims = []
        for k, c in Coll.collection_info.items():
            if keyword == c.name or keyword == sortkeyname('collection', k).value:
                sims += [c]
        return sims

    @staticmethod
    def add(code, name, depth, parents, db):
        c = Coll(code, name, depth, parents, db)
        Coll.collection_info[code] = c
        return c


    @staticmethod
    def is_short_collection(section_code):
        "Show abbreviated entries for items in this collection"
        return Coll.is_special_collection(section_code, "*")


    # def is_exclusive_collection(section_code):
    #     "Show items in this collection, and do not show them in regular collections"
    #     return is_special_collection(section_code, "^")

    @staticmethod
    def is_featured_collection(section_code):
        """Regardless of sort_criteria, show this collection
    at the top of the bibliography"""
        return Coll.is_special_collection(section_code, "!")

    @staticmethod
    def is_hidden_collection(section_code):
        "Hide items in this collection."
        return Coll.is_special_collection(section_code, "-")

    @staticmethod
    def is_misc_collection(section_code):
        "Show only those items in this collection that are not contained elsewhere"
        return Coll.is_special_collection(section_code, "&")

    @staticmethod
    def is_regular_collection(s):
        "Regular collection: not featured, short, hidden or misc"
        return not (Coll.is_short_collection(s) or Coll.is_featured_collection(s)
                    or Coll.is_hidden_collection(s) or Coll.is_misc_collection(s))

    @staticmethod
    def is_special_collection(section_code, special):
        if not is_string(section_code):
            return any([Coll.is_special_collection(x, special) for x in section_code])
        c = Coll.find(section_code)
        if c:  # it's a collection key
            return special in collname_split(c.name)[1]
        # if it's not a section key, then it doesn't indicate a short section
        return False

    @staticmethod
    def get_featured_collections(section_code):
        return filter(lambda x: Coll.is_featured_collection(x), section_code)

    @staticmethod
    def hideSectionTitle(section_code):
        c = Coll.find(section_code)
        if c:  # it's a collection key
            return c.hideSectionTitle
        return False

    def __init__(self, key, name, depth, parents, db):
        self.key = key
        self.name = name
        self.depth = depth
        self.parents = parents
        self.db = db
        self.hideSectionTitle = False


def strip(string):
    stripped = string.lstrip("0123456789*!- ")
    if stripped == "":
        return string
    return stripped


def last(string_or_list):
    if not is_string(string_or_list):
        return string_or_list[-1]
    return string_or_list


def js_strings(string_or_list):
    if is_string(string_or_list):
        return '"%s"' % string_or_list
    return ",".join(map(js_strings, string_or_list))


class Shortcut:
    def __init__(self, crit, values=None, topN=None, sortBy=None, sortDir='auto'):
        self.crit = crit
        self.levels = values
        self.sortDir = sortDir

        self.topN = topN
        self.catInfo = None
        self.sortBy = sortBy

    def setAllItems(self, all_items):
        self.all_items = all_items

    def getValueForUniqueItems(self):
        u = []
        uid = set()
        for i in self.all_items:
            if not i.uniqueID in uid:
                uid.add(i.uniqueID)
                v = i.access(self.crit)
                if not (self.crit=='collection' and Coll.hideSectionTitle(last(v))):
                    u += [v]
        #u = set([(i.access(self.crit), i.key) for i in self.all_items])
        #        return list([v for v, _id in u if v])
        return u

    def sort_crit_in_reversed_order(self):
        "We adopt the same sort order for the short cuts as for the sections and items within sections"
        global sort_criteria, sort_reverse
        if self.crit in sort_criteria:
            return sort_reverse[sort_criteria.index(self.crit)]
        if self.crit == 'date' and 'year' in sort_criteria:
            return sort_reverse[sort_criteria.index('year')]
        if self.crit == 'year' and 'date' in sort_criteria:
            return sort_reverse[sort_criteria.index('date')]
        return False

    def compile(self):
        Category = namedtuple('Category', ['vals', 'sortname', 'title', 'items'])
        self.catInfo = []
        l = self.getLevels()
        for sortname, section_print_title, feature_value in l:
            # if multiple items are listed in feature_value because it's a list,
            # we need to retrieve items for these separately
            fvs = feature_value if isinstance(feature_value, list) else [feature_value]
            items = []
            vals = []
            title = None
            for f in fvs:
                val1, title1, items1 = self.getBibItems(f, section_print_title)
                items += items1  # this is the key
                vals += [val1]
                title = title or title1  # use the first title
            self.catInfo += [Category(vals, sortname, title, items)]
        if self.sortDir or self.sortBy:
            if self.sortDir == 'auto':
                if self.levels:  # if levels are given explicitly
                    sort = False  # do not sort at all
                else:
                    sort = 'desc' if self.sort_crit_in_reversed_order() else 'asc'
            else:
                sort = self.sortDir

            if sort:  # sort?

                if self.sortBy == 'count':
                    k = lambda x: len(x.items)
                elif self.sortBy == 'name':
                        k = lambda x: x.title # by title
                else: # by sort name
                    k = lambda x: x.sortname  # sort by sort name (as given by sortkeyname)
                self.catInfo.sort(key=k, reverse=(sort == 'desc'))

    def getCatValueInfo(self):
        if self.topN:
            lens = sorted([len(tup.items) for tup in self.catInfo])
            if len(lens) > self.topN:
                cutoff = lens[-self.topN]
                return [tup for tup in self.catInfo if len(tup.items) >= cutoff]
        return self.catInfo

    @staticmethod
    def uniquify(seq, idfun=None):
        # return only unique items out of a sequence
        # order preserving
        if idfun is None:
            def idfun(x): return x
        seen = {}
        result = []
        for item in seq:
            marker = idfun(item)
            # in old Python versions:
            # if seen.has_key(marker)
            # but in new ones:
            if marker in seen: continue
            seen[marker] = 1
            result.append(item)
        return result

    def getLevels(self):
        def fit(v):  # first if tuple
            if isinstance(v, list):  # multiple items listed - use first for label
                return str(v[0])
            return str(v)

        if self.levels:  # e.g., ('type', [v1,v2,v3]) - given in settings
            l = [(sortkeyname(self.crit, fit(lev)).sort, fit(lev), lev) for lev in self.levels if lev]
        else:
            l = [sortkeyname(self.crit, lev) + (lev,) for lev in self.getValueForUniqueItems()]
        l = filter(lambda snv: snv[1], l)
        l = self.uniquify(l, idfun=lambda x: x[0])
        return l

    def getBibItems(self, crit_val, section_print_title):
        crit_val = last(crit_val) if self.crit == "collection" else str(crit_val)  # if collection, get its ID
        allvalues = [True]  # keep by default
        counter = None
        if self.crit == 'year':
            # Allow for range specification in years
            # We will search for all appropriate years using the JS search function.
            m = re.match(r'([0-9]*)-([0-9]*)', crit_val)
            if m and (m.group(1) or m.group(2)):
                fromyear = int(m.group(1) or 0)
                toyear = int(m.group(2) or 3000)

                allvalues = list(self.getValueForUniqueItems())

                def inrange(y):
                    try:
                        return (int(y) >= fromyear and int(y) <= toyear)
                    except ValueError:
                        return False
                    except TypeError:
                        return False

                allvalues = list(filter(inrange, allvalues))
                crit_val = map(lambda y: "year__%s" % y, set(allvalues))
                section_print_title = "%s&ndash;%s" % (m.group(1), m.group(2))
            else:
                # Currently, we're only filtering for the years, because that is were it is practically relevant
                allvalues = list(
                    filter(lambda y: (str(y) == str(crit_val)), self.getValueForUniqueItems()))
                crit_val = 'year__' + crit_val
        elif self.crit == 'collection':
            allvalues = list(filter(lambda y: (crit_val in y), self.getValueForUniqueItems()))
        elif self.crit in ['type', 'venue_short']:
            allvalues = list(filter(lambda y: (str(y) == str(crit_val)), self.getValueForUniqueItems()))
            crit_val = self.crit + '__' + crit_val
        return crit_val, section_print_title, allvalues


def shortcut(crit, values=None, topN=None, sortDir='auto', sortBy=None):
    """Make a shortcut for Zot/Bib/Web's show_shortcuts variable.

    CRIT     The criterion as a string, selected by the shortcut.
             Permissible values include 'collection', 'year', 'type', 'venue', and 'venue_short'.

    VALUES   Optional list of values to be show for the criterion.  Each element may be string,
             or an int (if appropriate, for years).  For numbers, strings may specify a range, e.g.,
             "2004-2009" (to select the range of years), or "-2004" or "2010-" to select years
             before or after the given year, respectively.

    TOPN     If given, only show the TOPN values with the most bibliographic entries.

    SORTDIR  Direction of sorting.  If given, 'asc' or 'desc', or None (to turn off sorting).

    SORTBY   May be given as 'count', which indicates sorting by the number of bibliographic entries
             covered by each value, or 'name', to sort by name.  The canonical order is default.
    """
    return Shortcut(crit, values=values, sortDir=sortDir, topN=topN, sortBy=sortBy)


try:
    import __builtin__
except ImportError:
    # Python 3
    import builtins as __builtin__


__builtin__.sortkeyname_order = sortkeyname_order

__builtin__.push_wordpress = lambda *args,**kwargs: None

__builtin__.shortcut = shortcut
__all__ += ['shortcut']

def make_header_htmls(all_items):
    # ordering:
    # sort collections as they are normally sorted (sortkeyname)

    headerhtmls = []  # {'collection':u"", 'year':u"", 'type':u""}
    for complex_crit in show_shortcuts:

        if is_string(complex_crit):
            complex_crit = Shortcut(complex_crit)

        vals = None
        crit = complex_crit.crit
        if crit == 'date':
            crit = 'year'

        complex_crit.setAllItems(all_items)
        complex_crit.compile()

        html = ""
        for info in complex_crit.getCatValueInfo(): # get info on the bib items associated with a category value (e.g., year=2007)
            # info: 'vals', 'sortname', 'title', 'items'
            if not info.items:  # empty result set (no items for this search, if type or year search)
                print("Warning: %s %s not found, but mentioned in shortcuts. Skipping." % (crit, info.vals))
            else:
                # collection does not need to be marked
                if hasattr(info.items, '__iter__'):
                    counterStr = " (%s)" % len(info.items)
                else:
                    counterStr = ""
                html += "<li class='link'><a style='white-space: nowrap;' href='#' onclick='searchF([%s],\"%s\",1);return false;'>%s<span class='cat_count'>%s</span></a></li>\n" % (
                js_strings(info.vals), info.title, info.title, counterStr)
        headerhtmls += [html]

    return headerhtmls


entry_count = 0

def div(cls=None, content="", style=None):
    "Helper that creates a HTML DIV element."
    s = u' style="%s"'%style if style else u''
    c = u' class="%s"' % cls if cls else u''
    return u'<div%s%s>%s</div>'%(c,s,content)

def make_html(all_items, exclude={}, shorten=False):
    """Produce the HTML for ALL_ITEMS.
    EXCLUDE certain items.
    SHORTEN the produced output for featured collections.
    """
    def a_button(name, url=None, js=None, title=None, cls=None):
        global smart_selections
        global language_code
        if js:
            js = 'onclick="%s"'%js
        else:
            js = '' # binding happens at doc level
        if not url:
            url = ""
        else:
            url = 'href=\"%s\"' % url
        if not cls:
            cls = name
        title2 = ""
        if title:
            title2 = "title=\"%s\"" % title
        if language_code in link_translations:
            name = link_translations[language_code].get(name.lower(), name)
        return u"<a class=\"%s\" %s %s %s>%s</a>" % (
        cls, title2, url, js, ("" if smart_selections else name))

    def button_label_for_object(obj, default):
        if re.search(r'\.pdf$', obj, re.IGNORECASE):
            n = 'pdf'
        elif re.search(r'\.docx?$', obj, re.IGNORECASE):
            n = 'doc'
        elif re.search(r'\.ps$', obj, re.IGNORECASE):
            n = 'ps'
        else:
            n = default
        return n

    count = 0
    string = ""
    for item in all_items:
        if item.key not in exclude:
            if item.title:

                count += 1

                htmlitem = item.html

                global show_links
                show_items = show_links # not a copy
                t = item.title
                u = None
                if item.url:
                    u = item.url

                t2 = t.replace(u"'", u'’')  # technically, we're going to have to do much more (or do a flexible match)
                t_to_replace = ["<i>" + t + "</i>.", "<i>" + t2 + "</i>.", "<i>" + t + "</i>", "<i>" + t2 + "</i>",
                                t + ".", t2 + ".", t, t2]
                if u:
                    new = tryreplacing(htmlitem, t_to_replace,
                                       u"<span class=\"doctitle\"><a class=\"doctitle\" href=\"%s\">%s</a></span>" % (
                                       u, "\\0"))

                    if new == htmlitem:
                        # replacement not successful
                        if not 'pdf' in show_items and not 'url' in show_items:
                            show_items = show_items + ['pdf'] # make copy
                    else:
                        # remove "Retrieved from"
                        # URL detector from http://daringfireball.net/2010/07/improved_regex_for_matching_urls
                        new = re.sub(
                            r"Retrieved from (?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?]))",
                            "", new)
                        # this is the new item
                        htmlitem = new
                else:
                    htmlitem = tryreplacing(htmlitem, t_to_replace, u"<span class=\"doctitle\">%s</span>" % ("\\0"))

                if item.extra:
                    htmlitem += div('bib-extra', item.extra)

                # Insert searchable keywords (not displayed)
                search_tags = ''
                if item.section_keyword:
                    search_tags += " ".join(item.section_keyword)  # no special tag for collections
                search_tags += " year__" + item.access('year')  # no search by date
                if item.venue_short():
                    search_tags += " venue_short__" + item.venue_short()
                if item.type:
                    search_tags += " type__" + item.type
                htmlitem += "<span class='bib-kw' style='display:none;'>%s</span>" % search_tags

                htmlitem = div('bib-details', htmlitem)

                venue = item.venue()
                if venue:
                    htmlitem += div('bib-venue', venue)
                venue_short = item.venue_short()
                if venue_short:
                    htmlitem += div('bib-venue-short', venue_short)

                if shorten:

                    ct = item.publicationTitle or item.journalAbbreviation or item.event or u""
                    if item.note and (len(item.note) < len(ct) or ct == u""):
                        ct = item.note

                    y = ""
                    if item.date:
                        y = "(%s)" % item.date

                if item.bib:
                    abstract, bibitem2 = extract_abstract(item.bib)
                    blinkitem = u""

                    # we print the original item name as label so that capitalization may be chosen via the items list
                    for show in show_items:
                        sl = show.lower()
                        bi = ""
                        if 'abstract' == sl and abstract:
                            bi = a_button('Abstract') + div('bibshowhide', div('abstract', abstract))
                        elif 'wikipedia' == sl and item.wikipedia:
                            bi = a_button('Wikipedia') + div('bibshowhide', div('bib', item.wikipedia, style='white-space:pre-wrap;'))
                        elif 'bib' == sl and bibitem2:
                            bi = a_button('BIB') + div('bibshowhide', div('bib', bibitem2))
                        elif 'file' == sl:
                            bi = u''
                            for a in item.attachments:
                                if a.saved_filename: #a.itemType=='attachment':
                                    bi += a_button(button_label_for_object(a.saved_filename, 'File'), url=file_output_path+'/'+a.saved_filename)
                        elif 'note' == sl:
                            for a in item.attachments:
                                if a.itemType == 'note' and a.note:
                                    bi = a_button('Note') + div('bibshowhide', div('note', a.note))
                        elif (sl == 'pdf' or sl == 'url') and u:
                            # automatically detect what the link points to
                            n = button_label_for_object(u, 'link')
                            bi = a_button(n, url=u, cls=n.lower())
                        elif 'ris' == sl and item.ris:
                            bi = '<a class="%s" title="Download RIS record" onclick="dwnD(\'%s\');return false;"></a>' % ('RIS', base64.b64encode(item.ris.encode('utf-8')).decode('utf-8'))
                        elif 'endnote' == sl and item.ris:  # EndNote = RIS
                            bi = '<a class="%s" title="Download EndNote record" onclick="dwnD(\'%s\');return false;"></a>' % ('EndNote', base64.b64encode(item.ris.encode('utf-8')).decode('utf-8'))
                        else:
                            continue
                        blinkitem += div('blink', bi)

                    if not omit_COinS and item.coins:
                        blinkitem += str(item.coins).strip()

                    if shorten:  # to do - consider moving this to the CSS
                        blinkitem = div(None, blinkitem, style="padding-left:20px;")

                    htmlitem += div('blinkitems', blinkitem)

                if shorten:
                    htmlitem = u"<a href=\"#\">&#8862;</a> <span class=\"doctitle-short\">%s</span> <span class=\"containertitle\">%s</span> %s" % (
                    t, ct, y) + "<div class=\"bibshowhide\" style=\"padding-left:20px;\">" + htmlitem + "</div>"
                    htmlitem = div(None, htmlitem)  # to limit what is being expanded

                tag = "li" if number_bib_items else "div"
                htmlitem = u'<%s class="bib-item">' % tag + htmlitem + u'</%s>' % tag
                string += htmlitem

    if len(string) == 0:
        return "", 0  # avoid adding title for section later on

    if number_bib_items:
        string = u'<ol>' + string + u'</ol>'

    global entry_count
    entry_count += count

    return cleanup_lines(string), count


include_collections = []
item_filters = []

def group_collection(id, api_key=None, collection=None, top_level=False):
    global include_collections
    include_collections += [('load', DBInstance.create(id, 'group', api_key), collection, top_level)]

def user_collection(id, api_key=None, collection=None, top_level=False):
    global include_collections
    include_collections += [('load', DBInstance.create(id, 'user', api_key), collection, top_level)]

def exclude_collection(collection, top_level_only=False):
    global include_collections
    include_collections += [('exclude', collection, top_level_only)]

def rename_collection(collection, newName):
    global include_collections
    include_collections += [('rename', collection, newName)]

def exclude_items(filter):
    """After all items are loaded, filter them using a function.
    The function given in FILTER takes one argument, ITEM, and
    returns True for each item to exclude.
    ITEM is of type ZotItem."""
    global item_filters
    item_filters += [filter]


__builtin__.user_collection = user_collection
__builtin__.group_collection = group_collection
__builtin__.exclude_collection = exclude_collection
__builtin__.rename_collection = rename_collection
__builtin__.exclude_items = exclude_items

__all__ += ['user_collection', 'group_collection', 'exclude_collection', 'rename_collection', 'exclude_items']


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

import zipfile
class DBInstance:

    dbInstanceCache = {}
    @staticmethod  # factory method
    def create(library_id, library_type, api_key):

        self = DBInstance()
        try:
            return DBInstance.dbInstanceCache[(library_id, library_type, api_key)]
        except KeyError: # not found
            pass

        self.zot=None
        self.zotLastMod = None
        try:
            self.zot = zotero.Zotero(library_id, library_type, api_key)
            self.zotLastMod = self.zot.last_modified_version()  # v1.1.1

            DBInstance.dbInstanceCache[(library_id, library_type, api_key)] = self

            if library_type == 'group':
                print("Loading: https://www.zotero.org/groups/%s/items" % library_id)
            else:
                print("Loading: %s" % library_id)

        except zotero_errors.UserNotAuthorised:
            print("UserNotAuthorised: Set correct Zotero API key in settings.py for library ID %s."%library_id, file=sys.stderr)
            raise SystemExit(1)

        return self

    # Interface to external database

    def traverse(self, agenda, depth=0, parents=[]):
        result = []
        # sort agenda by name
        for collitem in sorted(agenda, key=coll_name):
            key = coll_key(collitem)
            name = coll_data(collitem)[u'name']
            c = self.zot.collections_sub(key)

            result += [Coll.add(key, name, depth, parents, self)]
            result += self.traverse(c, depth + 1, parents + [key])
        return result

    # public
    def get_collections(self, topcollection, top_level):
        try:
            if topcollection:
                colls = self.traverse([self.zot.collection(topcollection)])

                if not top_level:
                    colls[0].hideSectionTitle=True  # the topmost one should be hidden

               # if top_level:
              #      print("Fetching top-level collection ", topcollection)
              #  else:
             #       colls = self.traverse(self.zot.collections_sub(topcollection))
            else:
                print("Fetching all collections:")
                colls = self.traverse(self.zot.collections())

            colls = filter(lambda e: e, colls)  # remove empties
            return colls

        except zotero_errors.UserNotAuthorised:
            print("UserNotAuthorised: Set correct Zotero API key in settings.py and allow access.", file=sys.stderr)
            raise SystemExit(1)


    def retrieve_x(self, collection, **args):
        items = self.zot.everything(
            self.zot.collection_items(collection, order=order_by, sort=sort_order,
                                    **args))
        return items

    def retrieve_bib(self, collection, content, style):
        return self.retrieve_x(collection, content=content, style=style)

    def retrieve_atom(self, collection):
        return self.retrieve_x(collection, content='csljson', format='atom')

    def retrieve_coins(self, collection):
        return self.retrieve_x(collection, content='coins')

    def retrieve_wikipedia(self, collection):
        return self.retrieve_x(collection, content='wikipedia')

    # public
    def retrieve_data(self, collection_id, exclude=None):
        def check_show(s):
            global show_links
            s = s.lower()
            for x in show_links:
                if x.lower() == s:
                    return True
            return False

        def cfilter(atom, type, content):
            if content_filter and type in content_filter:
                fun = content_filter[type]
                return [globals()[fun](item, thisatom, atom) for item, thisatom in zip(content, atom)]
            return content


        if not no_cache:
            cache_name = ".cache/%s.cache" % collection_id
            try:
                date, lm, bs, zv, items = pickle.load(open(cache_name, 'rb'))
                if date > datetime.now() - timedelta(days=14):  # cache expires after 14 days
                    if self.zotLastMod == lm and bs == bib_style:
                        if len(items)==0 or (hasattr(items[0], '__version__') and items[0].__version__ == ZotItem.__classversion__ and zv == zotero.__version__):
                            return items
                    #else:
                        #print("Not using cache %s (library modified)"%cache_name)
            except (IOError, ValueError, pickle.PicklingError, TypeError, EOFError) as e:
                # print("Not using cache - some error ", e)
                pass

        # ii = zot.everything(zot.collection_items(collection_id))
        ii = self.retrieve_x(collection_id)

        a = [ZotItem(i['data']) for i in ii]

        # PyZotero can retrieve different formats at once,
        # but this does not seem to work with current versions of the library or API

        b = cfilter(a, 'bib', self.retrieve_bib(collection_id, 'bibtex', ''))
        h = cfilter(a, 'html', self.retrieve_bib(collection_id, 'bib', bib_style))
        if check_show('EndNote') or check_show('RIS'):
            r = cfilter(a, 'ris', self.retrieve_bib(collection_id, 'ris', ''))
        else:
            r = [None for _x in h]
        if not omit_COinS:
            c = cfilter(a, 'coins', self.retrieve_coins(collection_id))
        else:
            c = [None for _x in h]
        if check_show('wikipedia'):
            w = cfilter(a, 'wikipedia', self.retrieve_wikipedia(collection_id))
        else:
            w = [None for _x in h]

        for bi, hi, ri, ci, wi, ai in zip(b, h, r, c, w, a):
            ai.bib = bi
            ai.html = hi
            ai.ris = ri
            ai.coins = ci
            ai.wikipedia = wi

        if not no_cache:
            make_sure_path_exists(os.path.dirname(cache_name))
            pickle.dump((datetime.now(), self.zotLastMod, bib_style, zotero.__version__, a),
                        open(cache_name, 'wb'))

        return a

    def arrangeAttachments(self, items):
        # Get attachments (separately)
        itemindex = {item.key:item for item in items}
        filtered = []
        for i in items:
            if i.parentItem:
                if i.parentItem in itemindex:
                    item = itemindex[i.parentItem]
                    item.addAttachment(i)
                    continue
            filtered += [i]  # was not added to another item
        return filtered

    def dumpFiles(self, item):
        global file_outputdir
        if item.attachments:
            for a in item.attachments:
                self.dumpFiles(a)
        if item.filename:
 
            def dump(item, p, fn):
                # Dump file into filename fn at path p
                # Returns the filename if successful
                outfile = os.path.join(p,fn)
                # uses zot
                try:
                    with open(outfile, 'wb') as f:
                        f.write(self.zot.file(item.key))
                    return fn # default
                except ValueError:
                    warn("Failed to save file %s into %s (%s), content type %s."%(item.filename, outfile, item.key, item.contentType))
                    warn("    Error in Pyzotero.")
                return None

            # an odd convention: if it's HTML, it's a "snapshot", and .zip is required
            # In Pyzotero 1.2.11, with the Zotero API as of 5/18/2017,
            # text/html files are really zip files.
            # the following code attempts to unzip such files.
            # if this fails, we back off to using the file directly.

            p = os.path.join(file_outputdir, item.key)
            make_sure_path_exists(p)

            if item.contentType in ['application/zip', 'text/html']:
                outfile = os.path.join(p, "temp.zip")
                item.saved_filename = dump(item, p, "temp.zip") # good default for now
                try:
                    # let's see if we can extract it
                    with zipfile.ZipFile(outfile, 'r') as zf:
                        for zippedfile in zf.infolist():
                            # This will relativize absolute path and eliminate .. 
                            zf.extract(zippedfile, path=p)
                    item.saved_filename = item.filename # main file inside the archive
                    os.remove(outfile)
                except zipfile.BadZipfile:
                    # use default filename
                    warn("Failed to deflate ZIP archive %s (%s)"%(item.filename, item.key))
                    item.saved_filename = item.filename # rename
                    os.rename(outfile, os.path.join(p, item.saved_filename))
                    pass
            else:
                item.saved_filename = dump(item, p, item.filename)

            # prepend path for URL
            if item.saved_filename:
                item.saved_filename = os.path.join(item.key, item.saved_filename)

            # ToDo:  check if file has changed, or maybe keep contents cached in ZotItem

import pprint
def detect_and_merge_doubles(items):
    iids = {}
    titles = {}

    def merge(a, b):
        if a.section_keyword and not a.section_keyword in b.section_keyword:
            b.section_keyword.update(a.section_keyword)
        a.uniqueID = b.uniqueID

    # get last names of all creators.  exclude editors unless editors is all we have
    lastnames = lambda creators: [c['lastName'] for c in creators if not c['creatorType'] == 'editor'] or\
                                 [c['lastName'] for c in creators]

    uniqueID = 0
    for a in items:
        key = a.key
        atl = a.title.lower()

        if key in iids:
            # depending on sort criteria, even the short collection ones
            # can show up elsewhere.
            #  and not (u'collection' in iids[key] and Coll.is_short_collection(iids[key].collection))
            # print("Merging ", a.title)

            # merge "section keywords"

            merge(a, iids[key])
        elif atl in titles:
            for t in titles[atl]:
                if a.date == t.date:
                    if set(lastnames(a.creators)) == set(lastnames(t.creators)):
                        merge(a, iids[t.key])
                        break
                    # We're showing warnings for almost-equal items later
        if not a.uniqueID:  # wasn't merged
            iids[key] = a
            titles[atl] = (titles[atl] if atl in titles else []) + [a]
            uniqueID+=1
            a.uniqueID = uniqueID

    return uniqueID

def merge_doubles(items):
    # this assumes that detect_and_merge_doubles has been run.

    result = []
    ids = set()
    for i in items:
        if not i.uniqueID in ids:
            ids.add(i.uniqueID)
            result += [i]
    return result

    # Equivalend to something like the following:
    # Conceptually, not used because the lambda function relies on a state variable
    # return list(filter(lambda i: prog1(not i.uniqueID in ids, ids.add(i.uniqueID)), items))


from datetime import datetime, timedelta
import pickle


def retrieve_all_items(collections):
    global no_cache

    item_ids = {}

    # move miscellaneous collections to the end
    collections = [e for e in collections if not Coll.is_misc_collection(e.key)] + \
                  [e for e in collections if Coll.is_misc_collection(e.key)]

    all_items = []
    for e in collections: # key, depth, collection_name, collection_parents, db
        c = 0
        print(" " + " " * len(e.parents) + e.name + " (" + e.key + ") ...", end="")

        key = e.key

        i2 = list(e.db.retrieve_data(key))

        i2 = e.db.arrangeAttachments(i2)

        if Coll.is_misc_collection(key):  # Miscellaneous type collection
            # This has everything that isn't mentioned above
            # so we'll filter what's in item_ids
            # print("Miscellaneous collection: %s items initially"%len(i2))
            i2 = list(filter(lambda a: not ((a.key in item_ids) or (a.title.lower() in item_ids)), i2))

            # print("Miscellaneous collection: %s items left"%len(i2))
        elif Coll.is_regular_collection(key):
            for i in i2:
                # we store by key (ID) and also by title hash
                for k in [i.key, i.title.lower()]:
                    if k not in item_ids:
                        item_ids[k] = []
                    item_ids[k] += [(i, key)]  # tuple is item and collectionkey

        # Update file

        if 'file' in show_links or 'FILE' in show_links:
            for item in i2:
                e.db.dumpFiles(item)

        # add IDs to the list with the collection name
        #### collect_ids(i2, collection_name, item_ids)

        print("%s Items." % len(list(i2)))

        parent_path = tuple(e.parents + [key])
        for item in i2:  # for sorting by collection
            item.collection = parent_path
            item.section_keyword = set(parent_path)  # will be added HTML so the entry can be found.  Create individual set.

        if len(i2) > 0:
            all_items += i2

    return all_items, item_ids


htmlid_regex = re.compile(r"[\s,:;'\"]", re.IGNORECASE)
def htmlid(s):
    return htmlid_regex.sub("", s)

def compile_data(all_items, section_code, crits, exclude={}, shorten=False):
    global show_top_section_headings

    corehtml, count = make_html(all_items, exclude=exclude, shorten=shorten)

    # empty categories shouldn't actually be passed to compile_data

    html = ""
    if section_code:
        section_print_title = sortkeyname(crits, section_code).value
        last_section_id = last(section_code)  # if collection, get its ID
        last_crit = last(crits)
    else:
        section_print_title = "Other"
        last_section_id = last_crit = None
        section_code = ['Other']
        # print(all_items)
        # raise RuntimeError("compile_data called with empty section_code")

    if last_section_id:
        html += "<a id='%s' style='{display: block; position: relative; top: -150px; visibility: hidden;}'></a>" % htmlid(last_section_id)
        if section_code and show_top_section_headings and not Coll.hideSectionTitle(last_section_id):
            depth = 0
            if not is_string(section_code):
                depth = len(section_code) - 1  # it's a path
            # do not show headings deeper than this
            # if depth<=show_top_section_headings:
            html += "<h%s class=\"collectiontitle\">%s</h%s>\n" % (2 + depth, section_print_title, 2 + depth)
    html += corehtml
    html = u'<div class="%s-bib-section">' % (u'short' if shorten else u'full') + html + u'</div>'

    # write_some_html(html, category_outputfile_prefix+"-%s.html"%last_section_id)
    return html


def show_double_warnings(item_ids):

    def itemref(i):
        auth = (i.title and i.title[:30]) or u""
        year = i.date or u""
        ref = "%s (%s)" % (auth, year)
        return ref

    for key, itemcolls in item_ids.items():
        if len(itemcolls) > 1:
            uniqueitems = set([i.key for i, _c in itemcolls])
            if len(uniqueitems) > 1:
                # This only applies to different items with the same title
                warning("%s items sharing the same title included:" % len(itemcolls))
                for i, c in itemcolls:
                    warn(" %s [%s] (collection: %s)" % (itemref(i), i.key, Coll.findName(c)))
            else:
                # if item is the same, it may still be included in several collections:
                uniquecolls = set([c for _i, c in itemcolls])
                uniquecolls = list(filter(Coll.is_regular_collection, list(uniquecolls)))
                if len(uniquecolls) > 1:
                    # we know that every item here has the same ID (because of the previous check)
                    # itemcolls is a list
                    warning('Item "%s" included in %s collections:\n %s' % (
                    itemref(itemcolls[0][0]), len(uniquecolls), ", ".join(map(Coll.findName, uniquecolls))))





def pull_up_featured_remove_hidden_colls(all_items):
    # split up into featured and other sections
    visible = list(filter(lambda it: not Coll.is_hidden_collection(it.collection), all_items))

    # if len(visible)<len(all_items):
    #     warning("Out of %s items, only %s will be visible due to hidden collections."%(len(all_items), len(visible)))
    #     warning("The following collections are hidden: ", map(Collection.collname, filter(lambda c: Coll.is_hidden_collection(c), set(map(lambda it:it.collection, all_items)))))

    featured = filter(lambda it: Coll.is_featured_collection(it.collection), visible)
    other = filter(lambda it: not Coll.is_featured_collection(it.collection), visible)
    # if a hidden item is available elsewhere, transfer its category so that it
    # can be searched for using the category shortcuts.
    # E.g., "selected works" might not be shown at the top of the bibliography,
    # but you still might filter for it.

    hidden_categories = defaultdict(set)  # to do, use multi dict
    for it in all_items:
        if Coll.is_hidden_collection(it.collection) and not it.section_keyword in hidden_categories[it.key]:
            hidden_categories[it.key].update(it.section_keyword)
    for it in visible:
        if it.key in hidden_categories:
            it.section_keyword.update(hidden_categories[it.key])

    return list(featured), list(other)


def sort_items(all_items, sort_criteria, sort_reverse):
    # sort the items (in place)
    if sort_criteria:
        all_items = list(all_items)
        # sort is stable, so we will sort several times,
        # from the last to the first criterion
        for crit, rev in reversed(list(zip(sort_criteria, sort_reverse))):
            # print("Sorting by",crit, rev)
            # all_items contains 4-tuples, the last one is the atom representation
            all_items.sort(key=lambda x: sortkeyname(crit, x.access(crit)).sort, reverse=rev)

            # prioritize featured collections
            # all_items.sort(key=lambda x: Coll.is_featured_collection(x.collection))
    return all_items


try:
    from itertools import zip_longest
except ImportError:
    # Python 2
    from itertools import izip_longest as zip_longest


def section_generator(items, crits):
    "Iterate over all items, return them section by section"

    collect = []
    prev_section = ""
    prev_crits_sec = ""
    # crit = crits[0]  ## TO DO:  section headings for all sort criteria
    crits_sec = []
    section = []

    def changed_section_headings(prev_section, section):
        cum_new_section = []
        do_rem = False
        for p, n in zip_longest(prev_section, section, fillvalue=None):
            cum_new_section = cum_new_section + [n]  # make copy to preserve previous entries
            if n and (p != n or do_rem):  # level is different
                yield cum_new_section
                do_rem = True

    for item_tuple in items:
        item = item_tuple
        # construct section path identifier
        # also, make matching criterion identifier

        section = []
        crits_sec = []

        if Coll.is_featured_collection(item.collection):
            section = list(Coll.get_featured_collections(item.collection))
            crits_sec += ['collection'] * len(section)
        else:
            # Then, everything is organized according to the sort criteria
            for crit in crits[:show_top_section_headings]:
                val = item.access(crit)
                if not crit=='collection':  # for collections, need to preserve ID (will be converted later)
                    # for everything else we want to aggregate bib items based on the display title of the section
                    # that way, some sections can be unified via sortkeyname, or years can be used for dates
                    _sortkey, val = sortkeyname(crit,val)
                if is_string(val):  # basic fields
                    section += [val]
                    crits_sec += [crit]
                elif hasattr(val, '__iter__'):  # collection paths (val is a list)
                    section += val  # flat concat
                    crits_sec += [crit] * len(val)

        # section = item.access(crit)
        if section != prev_section:
            changed_sections = list(changed_section_headings(prev_section, section))
            if changed_sections:
                if len(collect) > 0:
                    yield prev_section, prev_crits_sec, collect
                # new section, show a section header.  add as separate item.
                # add a header for every level that has changed
                # except for the last one - that'll come with the next set of items
                for s in changed_sections:  # [:-1]:
                    if not s == section:  # because that would be the heading for the next set of items.
                        yield s, crits_sec[:len(s)], []

                collect = []
            prev_section, prev_crits_sec = section, crits_sec

        collect += [item_tuple]
    if collect:
        yield prev_section, prev_crits_sec, collect

def main(include, item_filters=[]):

    index_configuration()

    all_items = []
    section_items = []

    sortedkeys = []
    for entry in include:
        func, args = entry[0], entry[1:]
        if func == 'exclude':  # handle exclusion of items
            coll, top_level_only = args
            # if coll is the name of a collection, turn it into a key
            collobjs = Coll.findSimilar(coll)
            for collobj in collobjs:
                sortedkeys = list(filter(lambda e:  (not collobj.key in [e.key]+([] if top_level_only else e.parents)), sortedkeys))
            if not collobjs:
                warn("Exclude: Collection %s not found."%coll)
        elif func == 'rename':
            coll, name = args
            collobjs = Coll.findSimilar(coll)
            for collobj in collobjs:
                collobj.name = name # newName
        elif func == 'load': # DB Object
            db, coll, toplevel = args
            sortedkeys += db.get_collections(coll, toplevel)

    all_items, item_ids = retrieve_all_items(sortedkeys)

    def apply_exclusion_filter(filter, item):
        try:
            r = filter(item)
            return not r
        except Exception as e:
            warn("Error while applying exclude_items filter: ", e)
        return False

    for f in item_filters:
        all_items = filter(lambda i: apply_exclusion_filter(f, i), all_items)
    all_items = list(all_items)

    # merge collections with the same name
    for c in sortedkeys:
        collobjs = Coll.findSimilar(c.name)
        if len(collobjs)>1:
            print("Merging %s collections into section %s."%(len(collobjs),c.name))
            for collobj in collobjs:
                for i in all_items:
                    if last(i.collection) == collobj.key:
                        i.collection = tuple(c.parents + [c.key])
                        i.section_keyword.update(set(i.collection))

    detect_and_merge_doubles(all_items)

    if 'collection' in sort_criteria:
        show_double_warnings(item_ids)
        # If collection doesn't feature in sort criteria,
        # double entries are likely to get filtered out anyway,
        # or they are desired (e.g., Selected Works)

    featured_items, regular_items = pull_up_featured_remove_hidden_colls(all_items)
    featured_items = sort_items(featured_items, ['collection'] + sort_criteria, [False] + sort_reverse)
    regular_items = sort_items(regular_items, sort_criteria, sort_reverse)
    # don't use chain - we will iterate over all_items several times, so
    # we need a list
    all_items = list(featured_items) + list(regular_items)

    headerhtmls = make_header_htmls(all_items)

    itemids = set()  # For statistics

    fullhtml = u""
    for section_code, crits, items in list(section_generator(all_items, sort_criteria)):
        # remove double entries within one section
        items = list(merge_doubles(items))
        fullhtml += compile_data(items, section_code, crits, shorten=Coll.is_short_collection(section_code))

        # Keep track of IDs so we can show statistics
        itemids.update(map(lambda i: i.key, items))

    print("The bibliography contains %s entries (%s unique keys)." % (len(all_items), len(itemids)))

    headerhtml = '<div id="bib-preamble" style="visibility:hidden;">'
    for crit, h in zip(show_shortcuts, headerhtmls):
        if isinstance(crit, tuple):
            crit = crit[0]
        if isinstance(crit, Shortcut):
            crit = crit.crit
        headerhtml += '<ul id="bib-cat-%s" class="bib-cat">' % crit + h + "</ul>"
    headerhtml += search_box + "</div>"  # preamble

    write_some_html(headerhtml + fullhtml, outputfile)


if __name__ == '__main__':
    read_args_and_init()
    html_header, search_box, html_footer = generate_base_html()

    if interactive_debugging:
        import code

        code.interact(local=locals())
    else:
        main(include_collections, item_filters)
