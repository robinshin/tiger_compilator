import unittest

from ast.evaluator import Evaluator
from ast.nodes import IntegerLiteral, BinaryOperator
from parser.parser import parse

class TestEvaluator(unittest.TestCase):

    def check(self, ast, expected):
        self.assertEqual(ast.accept(Evaluator()), expected)

    def parse_check(self, str, expected):
        self.assertEqual(parse(str).accept(Evaluator()), expected)

    def test_literal(self):
        self.check(IntegerLiteral(42), 42)

    def test_basic_operator(self):
        self.check(BinaryOperator('+', IntegerLiteral(10), IntegerLiteral(20)), 30)

    def test_priorities(self):
        self.check(BinaryOperator('+', IntegerLiteral(1), BinaryOperator('*', IntegerLiteral(2), IntegerLiteral(3))), 7)

    def test_parse_literal(self):
        self.parse_check('42', 42)

    def test_parse_sequence(self):
        self.parse_check('1+(2+3)+4', 10)

    def test_precedence(self):
        self.parse_check('1 + 2 * 3', 7)
        self.parse_check('2 * 3 + 1', 7)
        self.parse_check('10 - 1 - 2', 7)
        self.parse_check('1 | 0', 1)
        self.parse_check('0 & 0', 0)
        self.parse_check('1 < 4', 1)
        self.parse_check('3 > 5', 0)
        self.parse_check('4 = 5', 0)
        self.parse_check('6 <> 4', 1)
        self.parse_check('if 1 then 100 else 200 + 300', 100)

if __name__ == '__main__':
    unittest.main()
