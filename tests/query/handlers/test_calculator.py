from calculate_anything.utils.singleton import Singleton
import pytest
import calculate_anything.query.handlers.calculator as calculator
from calculate_anything.lang import LanguageService
from calculate_anything.query.handlers import CalculatorQueryHandler
from calculate_anything.utils.misc import StupidEval
from calculate_anything.exceptions import BooleanComparisonException, MissingSimpleevalException, ZeroDivisionException

LanguageService().set('en_US')
tr_calc = LanguageService().get_translator('calculator')
tr_err = LanguageService().get_translator('errors')

test_spec = [{
    # Normal test
    'query': '= 1 + 1 + 1',
    'results': [{
        'result': {
            'value': 3,
            'query': '1 + 1 + 1',
            'error': None,
            'order': 0
        },
        'query_result': {
            'icon': 'images/icon.svg',
            'name': '3',
            'description': '1 + 1 + 1',
            'clipboard': '3',
            'error': None,
            'order': 0,
            'value': 3,
            'value_type': int
        }
    }],
}, {
    # Division by zero
    'query': '= (1 + 2) / (1 - 1)',
    'results': [{
        'result': {
            'query': '(1 + 2) / (1 - 1)',
            'value': None,
            'error': ZeroDivisionException,
            'order': 0
        },
        'query_result': {
            'icon': 'images/icon.svg',
            'name': tr_err('infinite-result-error'),
            'description': tr_err('infinite-result-error-description'),
            'clipboard': None,
            'error': ZeroDivisionException,
            'order': 0,
            'value': None,
            'value_type': type(None)
        }
    }],
}, {
    # Complex number
    'query': '= (1 + 7 + 5i + 4i - 7i) / 2',
    'results': [{
        'result': {
            'value': 4 + 1j,
            'query': '(1 + 7 + 5j + 4j - 7j) / 2',
            'error': None,
            'order': 0
        },
        'query_result': {
            'icon': 'images/icon.svg',
            'name': '4 + i',
            'description': '(1 + 7 + 5i + 4i - 7i) / 2 ({})'.format(tr_calc('result-complex').capitalize()),
            'clipboard': '4 + i',
            'error': None,
            'order': 0,
            'value': 4 + 1j,
            'value_type': complex
        }
    }],
}, {
    # Complex number with reversed i
    'query': '= (1 + 7 + i2 + i5 - i11) / 2',
    'results': [{
        'result': {
            'value': 4 - 2j,
            'query': '(1 + 7 + 2j + 5j - 11j) / 2',
            'error': None,
            'order': 0
        },
        'query_result': {
            'icon': 'images/icon.svg',
            'name': '4 - 2i',
            'description': '(1 + 7 + 2i + 5i - 11i) / 2 ({})'.format(tr_calc('result-complex').capitalize()),
            'clipboard': '4 - 2i',
            'error': None,
            'order': 0,
            'value': 4 - 2j,
            'value_type': complex
        }
    }],
}, {
    # Test result with complex numbers that is real and not of type complex
    'query': '= e ^ (pi * i)',
    'results': [{
        'result': {
            'value': -1 + 0j,
            'query': 'e ** (pi * 1j)',
            'error': None,
            'order': 0
        },
        'query_result': {
            'icon': 'images/icon.svg',
            'name': '-1',
            'description': 'e ^ (π × i)',
            'clipboard': '-1',
            'error': None,
            'order': 0,
            'value': -1,
            'value_type': int
        }
    }],
}, {
    # Test inequality with comples number producing error
    'query': '= 1 + i > 0.5 + 2i',
    'results': [{
        'result': {
            'value': None,
            'query': '1 + 1j > 0.5 + 2j',
            'error': BooleanComparisonException,
            'order': 0
        },
        'query_result': {
            'icon': 'images/icon.svg',
            'name': tr_err('boolean-comparison-error'),
            'description': tr_err('boolean-comparison-error-description'),
            'clipboard': None,
            'error': BooleanComparisonException,
            'order': 0,
            'value': None,
            'value_type': type(None)
        }
    }],
}, {
    # Test boolean result
    'query': '= e ^ (pi * i) + 1 = 0',
    'results': [{
        'result': {
            'value': True,
            'query': 'e ** (pi * 1j) + 1 == 0',
            'error': None,
            'order': 0
        },
        'query_result': {
            'icon': 'images/icon.svg',
            'name': 'true',
            'description': 'e ^ (π × i) + 1 = 0 ({})'.format(tr_calc('result-boolean').capitalize()),
            'clipboard': 'true',
            'error': None,
            'order': 0,
            'value': True,
            'value_type': bool
        }
    }],
}, {
    # Test rejects 1
    'query': '= 1 % of 2',
    'results': [],
}, {
    # Test rejects 2
    'query': '= 1 == 2',
    'results': [],
}, {
    # Test rejects 3
    'query': '= 2.5 is 2.5',
    'results': [],
}, {
    # Test rejects 4
    'query': '= 5 // 2',
    'results': [],
}, {
    # Test wrong query
    'query': '= Some irrelevant query',
    'results': [],
}, {
    # Test missing value between equalities 1
    'query': '= 1 =  < 2',
    'results': [],
}, {
    # Test missing value between equalities 2
    'query': '= 5.4 >  = 4',
    'results': [],
}, {
    # Test missing value between equalities 3
    'query': '= 1 >=  = 5.67',
    'results': [],
}, {
    # Test missing value between equalities 4
    'query': '= pi <=  <= 8',
    'results': [],
}, {
    # Test other cases
    'query': '= 1 2 7.57',
    'results': [],
}, {
    # Test j not as imaginary
    'query': '= 8 + j + 4.5 - sqrt(5j)',
    'results': [],
}, {
    # Test i alone after number with spaces
    'query': '= 5 i',
    'results': [],
}]


