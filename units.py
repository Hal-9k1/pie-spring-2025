import math

_units_per_standard = {
    'mm': 1000,
    'cm': 100,
    'in': 100 / 2.54,
    'ft': 100 / 2.54 / 12,
    'm': 1,

    'deg': 180 / math.pi,
    'rev': 1 / (2 * math.pi),
    'rad': 1,

    'sec': 1,
    'nano': 10**9,
    'msec': 1000,
}

_unit_types = {
    'mm': 'distance',
    'cm': 'distance',
    'in': 'distance',
    'ft': 'distance',
    'm': 'distance',

    'deg': 'angle',
    'rev': 'angle',
    'rad': 'angle',

    'sec': 'time',
    'nano': 'time',
    'msec': 'time',
}

def convert(value, from_unit, to_unit):
    if from_unit not in _units_per_standard:
        raise ValueError(f'Unknown unit {from_unit})')
    if to_unit not in _units_per_standard:
        raise ValueError(f'Unknown unit {to_unit}')
    if _unit_types[from_unit] != _unit_types[to_unit]:
        raise ValueError(f'Cannot convert from {_unit_types[from_unit]} unit to { _unit_types[to_unit]} unit')
    return value * _units_per_standard[to_unit] / _units_per_standard[from_unit]
