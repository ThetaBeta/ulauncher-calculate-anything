# -*- coding: utf-8 -*-
'''Converter for currency, units and calculator.

Current backends: fixer.io.

Synopsis: "10 dollars to eur, cad" "10 meters to inches" "10 + sqrt(2)" "cos(pi + 3i)"'''

################################### SETTINGS #######################################
# Below are the settings for this extension
# API Key is your fixer.io API key
API_KEY = ''
# Cache update interval in seconds (defaults to 1 day = 86400 seconds)
CACHE = 86400
# Default currencies to show when no target currency is provided
DEFAULT_CURRENCIES = 'USD,EUR,GBP,CAD'
# Default cities to show when converting timezones
DEFAULT_CITIES = 'New York City US, London GB, Madrid ES, Vancouver CA, Athens GR'
# Set the following to True if you want to enable placeholder for empty results
SHOW_EMPTY_PLACEHOLDER = False
# Below line is the trigger keywords to your choice (put a space after your keyword)
# First element is the calculator trigger, second element is the time conversion trigger
__triggers__ = ['=', 'time']
####################################################################################

__title__ = 'Calculate Anything'
__version__ = '0.0.1'
__authors__ = 'Tilemachos Charalampous'
__py_deps__ = ['requests', 'requests', 'pint' ,'simpleeval', 'parsedatetime']

class AlbertLogger:
    def __init__(self, name):
        self._name = name

    @staticmethod
    def _escape(message):
        return message.replace('%', '\\%')

    def _log(self, func, message, *args):
        message = str(message)
        message = AlbertLogger._escape(message)
        if args:
            message = message % args
        message = '{}: {}'.format(self._name, message)
        func(message)

    def debug(self, message, *args):
        self._log(debug, message, *args)

    def info(self, message, *args):
        self._log(info, message, *args)

    def warning(self, message, *args):
        self._log(warning, message, *args)

    def error(self, message, *args):
        self._log(critical, message, *args)
    
class AlbertLogging:
    def getLogger(name=''):
        return AlbertLogger(name)

import locale
locale.setlocale(locale.LC_ALL, '')
import os
import sys
try:
    from calculate_anything.constants import MAIN_DIR
except ImportError as e:
    MAIN_DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(MAIN_DIR)

from calculate_anything.logging_wrapper import LoggingWrapper as logging
logging.set_logging(AlbertLogging)
from calculate_anything.currency.service import CurrencyService
from calculate_anything.time.service import TimezoneService
from calculate_anything.query.handlers import (
    UnitsQueryHandler, CalculatorQueryHandler, CurrencyQueryHandler,
    PercentagesQueryHandler, TimeQueryHandler
)
from calculate_anything.query import QueryHandler
from calculate_anything.lang import Language
from albert import ClipAction, Item, critical, debug, info, warning, critical

try:
    API_KEY = API_KEY or ''
    CACHE = int(CACHE)
except (ValueError, TypeError):
    CACHE = 86400

TRIGGERS = globals().get('__triggers__') or []
if isinstance(TRIGGERS, str):
    TRIGGERS = [TRIGGERS]

def initialize():
    service = CurrencyService()
    service.set_api_key(API_KEY)
    if CACHE > 0:
        service.enable_cache(CACHE)
    else:
        service.disable_cache()
    default_currencies = DEFAULT_CURRENCIES.split(',')
    default_currencies = map(str.strip, default_currencies)
    default_currencies = map(str.upper, default_currencies)
    default_currencies = list(default_currencies)
    service.set_default_currencies(default_currencies)
    service.run()

    default_cities = TimezoneService.parse_default_cities(DEFAULT_CITIES)
    TimezoneService().set_default_cities(default_cities)

def finalize():
    CurrencyService().disable_cache()

def is_time_trigger(trigger):
    try:
        return TRIGGERS[1] == trigger
    except IndexError:
        return False

def handleQuery(query):
    if TRIGGERS and not query.isTriggered:
        return
    query_str = query.string.strip()
    query.disableSort()
    items = []
    errors_num = 0

    if not TRIGGERS:
        handlers = []
    elif is_time_trigger(query.trigger):
        query_str = 'time ' + query_str
        handlers = [TimeQueryHandler]
    else:
        handlers = [
            UnitsQueryHandler,
            CalculatorQueryHandler,
            CurrencyQueryHandler,
            PercentagesQueryHandler
        ]
    results = QueryHandler().handle(query_str, *handlers)
    for result in results:
        errors_num += result.error is not None
        icon = result.icon or 'images/icon.svg'
        icon = os.path.join(MAIN_DIR, icon)

        if result.clipboard is not None:
            actions = [ClipAction(text=result.clipboard, clipboardText=result.clipboard)]
        items.append(Item(
            id=__title__,
            icon=icon,
            text=result.name,
            subtext=result.description,
            actions=actions
        ))
    
    should_show_placeholder = (
        query_str == '' or (
            SHOW_EMPTY_PLACEHOLDER and (
                TRIGGERS or query_str
            ) and len(items) == errors_num
        )
    )
    if should_show_placeholder:
        items.append(
            Item(
                id=__title__,
                icon=os.path.join(MAIN_DIR, 'images/icon.svg'),
                text=Language().translate('no-result', 'misc'),
                subtext=Language().translate('no-result-description', 'misc'),
            )
        )
    if not items:
        return None
    return items
