import unittest

from ply.lex import LexError

from .tokenizer import lexer

class TestLexer(unittest.TestCase):

    def check(self, type, value):
        t = lexer.token()
        self.assertEqual(t.type, type)
        self.assertEqual(t.value, value)

    def check_end(self):
        t = lexer.token()
        self.assertIsNone(t)

    def test_basic(self):
        lexer.input("42")
        self.check('NUMBER', 42)
        self.check_end()

    def test_op(self):
        lexer.input("1 + 2 * 3")
        self.check('NUMBER', 1)
        self.check('PLUS', '+')
        self.check('NUMBER', 2)
        self.check('TIMES', '*')
        self.check('NUMBER', 3)
        self.check_end()

    def test_keyword(self):
        lexer.input("var")
        self.check('VAR', 'var')
        self.check_end()

    def test_identifier(self):
        lexer.input("foobar")
        self.check('ID', 'foobar')
        self.check_end()

    def test_error(self):
        lexer.input("foobar@")
        self.check('ID', 'foobar')
        self.assertRaises(LexError, lexer.token)

    def test_unhandled_keyword(self):
        lexer.input("array")
        self.assertRaises(LexError, lexer.token)

if __name__ == '__main__':
    unittest.main()
