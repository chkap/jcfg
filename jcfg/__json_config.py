import re
import argparse
import json

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
        cfg_value = self.__get_value_by_key_list(key_list)
        if isinstance(cfg_value, JsonCfg):
            return cfg_value
        elif isinstance(cfg_value, JsonCfgValue):
            return cfg_value.get()
        else:
            assert False, 'This should never happen!'
        return 

    def __getattr__(self, name):
        # if name == '_JsonCfg__config_desc':
        #     return object.__getattr__(self, name)

        self.__assert_valid_key(name)
        if name not in self.__config_desc:
            return AttributeError('Config key {} not found'.format(name))
        else:
            _value = self.__config_desc[name]
            # print('{} -> {}'.format(name, _value))
            if isinstance(_value, JsonCfg):
                return _value
            else:
                assert isinstance(_value, JsonCfgValue), type(_value)
                return _value.get()

    def __get_value_by_key_list(self, key_list):
        assert len(key_list) >= 1
        cfg_value = self
        for key in key_list:
            cfg_value = cfg_value._get_value(key)
        return cfg_value
        # if len(key_list) == 1:
        #     return self._get_value(key_list[0])
        # else:
        #     return self.__get_value_by_key_list(key_list[:-1])[key_list[-1]]

    def _get_value(self, key):
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
                raise JCfgInvalidSetValueError('_JsonCfg__config_desc is a reserved key!')

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
    
    def items(self):
        for key in self.keys():
            yield key, self.__getitem__(key)

    def parse_args(self, description=None, update_from_file=True):
        parser = argparse.ArgumentParser(description=description)
        
        cfg_file_dest = '___jcfg_path'
        if update_from_file is True:
            parser.add_argument('-c', help='file path to update config', type=str, metavar='CONFIG_PATH', dest=cfg_file_dest)

        all_keys = list(self.keys())
        for key in all_keys:
            self.__get_value_by_key_list(key.split('.')).add_to_argument(parser, key)
        
        args = parser.parse_args()
        args = vars(args)
        if update_from_file is True:
            cfg_path = args.pop(cfg_file_dest)
            if cfg_path is not None:
                self.update_from_file(cfg_path)

        for k, v in args.items():
            # print('{} -> {}'.format(k, v))
            if v is None:
                continue
            if k not in all_keys:
                raise ValueError('Unkown config key encountered: {}'.format(k))
            
            k_list = k.split('.')
            cfg_value = self.__get_value_by_key_list(k_list)
            if isinstance(v, list):
                cfg_value.set(v)
            else:
                cfg_value.set(v)
    
    def update_from_file(self, json_path):
        with open(json_path) as rfile:
            json_cfg = json.load(rfile)
        
        for k, v in json_cfg.items():
            self.__setitem__(k, v)
    
    def print_config(self):
        for k in self.keys():
            print('{} = {}'.format(k, self.__getitem__(k)))


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
        self.__extra = extra_attr
        # print('{} -> {}'.format(value, value_type))

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
        '''value can be a pure value (int, float, str, or list) or a custom dict value
        '''
        if isinstance(value, dict) and 'default' in value:
            return cls.__create_from_dict_value(value)
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
                'Invalid value: {}'.format(str(value)))
        return JsonCfgValue(value, _type, value, **extra_attr)

    @classmethod
    def __create_from_dict_value(cls, value):
        assert isinstance(value, dict)
        assert 'default' in value
        default = value.pop('default')
        return cls.__create_from_pure_value(default, **value)


