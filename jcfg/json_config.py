import re
import argparse
import json
import pprint

import jstyleson

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
            value = config_meta[key]
            if isinstance(value, dict) and _DEFAULT_KEY not in value:
                config_desc[key] = JsonCfg(config_meta[key])
            else:
                config_desc[key] = JsonCfgValue.create_from_value(value)
                if config_desc[key].validate() is False:
                    raise JCfgValidateFailError('Init config failed because validate failure.')
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
        cfg_value = self.__get_by_keys(key_list)
        if isinstance(cfg_value, JsonCfg):
            return cfg_value
        elif isinstance(cfg_value, JsonCfgValue):
            return cfg_value.get()
        else:
            assert False, 'This should never happen!'

    def __getattr__(self, name):
        # if name == '_JsonCfg__config_desc':
        #     return object.__getattr__(self, name)

        self.__assert_valid_key(name)
        if name not in self.__config_desc:
            raise AttributeError('Config key {} not found'.format(name))
        else:
            _value = self.__config_desc[name]
            # print('{} -> {}'.format(name, _value))
            if isinstance(_value, JsonCfg):
                return _value
            else:
                assert isinstance(_value, JsonCfgValue), type(_value)
                return _value.get()

    def _get_value_obj(self, key):
        self.__assert_valid_key(key)
        if key not in self.__config_desc:
            raise JCfgKeyNotFoundError(
                'Config key: {} is not found'.format(key))
        else:
            _value = self.__config_desc[key]
            assert isinstance(_value, (JsonCfg, JsonCfgValue))
            return _value
    
    def __get_by_keys(self, keys):
        assert isinstance(keys, list) and len(keys) > 0
        iter_value = self
        for key in keys:
            iter_value = iter_value._get_value_obj(key)
        return iter_value

    def __setitem__(self, key, value):
        key_list = key.split('.')
        self.__set_value_by_key_list(key_list, value)

    def __setattr__(self, key, value):
        if key == '_JsonCfg__config_desc':
            if key not in self.__dict__:
                return object.__setattr__(self, key, value)
            else:
                raise JCfgInvalidSetValueError('_JsonCfg__config_desc is a reserved key!')

        if key not in self.__config_desc:
            return object.__setattr__(self, key, value)
        else:
            return self.__setitem__(key, value)

    def __set_value_by_key_list(self, key_list, value):
        jcfg_value = self.__get_by_keys(key_list)
        if not isinstance(jcfg_value, JsonCfgValue):
                raise JCfgInvalidSetValueError('Cannot set value to a sub config: {}'.format('.'.join(key_list)))
        jcfg_value.set(value)
        if jcfg_value.validate() is False:
            raise JCfgValidateFailError()

    def keys(self):
        for key in sorted(self.__config_desc.keys()):
            if isinstance(self.__config_desc[key], JsonCfgValue):
                yield key
            elif isinstance(self.__config_desc[key], JsonCfg):
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
        
        cfg_file_dest = '___jcfg_load_path'
        parser.add_argument('-c', help='file path to update config', type=str, metavar='CONFIG_PATH', dest=cfg_file_dest)

        cfg_save_dest = '___jcfg_save_path'
        parser.add_argument('-s', help='file path to dump final config', type=str, metavar='SAVE_PATH', dest=cfg_save_dest)

        all_keys = list(self.public_keys())
        for key in all_keys:
            jcfg_value = self.__get_by_keys(key.split('.'))
            assert isinstance(jcfg_value, JsonCfgValue)
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
                raise ValueError('Unkown config key encountered: {}'.format(k))
            
            k_list = k.split('.')
            cfg_value = self.__get_by_keys(k_list)
            if not isinstance(cfg_value, JsonCfgValue):
                raise JCfgInvalidSetValueError('Cannot set value to a sub config: {}'.format(k))
            cfg_value.set(v)
        
        if cfg_save_path is not None:
            self.save_to_file(cfg_save_path)
    
    def update_from_file(self, json_path):
        with open(json_path) as rfile:
            json_cfg = jstyleson.load(rfile)
        
        def _load_key_value_from_json(json_dict):
            _ret_dict = {}
            for k, v in json_dict.items():
                if isinstance(v, dict):
                    _sub_ret_dict = _load_key_value_from_json(v)
                    for sub_k, sub_v in _sub_ret_dict.items():
                        _new_k = '.'.join([k, sub_k])
                        _ret_dict[_new_k] = sub_v
                else:
                    if k.startswith('_'):
                        raise ValueError('Config key starts with "_" is private key, which is immutable!')
                    _ret_dict[k] = v
            return _ret_dict
        
        new_cfg = _load_key_value_from_json(json_cfg)
        for k, v in new_cfg.items():
            self.__setitem__(k, v)
    
    def save_to_file(self, json_path, indent=4, sort_keys=True):
        config_dict = self.to_dict()
        with open(json_path, 'w') as wf:
            json.dump(config_dict, wf, indent=indent, sort_keys=sort_keys)
        

    def print_config(self, indent=4):
        config_dict = self.to_dict()
        pprint.pprint(config_dict, indent=4)


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


