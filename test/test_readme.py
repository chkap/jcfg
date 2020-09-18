# in file: my_program.py
from jcfg import JsonCfg

def main():
    cfg = JsonCfg({
        'input_path': '',
        'input_int': 0,
        'input_float': 0.0,
        'test_default': {
            '_default': 3,
            '_desc': 'description'
        }
    })
    cfg.parse_args()

    # do any work you want below
    # you can get the input_path, input_int, or input_float like this:

    res = cfg.input_int + cfg.input_float
    # `cfg.input_int` and `cfg.input_float` will get the actual value depending on the cli input. jcfg have done the type check work for you. If the input option cannot be parsed as an integer, it will raise error
    print(res)

if __name__ == '__main__':
    main()
    