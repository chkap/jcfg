import re


from .error import JCfgInvalidKeyError, JCfgInvalidValueError, JCfgKeyNotFoundError, JCfgValueTypeMismatchError, JCfgInvalidSetValueError


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
            cls.__assert_valid_key(key)
            value = config_meta[key]
            if isinstance(value, dict) and 'default' not in value:
                config_desc[key] = JsonCfg(config_meta[key])
            else:
                config_desc[key] = JsonCfgValue.create_from_value(value)
        return config_desc

    @classmethod
    def __parse_value(cls, value):
        value_type = cls.__check_value_type(value)
        if value_type == 'pure_value':
            value_desc = cls.__create_value_desc_from_default_value(value)
        elif value_type == 'custom_value':
            assert 'default' in value
            value_desc = cls.__create_value_desc_from_default_value(
                value['default'])
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
        value_desc['value'] = value
        value_desc['default'] = value
        assert cls.__check_value_type(value) == 'pure_value'
        if isinstance(value, int):
            value_desc['type'] = int
        elif isinstance(value, float):
            value_desc['type'] = float
        elif isinstance(value, str):
            value_desc['type'] = str
        elif isinstance(value, list):
            value_desc['type'] = list
        else:
            assert False, 'This should never happen!'

        return value_desc

    @classmethod
    def __assert_valid_key(cls, key):
        if cls.__reo.fullmatch(key) is None:
            raise JCfgInvalidKeyError(
                'Invalid config key: {}, only [A-Za-z0-9_] is allowed.'.format(key))
        else:
            return

    @classmethod
    def __check_value_type(cls, value):
        if isinstance(value, dict):
            if 'default' in value and cls.__check_value_type(value['default']) == 'pure_value':
                return 'custom_value'  # is a subconfig
            else:
                return 'subconfig'
        elif isinstance(value, int) or isinstance(value, float) or isinstance(value, list) or isinstance(value, str):
            return 'pure_value'
        else:
            raise JCfgInvalidValueError(
                'Invalid value error: {}'.format(str(value)))

    def __getitem__(self, key):
        key_list = key.split('.')
        return self.__get_value_by_key_list(key_list)

    def __getattr__(self, name):
        if name == '_JsonCfg__config_desc':
            return object.__getattr__(self, name)
        
        self.__assert_valid_key(name)
        # print('getattr: {}'.format(name))
        # print('config_desc type: {}'.format(type(self.__config_desc)))
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
                assert isinstance(_value, JsonCfgValue), type(_value)
                return _value.get()

    def __setitem__(self, key, value):
        key_list = key.split('.')
        self.__set_value_by_key_list(key_list, value)
    
    def __setattr__(self, key, value):
        # print('setattr: {}'.format(key))
        if key == '_JsonCfg__config_desc' or key not in self.__config_desc:
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
                raise JCfgInvalidSetValueError('Cannot set value to an exist subconfig.')
            else:
                assert isinstance(_value, JsonCfgValue), type(_value)
                return _value.set(value)


class JsonCfgValue(object):
    def __init__(self, value, value_type, default, **extra_attr):
        self.__value = value
        self.__type = value_type
        self.__default = default
        self.__extra = extra_attr

    def get(self):
        return self.__value

    def set(self, value):
        if isinstance(value, self.__type):
            self.__value = value
        else:
            if isinstance(value, int) and self.__type == float:
                self.__value = value
            else:
                raise JCfgValueTypeMismatchError('The type of this config is set to {}, but is assigned a {}'.format(
                    str(self.__type), str(type(value))))

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
