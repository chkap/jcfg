import re
import argparse
import json
import pprint

import jstyleson
import yaml

from .error import JCfgInvalidKeyError, JCfgInvalidValueError, JCfgKeyNotFoundError, JCfgValueTypeMismatchError, \
    JCfgInvalidSetValueError, JCfgEmptyConfigError, JCfgValidateFailError

_DEFAULT_KEY = '_default'

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
        if len(config_meta) == 0:
            raise JCfgEmptyConfigError()
        for key in config_meta:
            cls.__assert_valid_key(key)
            if key in dir(cls):
                raise JCfgInvalidKeyError('{} is reserved, should not be used as config key.'.format(key))
            value = config_meta[key]
            if isinstance(value, dict) and _DEFAULT_KEY not in value:
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
    
    def __get_sub_config_or_value(self, key):
        assert isinstance(key, str)
        if key == '':
            raise JCfgInvalidKeyError('Empty config key')
        key_list = key.split('.', maxsplit=1)
        if len(key_list) == 1:
            _key = key_list[0]
            self.__assert_valid_key(_key)
            if _key not in self.__config_desc:
                raise JCfgKeyNotFoundError('Config key: {} not defined!'.format(key))
            else:
                _value = self.__config_desc[_key]
                return _value
        else:
            sub_config = self.__get_sub_config_or_value(key_list[0])
            if isinstance(sub_config, JsonCfgValue):
                raise JCfgInvalidKeyError('Cannot get sub key of JsonCfgValue: {}'.format(key))
            assert isinstance(sub_config, JsonCfg)
            return sub_config.__get_sub_config_or_value(key_list[1])

    def __getitem__(self, key):
        _value = self.__get_sub_config_or_value(key)
        if isinstance(_value, JsonCfgValue):
            return _value.get()
        else:
            assert isinstance(_value, JsonCfg), type(_value)
            return _value

    def __getattr__(self, name):
        return self.__getitem__(name)
    
    def __setitem__(self, key, value):
        jcfg_value = self.__get_sub_config_or_value(key)
        if not isinstance(jcfg_value, JsonCfgValue):
            raise JCfgInvalidSetValueError('Cannot set value to a sub config: {}'.format(key))
        jcfg_value.set(value)
        if jcfg_value.validate() is False:
            raise JCfgValidateFailError('Validate failure of key: {}={}'.format(key, value))

    def __setattr__(self, key, value):
        if key == '_JsonCfg__config_desc':
            if key not in self.__dict__:
                return object.__setattr__(self, key, value)

        return self.__setitem__(key, value)

    def keys(self):
        for key in sorted(self.__config_desc.keys()):
            if isinstance(self.__config_desc[key], JsonCfgValue):
                yield key
            else:
                assert isinstance(self.__config_desc[key], JsonCfg)
                for _k in self.__config_desc[key].keys():
                    yield '{}.{}'.format(key, _k)
    
    def items(self):
        for key in self.keys():
            yield key, self.__getitem__(key)
    
    def to_dict(self):
        dst = {}
        for key, val in self.__config_desc.items():
            if isinstance(val, JsonCfgValue):
                dst[key] = val.get()
            else:
                assert isinstance(val, JsonCfg)
                dst[key] = val.to_dict()
        
        return dst
    
    def public_keys(self):
        for key in sorted(self.__config_desc.keys()):
            if key.startswith('_'):
                continue
            if isinstance(self.__config_desc[key], JsonCfgValue):
                yield key
            elif isinstance(self.__config_desc[key], JsonCfg):
                for _k in self.__config_desc[key].public_keys():
                    yield '{}.{}'.format(key, _k)
    
    def public_items(self):
        for key in self.public_keys():
            yield key, self.__getitem__(key)

    def parse_args(self, description=None):
        parser = argparse.ArgumentParser(description=description)
        
        cfg_file_dest = '@load_path'
        parser.add_argument('-c', help='file path to update config', type=str, metavar='CONFIG_PATH', dest=cfg_file_dest)

        cfg_save_dest = '@save_path'
        parser.add_argument('-s', help='file path to dump final config', type=str, metavar='SAVE_PATH', dest=cfg_save_dest)

        all_keys = list(self.public_keys())
        for key in all_keys:
            jcfg_value = self.__get_sub_config_or_value(key)
            assert isinstance(jcfg_value, JsonCfgValue), key
            jcfg_value.add_to_argument(parser, key)
        
        args = parser.parse_args()
        args = vars(args)
        cfg_path = args.pop(cfg_file_dest)
        if cfg_path is not None:
            self.update_from_file(cfg_path)

        cfg_save_path = args.pop(cfg_save_dest)

        for k, v in args.items():
            if v is None:
                continue
            if k not in all_keys:
                raise ValueError('Unkown config key: {}'.format(k))
            
            cfg_value = self.__get_sub_config_or_value(k)
            if not isinstance(cfg_value, JsonCfgValue):
                raise JCfgInvalidSetValueError('Cannot set value to a sub config: {}'.format(k))
            cfg_value.set(v)
            if cfg_value.validate() is False:
                raise JCfgValidateFailError('Validate failure of key: {}={}'.format(k, v))
        
        if cfg_save_path is not None:
            self.save_to_file(cfg_save_path)
    
    def update_from_file(self, config_path):
        if config_path.endswith('.yaml'):
            with open(config_path, encoding='utf-8') as rf:
                config = yaml.safe_load(rf)
        else:
            # load config as json file
            with open(config_path, encoding='utf-8') as rf:
                config = jstyleson.load(rf)
        
        def _load_key_value_from_dict(config):
            _ret_dict = {}
            for k, v in config.items():
                if isinstance(v, dict):
                    _sub_ret_dict = _load_key_value_from_dict(v)
                    for sub_k, sub_v in _sub_ret_dict.items():
                        _new_k = '.'.join([k, sub_k])
                        _ret_dict[_new_k] = sub_v
                else:
                    if k.startswith('_'):
                        raise ValueError('Config key starts with "_" is private key, which is immutable!')
                    _ret_dict[k] = v
            return _ret_dict
        
        new_cfg = _load_key_value_from_dict(config)
        for k, v in new_cfg.items():
            self.__setitem__(k, v)
    
    def save_to_file(self, save_path, indent=4, sort_keys=True):
        config_dict = self.to_dict()
        if save_path.endswith('.yaml'):
            with open(save_path, 'w', encoding='utf-8') as wf:
                yaml.safe_dump(config_dict, wf)
        else:
            with open(save_path, 'w') as wf:
                json.dump(config_dict, wf, indent=indent, sort_keys=sort_keys)

    def print_config(self, indent=4):
        config_dict = self.to_dict()
        pprint.pprint(config_dict, indent=4)
    
    def validate(self):
        for key in self.keys():
            jcfg_value = self.__get_by_keys(key.split('.'))
            if jcfg_value.validate() is False:
                raise JCfgValidateFailError('Validate failure of key: {}={}'.format(key, jcfg_value.get()))


