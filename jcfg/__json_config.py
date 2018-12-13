import re
import argparse

from .error import JCfgInvalidKeyError, JCfgInvalidValueError, JCfgKeyNotFoundError, JCfgValueTypeMismatchError, \
    JCfgInvalidSetValueError


class JsonCfg(object):
    __valid_key_pattern = r'[A-Za-z_][A-Za-z0-9_]*'
    __reo = re.compile(__valid_key_pattern)

    def __init__(self, config_meta):
        if not isinstance(config_meta, dict):
            raise ValueError(
                'Cannot init from {}, a dict is needed'.format(type(dict)))
        self.__config_desc = self.__load_from(config_meta)

    @classmethod
    def __load_from(cls, config_meta):
        config_desc = {}
        for key in config_meta:
            cls.__assert_valid_key(key)
            value = config_meta[key]
            if isinstance(value, dict) and 'default' not in value:
                config_desc[key] = JsonCfg(config_meta[key])
            else:
                config_desc[key] = JsonCfgValue.create_from_value(value)
        return config_desc

    @classmethod
    def __assert_valid_key(cls, key):
        if cls.__reo.fullmatch(key) is None:
            raise JCfgInvalidKeyError(
                'Invalid config key: {}, only [A-Za-z0-9_] is allowed.'.format(key))
        else:
            return

    def __getitem__(self, key):
        key_list = key.split('.')
        return self.__get_value_by_key_list(key_list).get()

    def __getattr__(self, name):
        if name == '_JsonCfg__config_desc':
            return object.__getattr__(self, name)

        self.__assert_valid_key(name)
        if name not in self.__config_desc:
            return AttributeError('Config key {} not found'.format(name))
        else:
            _value = self.__config_desc[name]
            if isinstance(_value, JsonCfg):
                return _value
            else:
                assert isinstance(_value, JsonCfgValue), type(_value)
                return _value.get()

    def __get_value_by_key_list(self, key_list):
        assert len(key_list) >= 1
        if len(key_list) == 1:
            return self.__get_value(key_list[0])
        else:
            return self.__get_value_by_key_list(key_list[:-1])[key_list[-1]]

    def __get_value(self, key):
        self.__assert_valid_key(key)
        if key not in self.__config_desc:
            raise JCfgKeyNotFoundError(
                'Config key: {} is not found'.format(key))
        else:
            _value = self.__config_desc[key]
            if isinstance(_value, JsonCfg):
                return _value
            else:
                assert isinstance(_value, JsonCfgValue), _value.type
                return _value

    def __setitem__(self, key, value):
        key_list = key.split('.')
        self.__set_value_by_key_list(key_list, value)

    def __setattr__(self, key, value):
        if key == '_JsonCfg__config_desc':
            if key not in self.__dict__:
                return object.__setattr__(self, key, value)
            else:
                return

        if key not in self.__config_desc:
            return object.__setattr__(self, key, value)
        else:
            return self.__setitem__(key, value)

    def __set_value_by_key_list(self, key_list, value):
        assert len(key_list) >= 1
        if len(key_list) == 1:
            self.__set_value(key_list[0], value)
        else:
            subconfig = self.__config_desc[key_list[0]]
            return subconfig.__setitem__('.'.join(key_list[1:]), value)

    def __set_value(self, key, value):
        self.__assert_valid_key(key)
        if key not in self.__config_desc:
            raise JCfgKeyNotFoundError(
                'Config key: {} is not found'.format(key))
        else:
            _value = self.__config_desc[key]
            if isinstance(_value, JsonCfg):
                raise JCfgInvalidSetValueError(
                    'Cannot set value to an exist subconfig.')
            else:
                assert isinstance(_value, JsonCfgValue), _value.type
                return _value.set(value)

    def keys(self):
        for key in sorted(self.__config_desc.keys()):
            if isinstance(self.__config_desc[key], JsonCfgValue):
                yield key
            elif isinstance(self.__config_desc[key], JsonCfg):
                for _k in self.__config_desc[key].keys():
                    yield '{}.{}'.format(key, _k)

    def parse_args(self, description=None):
        parser = argparse.ArgumentParser(description=description)
        
        all_keys = list(self.keys())
        for key in all_keys:
            self.__get_value_by_key_list(key.split('.')).add_to_argument(parser, key)
        
        args = parser.parse_args()

        for k, v in vars(args):
            if k not in all_keys:
                raise ValueError('Unkown config key encountered: {}'.format(k))
            if isinstance(v, list):
                assert self.__getitem__(k).type == list
                new_list = self.__getitem__(k).get().extend(v)
                self.__setitem__(k, new_list)
            else:
                self.__setitem__(k, v)
        

class JsonCfgValue(object):
    def __init__(self, value, value_type, default, **extra_attr):
        self.__value = value
        self.__type = value_type
        self.__default = default
        self.__extra = extra_attr

    def get(self):
        return self.__value

    @property
    def type(self):
        return self.__type

    def set(self, value):
        if isinstance(value, self.__type):
            self.__value = value
        else:
            if isinstance(value, int) and self.__type == float:
                self.__value = value
            else:
                raise JCfgValueTypeMismatchError('The type of this config is set to {}, but is assigned a {}'.format(
                    str(self.__type), str(type(value))))
    
    def add_to_argument(self, arg_parser, key):
        if self.__type == list:
            arg_parser.add_argument('--{}'.format(key), nargs='*')
        else:
            arg_parser.add_argument('--{}'.format(key), type=self.__type)
        return

    @classmethod
    def create_from_value(cls, value):
        '''value can be a pure value (int, float, str, or list) or a custom dict value
        '''
        if isinstance(value, dict) and 'default' in value:
            return cls.__create_from_dict_value(value)
        else:
            return cls.__create_from_pure_value(value)

    @classmethod
    def __create_from_pure_value(cls, value, **extra_attr):
        if isinstance(value, int):
            _type = int
        elif isinstance(value, float):
            _type = float
        elif isinstance(value, str):
            _type = str
        elif isinstance(value, list):
            _type = list
        else:
            raise JCfgInvalidValueError(
                'Invalid value error: {}'.format(str(value)))
        return JsonCfgValue(value, _type, value, **extra_attr)

    @classmethod
    def __create_from_dict_value(cls, value):
        assert isinstance(value, dict)
        assert 'default' in value
        default = value.pop('default')
        return cls.__create_from_pure_value(default, **value)


