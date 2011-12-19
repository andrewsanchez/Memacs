#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2011-12-18 15:13:31 aw>

import sys,os
# needed to import common.*
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging 
from common.loggingsettings import *  
from common.orgwriter import OrgOutputWriter
from common.orgformat import OrgFormat
from common.argparser import MemacsArgumentParser
from common import orgwriter
import re
import codecs
from urllib2 import HTTPError, URLError, urlopen
import time
import calendar
import traceback

try:
    from icalendar import Calendar
except ImportError:
    print "please install python package \"icalendar\""
    sys.exit(3)


PROG_VERSION_NUMBER = u"0.1"
PROG_VERSION_DATE = u"2011-12-18"
# TODO set real description and so on
SHORT_DESCRIPTION = u"Memacs for ical Calendars"
TAG = u"calendar"
DESCRIPTION = u"""This script parses a *.ics file and generates 
Entries for VEVENTS

Emacs tmp-files like file~ are automatically ignored
"""

REGEX_VEVENT               = re.compile("BEGIN:VEVENT(.*?)END:VEVENT", re.DOTALL)
REGEX_VEVENT_DTSTART       = re.compile("DTSTART:(.*)")
REGEX_VEVENT_DTSTARTALLDAY = re.compile("DTSTART;VALUE=DATE(.*)")
REGEX_VEVENT_DTEND         = re.compile("DTEND:(.*)")
REGEX_VEVENT_SUMMARY       = re.compile("SUMMARY:(.*)")
REGEX_VEVENT_DESCRIPTION   = re.compile("DESCRIPTION:(.*)")
REGEX_VEVENT_LOCATION      = re.compile("LOCATION:(.*)")

def main():
    ###########################################################################
    parser = MemacsArgumentParser(prog_version=PROG_VERSION_NUMBER,
                                  prog_version_date=PROG_VERSION_DATE,
                                  description=DESCRIPTION,
                                  )
    # adding additional arguments
    parser.add_argument("-c", "--calendar-url", dest="calendar_url",
                        help="url to calendar")
    
    parser.add_argument("-cf", "--calendar-file", dest="calendar_file",
                        help="path to calendar")
    
    parser.add_argument("-x", "--exclude", dest="excludelist",
                        help="path to one or more folders seperated with \"|\"," + \
                        "i.e.:\"/path/to/folder1|/path/to/folder2|..\"")
    
    # do parsing  
    args = parser.parse_args()
    
    handle_logging(args.verbose,args.suppressmessages,args.outputfile) 
    logging.debug("args specified:") 
    logging.debug(args)
    
    if not args.calendar_url and not args.calendar_file:
        parser.error("specify a calendar url or calendar file")
            
    if args.calendar_url and args.calendar_file:
        parser.error("only set a url or path to a calendar not both.")
    
    if args.calendar_file and not os.path.exists(args.calendar_file):
        parser.error("calendar path not exists")
    
    writer = OrgOutputWriter(file_name=args.outputfile, short_description=SHORT_DESCRIPTION, tag=TAG);
    # do stuff
    if args.calendar_file:
        try:
            file = codecs.open(args.calendar_file, 'rb')
            data = file.read()
            file.close()
        except IOError:
            logging.error("Error at opening file: %s" % args.calendar_file)
            sys.exit(1)
            
    elif args.calendar_url:
        try:
            req = urlopen(args.calendar_url, None, 10)
            data = req.read()
        except HTTPError:
            logging.error("Error at opening url: %s" % args.calendar_url)
            sys.exit(1)
        except URLError:
            logging.error("Error at opening url: %s" % args.calendar_url)
            sys.exit(1)
        except ValueError:
            logging.error("Error - no valid url: %s" % args.calendar_url)
            sys.exit(1)
    
    cal = Calendar.from_string(data);
    
    for component in cal.walk():
        if component.name == "VCALENDAR":
            # Set timezone
            timezone = component.get('x-wr-timezone')
            logging.debug("Setting timezone to: " + timezone)
            os.environ['TZ'] = timezone;
            time.tzset()
        elif component.name == "VEVENT":
            summary  = unicode(component.get('summary'))
            location = unicode(component.get('location'))
            description = unicode(component.get('description'))
            dtstart  = unicode(component.get('dtstart')) # format: 20091207T180000Z or 20100122
            dtend    = unicode(component.get('dtend'))   # format: 20091207T180000Z or 20100122
            dtstamp  = unicode(component.get('dtstamp')) # format: 20091207T180000Z
            orgdatecreated = OrgFormat.date(OrgFormat.datetupelutctimestamp(dtstamp))
            orgdate = OrgFormat.utcrange(dtstart, dtend)
            logging.debug(orgdate + " " + summary)
            writer.write_org_subitem(summary)
            writer.writeln("   " +orgdate)
            writer.writeln("   :PROPERTIES:")
            if location:
                writer.writeln("   :LOCATION:" +location)
            if description:
                writer.writeln("   :DESCRIPTION:" +description)
            writer.writeln("   :END:")
        else:
            logging.info("Not handling component: "+component.name)
            

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt")
    except SystemExit:
        # if we get an sys.exit() do exit!
        pass
    except:
        error_lines = traceback.format_exc().splitlines()
        logging.error("\n   ".join(map(str,error_lines)))
        raise # re raise exception    