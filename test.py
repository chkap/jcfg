
import unittest

from jcfg import JsonCfg


class TestLoadFromConfigMeta(unittest.TestCase):

    def test_load_meta(self):

        meta = {
            'a': 1,
            'b': 1.0,
            'c': 'val',
            'd': [1, 2, 3, 4],
            'e': {
                'default': 1,
                'custom_attr': 't',
            },
            'f': {
                'f_a': 1,
                'f_b': 2,
                'f_c': {
                    'default': 1,
                    'custom_attr': 't',
                },
                'f_d': {
                    'f_d_a': 's',
                    'f_d_b': {
                        'default': ['a', 'b', 'c']
                    }
                }
            }
        }
        try:
            JsonCfg(meta)
        except Exception:
            self.fail('failed')
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
