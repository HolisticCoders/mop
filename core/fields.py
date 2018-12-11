import maya.cmds as cmds


class Attribute(object):
    def __init__(self, instance, field):
        self.field = field
        self.is_multi = field.create_attr_args.get('multi', False)
        self.attr_name = '.'.join([instance.name, field.name])
        if not cmds.attributeQuery(field.name, node=instance.name, exists=True):
            cmds.addAttr(
                instance.name,
                longName=field.name,
                **field.create_attr_args
            )

    def set(self, value):
        if self.is_multi:
            self._set_multi_attribute(value)
        else:
            self._set_single_attribute(value)

    def get(self):
        if self.is_multi:
            return self._get_multi_attribute()
        else:
            return cmds.getAttr(self.attr_name)

    def _get_multi_attribute(self):
        indices = self._get_multi_indices()
        if indices:
            return [cmds.getAttr('{}[{}]'.format(self.attr_name, i)) for i in indices]
        else:
            return []

    def _set_single_attribute(self, value):
        casted_value = self.field.cast(value)
        cmds.setAttr(self.attr_name, casted_value, **self.field.set_attr_args)

    def _set_multi_attribute(self, value):
        self._clear_multi_attribute()
        if not isinstance(value, list):
            value = [value]
        for index, item in enumerate(value):
            casted_item = self.field.cast(item)
            attrName = '{}[{}]'.format(self.attr_name, index)
            cmds.setAttr(attrName, casted_item)

    def _clear_multi_attribute(self):
        indices = self._get_multi_indices()
        for index in indices:
            cmds.removeMultiInstance('{}[{}]'.format(self.attr_name, index))

    def _get_multi_indices(self):
        indices = cmds.getAttr(self.attr_name, multiIndices=True)
        if not indices:
            indices = []
        return indices


class Field(object):
    create_attr_args = {}
    set_attr_args = {}

    def __init__(
        self,
        name=None,
        as_list=False,
    ):
        self.name = name
        if as_list:
            self.create_attr_args['multi'] = True
        self._attrs = {}

    def __get__(self, instance, instancetype=None):
        self._ensure_maya_attr(instance)
        return self._attrs[instance]

    def _ensure_maya_attr(self, instance):
        if instance not in self._attrs:
            self._attrs[instance] = self.create_attr(instance)

    def create_attr(self, instance):
        return Attribute(instance, self)

class IntField(Field):
    create_attr_args = {
        'attributeType': 'long'
    }

    def cast(self, value):
        return int(value)

class FloatField(Field):
    create_attr_args = {
        'attributeType': 'double'
    }

    def cast(self, value):
        return float(value)

class BoolField(Field):
    create_attr_args = {
        'attributeType': 'bool'
    }

    def cast(self, value):
        return bool(value)

class StringField(Field):
    create_attr_args = {
        'dataType': 'string'
    }
    set_attr_args = {
        'type': 'string'
    }

    def cast(self, value):
        return str(value)

class ObjectField(StringField):
    def cast(self, value):
        value = super(ObjectField, self).cast(value)
        if cmds.objExists(value):
            return value
        else:
            raise ValueError('node `{}` does not exist'.format(value))
