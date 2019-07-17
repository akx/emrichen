from .json import load_json
from .yaml import load_yaml, load_tyaml

PARSERS = {
    'yaml': load_yaml,
    'tyaml': load_tyaml,
    'json': load_json,
}


def parse(data, format):
    if format in PARSERS:
        return PARSERS[format](data)
    else:
        raise ValueError('No parser for format {format}'.format(format=format))
