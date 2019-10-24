# jcfg

jcfg is an easy-to-use json-based configuration tool for building python programs.

Suppose that you want to develop an program that has three config options: a file path (type of string), an integer (type of int), and a float number. And also want to be able to load configs from a local file. Then, you can write code like this, with jcfg:

```python
# in file: my_program.py
from jcfg import JsonCfg

def main():
    cfg = JsonCfg({
        'input_path': '',
        'input_int': 0,
        'input_float': 0.0
    })
    cfg.parse_args()

    # do any work you want below
    # you can get the input_path, input_int, or input_float like this:

    res = cfg.input_int + cfg.input_float
    # `cfg.input_int` and `cfg.input_float` will get the actual value depending on the cli input. jcfg have done the type check work for you. If the input option cannot be parsed as an integer, it will raise error

    ....

if __name__ == '__main__':
    main()
    
```

Type `python3 my_program.py -h` in your terminal, you will get:
```bash
usage: test_readme.py [-h] [-c CONFIG_PATH] [--input_float INPUT_FLOAT]
                      [--input_int INPUT_INT] [--input_path INPUT_PATH]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_PATH        file path to update config
  --input_float INPUT_FLOAT
                        type: <class 'float'>, default: 0.0
  --input_int INPUT_INT
                        type: <class 'int'>, default: 0
  --input_path INPUT_PATH
                        type: <class 'str'>, default:
```

As you can see above, these config options can be loaded from either cli input or a json file with cli option `-c your_config.json`. 

# Usage

## To define config options

The config options should be defined based on the dict object provided when constructing `JsonCfg`. Each key in the dict will be the name of an config option, and the corresponding value will be either the default value for this config or a sub-config under this key name, based on:

1. if the value is a dict without the key `_default`, this value will define a sub-config under this key,
2. otherwise, the value indicates the default value (and also some other meta info) for this key. The type of this config will be implicitly determined as the type of the default value. 

For better understanding, here is an example:

```python
cfg = jcfg.JsonCfg({
    'option_int': -1,  # this define an config option with name `option_int` with default value of -1, and also with type of int (type(-1) is int).
    'option_float': 0.0,  # this define config `option_float`, with default value 0.0, and type of float.
    'option_str': 'default_value',  # default value: 'default_value', with type str
    'option_list': [],  # this defins an config with default value of empty list, of type list
    'sub_config': {  # this will define and sub-config
        'sub_int': 0,
        'sub_float': 0.0,
        'sub_sub_config': {  # sub-config can be recursively defined
            'leaf_key': 0, 
        }
    },
    'not_sub_config': {  # however, this won't define a sub-config, but an config with value type: string
        '_default': 'this_is_default_value', 
        '_desc': 'this_si_description',  # this will provide detailed description for this config when typing --help
    }
})
```

## To load configs from cli

All config options could be overrided from cli with the corresponding config key name. For sub-config, the config key name is defined by all the config key name between root config and leaf config. Here is an example to override the sub-config value:

```bash
python3 test.py --sub_config.sub_int 2
```

## To load configs from file

All configs can also be loaded from a json file. Here is an examples:

```json
\\ config.json
{
    "option_str": "new_string",
    "sub_config":{
        "sub_int": 1,
    },
    "sub_config.sub_float": 3
}
```
These config can be updated by `python3 test.py -c config.json`.

Note that, sub-config value can be defined as a dict or key-value pair with full config path, like above.

If both config file and cli option are provided, the config will be **first overrided from config file, then overrided from cli options**.

## Access to configs.

The configs can be easily accessed like this:
```python
cfg.option_int   # or 
cfg['option_int']

# for sub-config
cfg.sub_config.sub_int  # or
cfg['sub_config']['sub_int']  # or
cfg['sub_config.sub_int']
```

# Other features

* Config key startswith `_` denotes private config options, which will never be overrided from cli or file.
* '_default' is the reserved key, you should never define a config with key name '_default'.
* '_desc' is another reserved key for defining cli description of config key
* Some other reserved key startswith `_` may be added someday, to provide more advanced meta control.






