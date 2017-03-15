import unittest

from parser.dumper import Dumper
from parser.parser import parse

class TestDumper(unittest.TestCase):

    def check_parser_fail(self, str):
        try:
            self.parse(str)
        except:
            return
        raise AssertionError("This can be parsed but should not: %s" % str)

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
        self.check('let var a: int := 2 in a end', 'let var a: int := 2 in a end')
        self.check('let function f(): int = 1 + 2 in 1 end', 'let function f(): int = (1 + 2) in 1 end')
        self.check('let function f(a: int) = 1 in 1 end', 'let function f(a: int) = 1 in 1 end')
        self.check('let function f(a: int, b: int, c: int) = 2 in 2 end', 'let function f(a: int, b: int, c: int) = 2 in 2 end')
        self.check_parser_fail("let in 1 end")

    def test_fun_call(self):
        self.check("func()", "func()")
        self.check("func(1 + 2)", "func((1 + 2))")
        self.check("func(a, b, c)", "func(a, b, c)")
if __name__ == '__main__':
    unittest.main()
