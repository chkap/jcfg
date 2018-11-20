import re


from .error import JCfgInvalidKeyError, JCfgInvalidValueError


class JsonCfg(object):
    __valid_key_pattern = r'[A-Za-z_][A-Za-z0-9_]*'
    __reo = re.compile(__valid_key_pattern)

    def __init__(self, config_meta):
        assert isinstance(config_meta, dict)
        self.__config_desc = self.__load_from(config_meta)

    @classmethod
    def __load_from(cls, config_meta):
        config_desc = {}
        for key in config_meta:
            cls.assert_valid_key(key)
            value_type = cls.__check_value_type(config_meta[key])
            if value_type == 'pure_value' or value_type == 'custom_value':
                config_desc[key] = cls.__parse_value(config_meta[key])
            else:
                config_desc[key] = cls.__load_from(config_meta[key])
        return config_desc

    @classmethod
    def __parse_value(cls, value):
        value_type = cls.__check_value_type(value)
        if value_type == 'pure_value':
            value_desc = cls.__create_value_desc_from_default_value(value)
        elif value_type == 'custom_value':
            assert 'value' in value
            value_desc = cls.__create_value_desc_from_default_value(value['default'])
            for attr in value:
                if attr in value_desc:
                    continue
                else:
                    value_desc[attr] = value[attr]
        else:
            assert False, 'This should never happen!'
        
        return value_desc

    @classmethod
    def __create_value_desc_from_default_value(cls, value):
        value_desc = {}
        assert cls.__check_value_type(value) == 'pure_value'
        if isinstance(value, int):
            value_desc['type'] = int
            value_desc['value'] = value
            value_desc['default'] = value
        elif isinstance(value, float):
            value_desc['type'] = float
            value_desc['value'] = value
            value_desc['default'] = value
        elif isinstance(value, list):
            value_desc['type'] = list
            value_desc['value'] = value
            value_desc['default'] = value
        else:
            assert False, 'This should never happen!'
        
        return value_desc


    @classmethod
    def assert_valid_key(cls, key):
        if cls.__reo.fullmatch(key) is None:
            raise JCfgInvalidKeyError(
                'Invalid config key: {}, only A-Za-z0-9_ is allowed.'.format(key))
        else:
            return

    @classmethod
    def __check_value_type(cls, value):
        if isinstance(value, dict):
            if 'default' in value and cls.__check_value_type(value['default']) == 'pure_value':
                return 'custom_value'  # is a subconfig
            else:
                return 'subconfig'
        elif isinstance(value, int) or isinstance(value, float) or isinstance(value, list):
            return 'pure_value'
        else:
            raise JCfgInvalidValueError('Invalid value error: {}'.format(str(value)))



