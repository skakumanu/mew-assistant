"""
Calendar adapters.

The design's promise is that nobody installs anything they do not already
have: a provider keeps working in the calendar they already use, and Mew
reads from it and writes back to it.

  google  full read and write, through the person's own OAuth token
  ics     read-only feed - which is how Apple, Calendly and most clinic and
          school booking tools publish, so one adapter covers all of them

An unwritable calendar is not a broken one: the schedule in Mew stays
authoritative and the log records that the calendar could not be updated.
"""

from .base import CalendarAdapter, CalendarEvent, CalendarSyncError
from .google import GoogleCalendarAdapter
from .ics import IcsFeedAdapter, parse_ics

__all__ = [
    "CalendarAdapter",
    "CalendarEvent",
    "CalendarSyncError",
    "GoogleCalendarAdapter",
    "IcsFeedAdapter",
    "parse_ics",
]
