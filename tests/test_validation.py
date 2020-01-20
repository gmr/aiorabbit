# coding=utf-8
from . import testing


class ValidationTestCase(testing.ClientTestCase):

    def test_validate_bool(self):
        self.client._validate_bool('valid', True)
        self.client._validate_bool('valid', False)

    def test_validate_bool_raises(self):
        with self.assertRaises(TypeError):
            self.client._validate_bool('invalid', '')

    def test_validate_exchange_name(self):
        self.client._validate_exchange_name('valid', '')
        self.client._validate_exchange_name('valid', 'foo-bar:baz_0')
        self.client._validate_exchange_name('valid', 'über-zentrale')

    def test_validate_exchange_name_raises(self):
        with self.assertRaises(TypeError):
            self.client._validate_exchange_name('invalid', True)
        with self.assertRaises(ValueError):
            self.client._validate_exchange_name(
                'invalid', '{:*<500}'.format('*'))
        with self.assertRaises(ValueError):
            self.client._validate_exchange_name('invalid', 'foo*bar')

    def test_validate_field_table(self):
        self.client._validate_field_table('valid', {'🐇': '🐇', '🐇🐇': True})

    def test_validate_field_table_raises(self):
        with self.assertRaises(TypeError):
            self.client._validate_field_table('invalid', True)
        with self.assertRaises(ValueError):
            self.client._validate_field_table(
                'invalid', {'{:*<500}'.format('*'): 1})
        with self.assertRaises(ValueError):
            self.client._validate_field_table('invalid', {True: False})

    def test_validate_short_str(self):
        self.client._validate_short_str('valid', 'a!@b-34f🐇')

    def test_validate_short_str_raises(self):
        with self.assertRaises(TypeError):
            self.client._validate_short_str('invalid', True)
        with self.assertRaises(ValueError):
            self.client._validate_short_str('invalid', '{:*<500}'.format('*'))