@pytest.mark.parametrize('test_spec', test_spec)
def test_calculator(test_spec):
    results = CalculatorQueryHandler().handle(test_spec['query'])

    if results is None:
        assert len(test_spec['results']) == 0
        return

    assert len(results) == len(test_spec['results'])

    for result, item in zip(results, test_spec['results']):
        assert result.value == item['result']['value']
        assert result.query == item['result']['query']
        assert result.error == item['result']['error']
        assert result.order == item['result']['order']

        query_result = result.to_query_result()
        assert query_result.icon == item['query_result']['icon']
        assert query_result.name == item['query_result']['name']
        assert query_result.description == item['query_result']['description']
        assert query_result.clipboard == item['query_result']['clipboard']
        assert query_result.error == item['query_result']['error']
        assert query_result.order == item['query_result']['order']
        assert query_result.value == item['query_result']['value']
        # Although seems stupid we use this to distinguish between equalities in floats and ints
        # For example 3.0 is not equal to 3 we want the type to be correct
        assert isinstance(query_result.value,
                          item['query_result']['value_type'])


def test_simpleeval_missing():
    # Allow CalculatorQueryHandler to be reinstantiated 
    if CalculatorQueryHandler in Singleton._instances:
        del Singleton._instances[CalculatorQueryHandler]
    # Set stupid StupidEval as SimpleEval
    SimpleEval = calculator.SimpleEval
    calculator.SimpleEval = StupidEval
    
    assert isinstance(CalculatorQueryHandler()._simple_eval, StupidEval)
    
    # Test simple calculation that can be handled with StupidEval
    results = CalculatorQueryHandler().handle_raw('1245')
    assert len(results) == 1
    query_result = results[0].to_query_result()
    assert query_result.icon == 'images/icon.svg'
    assert query_result.name == '1245'
    assert query_result.description == '1245'
    assert query_result.error == None
    assert query_result.clipboard == '1245'
    assert query_result.order == 0
    assert query_result.value == 1245
    assert isinstance(query_result.value, int)


    # Test simple calculation that cannot be handled with StupidEval
    results = CalculatorQueryHandler().handle_raw('1 + 1 + 2')
    assert len(results) == 1
    query_result = results[0].to_query_result()
    assert query_result.icon == 'images/icon.svg'
    assert query_result.name == tr_err('install-simpleeval')
    assert query_result.description == tr_err('install-simpleeval-description')
    assert query_result.error == MissingSimpleevalException
    assert query_result.clipboard == 'pip install simpleeval'
    assert query_result.order == -1
    assert query_result.value == None

    # Set back SimpleEval
    calculator.SimpleEval = SimpleEval

def test_misc_cov():
    pass