
import unittest
import sys
sys.path.insert(0, '.')
import subprocess

from jcfg import JsonCfg
from jcfg import JCfgKeyNotFoundError, JCfgInvalidKeyError, JCfgValueTypeMismatchError, JCfgInvalidSetValueError

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
                '_default': ['a', 'b', 'c']
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
                        '_default': ['a', 'b', 'c']
                    }
                }
            }
        }
        self.config = JsonCfg(test_config)

    def test_get(self):
        self.assertEqual(self.config['c'], 'val')
        self.assertEqual(self.config['d'][0], 1)
        # print(self.config.e)
        # print(self.config.f.f_a)
        self.assertEqual(self.config.e, True)
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
                        '_default': ['a', 'b', 'c']
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

        self.config.e = False
        self.assertEqual(self.config.e, False)

        try:
            self.config.e = 1
            self.fail('This line should never run!')
        except JCfgValueTypeMismatchError:
            self.assertTrue(True)

        try:
            self.config.f.f_d = 'fail'
            self.fail('This line should never run!')
        except JCfgInvalidSetValueError:
            self.assertTrue(True)

class TestParseArgs(unittest.TestCase):

    def test_argparser(self):
        self.assertTrue(True, msg='Testing argparser from CLI success!')
        subprocess.check_call(['python3', 'test_parse_from_args_main.py', '-c', 'test_config_with_comments.json', '--a', '5'])
        self.assertTrue(True, msg='Testing argparser from CLI success!')

class TestPublicKey(unittest.TestCase):
    def setUp(self):
        test_config = {
            '_this_is_private_key': 1,
            'this_is_public_key': 1
        }
        self.config = JsonCfg(test_config)

    def test_parse_from_args(self):
        self.config.print_config()
        self.assertTrue(True)

class TestConfigMeta(unittest.TestCase):

    def test_parse_with_config_meta(self):
        test_config = {
            'foo': {
                '_default': 2,
                '_desc': 'this is a test description!'
            }
        }
        self.config = JsonCfg(test_config)
        self.config.print_config()
        self.assertTrue(True)

class TestConfigMeta(unittest.TestCase):
    def test_save_to_file(self):
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
                        '_default': ['a', 'b', 'c']
                    }
                }
            }
        }

        cfg = JsonCfg(test_config)
        tmp_dst_file = 'test_tmp_config.json'
        cfg.save_to_file(tmp_dst_file)
        cfg.update_from_file(tmp_dst_file)
        cfg.print_config()

if __name__ == '__main__':
    # test_argparser()
    unittest.main()
    # test_argparser()
