import logging
try:
    import pint
except ImportError:
    pint = None
from .interface import QueryHandler
from .lang import Language
from ..utils import is_types, Singleton
from ..constants import UNIT_QUERY_REGEX, EMPTY_AMOUNT, UNIT_QUERY_REGEX_DEFAULT, UNIT_REGEX_SPLIT

class UnitsQueryHandler(QueryHandler):
    def __init__(self):
        self._ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
        self._logger = logging.getLogger(__name__)

    @staticmethod
    def _extract_query(query):
        matches = UNIT_QUERY_REGEX.findall(query)
        matches_default = UNIT_QUERY_REGEX_DEFAULT.findall(query)
        if not matches and not matches_default:
            return None
        translator = Language.get_instance().get_translator('units')

        if matches:
            unit_from, _, units_to = matches[0]
            units_to = units_to.split(',')
        else:
            unit_from = matches_default[0]
            units_to = []
        # amount = 1.0 if EMPTY_AMOUNT.match(amount) else float(amount)
        unit_from = unit_from.strip().lower()
        unit_from = translator(UNIT_REGEX_SPLIT.sub(lambda m: translator(m.group(0)), unit_from))
        units_to = map(str.strip, units_to)
        units_to = map(str.lower, units_to)
        units_to = map(lambda u: UNIT_REGEX_SPLIT.sub(lambda m: translator(m.group(0)), u), units_to)
        units_to = list(dict.fromkeys(units_to))

        return unit_from, units_to

    def handle(self, query):
        if pint is None:
            return [{
                'icon': 'images/icon.svg',
                'value': '',
                'name': 'Looks like pint is not installed.',
                'description': 'Install it with "pip install pint" and restart launcher.',
                'is_error': True,
                'order': -1
            }]

        query = UnitsQueryHandler._extract_query(query)
        if not query:
            return None
        unit_from, units_to = query

        try:
            unit_from_ureg = self._ureg.parse_expression(unit_from)
            if is_types(unit_from_ureg, int, float, complex):
                return
            if unit_from_ureg.units == self._ureg('dimensionless'):
                return
        except Exception as e:
            self._logger.error('Could not convert parse from unit: {}'.format(unit_from))
            return None
        
        if not units_to:
            units_to = [str(unit_from_ureg.units)]

        translator = Language.get_instance().get_translator('units')
        unit_from_name = translator(str(unit_from_ureg.units)).replace('**', '^').replace('_', ' ')

        results = []
        i = 0
        for unit_to in units_to:
            try:
                unit_to_ureg = self._ureg.parse_expression(unit_to)
                rate = unit_from_ureg.to(unit_to_ureg).magnitude / unit_from_ureg.magnitude
                amount_converted = unit_from_ureg.to(unit_to_ureg)
            except Exception as e:
                self._logger.error('Could not convert to unit: {}'.format(unit_to))
                continue

            unit_to_name = str(unit_to_ureg.units)
            has_temperature = 'degree_' in unit_to_name
            unit_to_name = translator(unit_to_name).replace('**', '^').replace('_', ' ')
            if has_temperature or unit_from_name == unit_to_name:
                description = ''
            else:
                description = '1 {} = {:g} {}'.format(unit_from_name, rate, unit_to_name)

            results.append({
                'value': amount_converted.magnitude,
                'name': '{:g} {}'.format(amount_converted.magnitude, unit_to_name),
                'description': description,
                'is_error': False,
                'order': i,
            })
            i += 1
        return results

    @classmethod
    @Singleton
    def get_instance(cls):
        return cls()