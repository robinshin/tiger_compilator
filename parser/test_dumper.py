import unittest

from parser.dumper import Dumper
from parser.parser import parse

class TestDumper(unittest.TestCase):

    def parse_dump(self, text):
        tree = parse(text)
        return tree.accept(Dumper(semantics=False))

    def check(self, text, expected):
        self.assertEqual(self.parse_dump(text), expected)

    def test_literal(self):
        self.check("42", "42")

    def test_priority(self):
        self.check("1+2*3", "(1 + (2 * 3))")
        self.check("2*3+1", "((2 * 3) + 1)")

    def test_ifthenelse(self):
        self.check('if 1 then 2 else 3', 'if 1 then 2 else 3')

    def test_letinend(self):
        self.check('let var a := 2 in a end', 'let var a := 2 in a end')

if __name__ == '__main__':
    unittest.main()
