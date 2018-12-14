
import unittest

from jcfg import JsonCfg
from jcfg import JCfgKeyNotFoundError, JCfgInvalidKeyError, JCfgValueTypeMismatchError, JCfgInvalidSetValueError

test_config = {
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


class TestLoadFromConfigMeta(unittest.TestCase):

    def test_load_meta(self):
        JsonCfg(test_config)
        self.assertTrue(True)

    def test_failed_loading(self):
        try:
            JsonCfg({'2363': 1})
        except JCfgInvalidKeyError:
            self.assertTrue(True)


class TestGetItem(unittest.TestCase):

    def setUp(self):
        self.config = JsonCfg(test_config)

    def test_get(self):
        self.assertEqual(self.config['c'], 'val')
        self.assertEqual(self.config['d'][0], 1)
        self.assertIsInstance(self.config['f']['f_d'], JsonCfg)
        self.assertIsInstance(self.config.f.f_d, JsonCfg)

    def test_concat_get(self):
        self.assertEqual(self.config['f.f_d.f_d_b'][0], 'a')

    def test_failure(self):
        try:
            self.config['f.']
            self.fail('This line should never run!')
        except JCfgInvalidKeyError:
            self.assertTrue(True)

        try:
            self.config['non_exist_key']
            self.fail('This line should never run!')
        except JCfgKeyNotFoundError:
            self.assertTrue(True)

        try:
            self.config['.f.']
            self.fail('This line should never run!')
        except JCfgInvalidKeyError:
            self.assertTrue(True)

        try:
            self.config['f?%f..']
            self.fail('This line should never run!')
        except JCfgInvalidKeyError:
            self.assertTrue(True)


class TestSetItem(unittest.TestCase):
    def setUp(self):
        test_config = {
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
        self.config = JsonCfg(test_config)

    def test_set(self):
        self.config['b'] = 2.0
        self.assertEqual(self.config['b'], 2.0)

        self.config.f.f_b = 9
        self.assertEqual(self.config['f.f_b'], 9)

        try:
            self.config.e = 3.0
            self.fail('This line should never run!')
        except JCfgValueTypeMismatchError:
            self.assertTrue(True)

        try:
            self.config.f.f_d = 'fail'
            self.fail('This line should never run!')
        except JCfgInvalidSetValueError:
            self.assertTrue(True)


def test_argparser():
    test_config = {
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
    
    jcfg = JsonCfg(test_config)
    jcfg.print_config()
    jcfg.parse_args(description='test jcfg')
    jcfg.print_config()



if __name__ == '__main__':
    test_argparser()
    # unittest.main()
    # test_argparser()