def _str2bool(s):
    if s.lower() in ['1', 'true']:
        return True
    elif s.lower() in ['0', 'false']:
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value (1 or true for True, 0 or false for False) expected.')


class JsonCfgValue(object):
    def __init__(self, value, value_type, default, **extra_attr):
        self.__value = value
        self.__type = value_type
        self.__default = default
        self.__validate_func = extra_attr.pop('_validate', None)
        if self.__validate_func is not None:
            assert callable(self.__validate_func), 'Validate_func need to be callable!'
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
    
    def validate(self):
        if self.__validate_func is None:
            return True
        else:
            return self.__validate_func(self.get())
    
    def get_meta(self, key):
        if key in self.__extra:
            return self.__extra[key]
        else:
            return None
    
    def add_to_argument(self, arg_parser, key):
        desc = self.get_meta('_desc')
        if desc is not None:
            help_info = '{}. type: {}, default: {}'.format(desc, self.type, self.get())
        else:
            help_info = 'type: {}, default: {}'.format(self.type, self.get())
        if self.__type == list:
            arg_parser.add_argument('--{}'.format(key), nargs='*', help=help_info)
        elif self.__type == bool:
            arg_parser.add_argument('--{}'.format(key), type=_str2bool, help=help_info)
        else:
            arg_parser.add_argument('--{}'.format(key), type=self.__type, help=help_info)
        return

    @classmethod
    def create_from_value(cls, value):
        '''value can be a pure value (int, float, str, list, tuple) or a custom dict value
        '''
        if isinstance(value, dict) and _DEFAULT_KEY in value:
            return cls.__create_from_dict_value(value)
        elif isinstance(value, tuple):
            if len(value) == 2:
                assert isinstance(value[1], str), 'The second element in the tuple should be of type str, for config description.'
                dict_value={
                    '_default': value[0],
                    '_desc': value[1]
                }
                return cls.create_from_value(dict_value)
            elif len(value) == 3:
                assert isinstance(value[1], str), 'The 2nd element in the tuple should be of type str, for config description.'
                assert callable(value[2]), 'The 3rd element in the tuple should be callable, for validating values.'
                dict_value = {
                    '_default': value[0],
                    '_desc': value[1],
                    '_validate': value[2],
                }
                return cls.create_from_value(dict_value)
            else:
                raise ValueError('Currently only 2 or 3 -element tuple is supported for init configs.')
        else:
            return cls.__create_from_pure_value(value)

    @classmethod
    def __create_from_pure_value(cls, value, **extra_attr):
        if isinstance(value, bool):
            _type = bool
        elif isinstance(value, int):
            _type = int
        elif isinstance(value, float):
            _type = float
        elif isinstance(value, str):
            _type = str
        elif isinstance(value, list):
            _type = list
        else:
            raise JCfgInvalidValueError(
                'Invalid value: {}'.format(value))
        return JsonCfgValue(value, _type, value, **extra_attr)

    @classmethod
    def __create_from_dict_value(cls, value):
        assert isinstance(value, dict)
        assert _DEFAULT_KEY in value
        default = value.pop(_DEFAULT_KEY)

        # get description
        desc = value.get('_desc', '')
        assert isinstance(desc, str), 'Description for a key should be str!'
        return cls.__create_from_pure_value(default, **value)


