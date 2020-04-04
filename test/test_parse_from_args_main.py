import sys
sys.path.insert(0, '..')

from jcfg import JsonCfg

def main():
    test_config = {
            'a': 1,
            'b': 1.0,
            'c': 'val',
            'd': [1, 2, 3, 4],
            'e': {
                '_default': True,
                '_custom_attr': 't',
            },
            'f': {
                'f_a': 1,
                'f_b': 2,
                'f_c': {
                    '_default': 1,
                    '_custom_attr': 't',
                },
                'f_d': {
                    'f_d_a': 's',
                    'f_d_b': {
                        '_default': ['a', 'b', 'c'],
                        '_desc': 'test_description'
                    }
                }
            },
            'g': (3, 'this is a description str')  # define an option with 2-size tuple
        }
    
    jcfg = JsonCfg(test_config)
    jcfg.print_config()
    jcfg.parse_args(description='test jcfg')
    jcfg.print_config()


if __name__ == "__main__":
    main()    
