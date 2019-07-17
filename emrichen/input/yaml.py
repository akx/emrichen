import re
from collections import OrderedDict

import yaml
from yaml.constructor import ConstructorError

from ..exceptions import NoSuchTag
from .utils import make_compose
from ..tags.base import tag_registry


def construct_tagless_yaml(loader, node):
    # From yaml.constructor.BaseConstructor#construct_object
    if isinstance(node, yaml.ScalarNode):
        constructor = loader.construct_scalar
    elif isinstance(node, yaml.SequenceNode):
        constructor = loader.construct_sequence
    elif isinstance(node, yaml.MappingNode):
        constructor = loader.construct_mapping
    return constructor(node)


def construct_tagged_object(loader, node):
    name = node.tag.lstrip('!')
    if name in tag_registry:
        tag = tag_registry[name]
        data = construct_tagless_yaml(loader, node)
        return tag(data)
    if ',' in name:  # Compose
        try:
            return make_compose(names=name, value=construct_tagless_yaml(loader, node))
        except NoSuchTag as nst:
            name = nst.args[0]
            raise ConstructorError(
                None, None,
                "in compose tag %s: can't find tag %s" % (node.tag, name),
                node.start_mark,
            ) from nst
    raise ConstructorError(
        None, None,
        "can't find tag %s" % node.tag,
        node.start_mark,
    )


class RichLoader(yaml.SafeLoader):
    def __init__(self, stream):
        super(RichLoader, self).__init__(stream)
        self.add_tag_constructors()

    def add_tag_constructors(self):
        self.yaml_constructors = self.yaml_constructors.copy()  # Grab an instance copy from the class
        self.yaml_constructors[self.DEFAULT_MAPPING_TAG] = self._make_ordered_dict
        self.yaml_constructors[None] = construct_tagged_object

    @staticmethod
    def _make_ordered_dict(loader, node):
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))


class InlineTemplateLoader(RichLoader):
    def construct_scalar(self, node):
        if node.tag == 'tag:yaml.org,2002:str' and '$' in node.value:
            new_value = re.sub('\$(.+?)\$', lambda m: '{' + m.group(1) + '}', node.value)
            if new_value != node.value:
                from emrichen.tags import Format
                return Format(data=new_value)
        return super().construct_scalar(node)


def load_yaml(data):
    return list(yaml.load_all(data, Loader=RichLoader))


def load_tyaml(data):
    return list(yaml.load_all(data, Loader=InlineTemplateLoader))
