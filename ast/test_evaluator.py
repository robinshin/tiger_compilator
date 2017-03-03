import unittest

from ast.evaluator import Evaluator
from ast.nodes import IntegerLiteral, BinaryOperator
from parser.parser import parse

class TestEvaluator(unittest.TestCase):

    def check(self, ast, expected):
        self.assertEqual(ast.accept(Evaluator()), expected)

    def parse_check(self, str, expected):
        self.assertEqual(parse(str).accept(Evaluator()), expected)

    def parse_failure(self, str):
        try:
            parse(str)
        except:
            return
        raise NameError('AssertionError')

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
        self.parse_failure('10 = 10 = 10')

    def test_precedence(self):
        self.parse_check('1 + 2 * 3', 7)
        self.parse_check('2 * 3 + 1', 7)

    def test_basic_operator_arith(self):
        self.check(BinaryOperator('-', IntegerLiteral(10), IntegerLiteral(5)), 5)
        self.parse_check('10 - 1 - 2', 7)
        self.check(BinaryOperator('/', IntegerLiteral(6), IntegerLiteral(2)), 3)
        self.check(BinaryOperator('*', IntegerLiteral(6), IntegerLiteral(2)), 12)
        self.check(BinaryOperator('/', IntegerLiteral(5), IntegerLiteral(2)), 2)

    def test_basic_operator_logic(self):
        self.check(BinaryOperator('|', IntegerLiteral(1), IntegerLiteral(0)), 1) 
        self.check(BinaryOperator('|', IntegerLiteral(0), IntegerLiteral(0)), 0)
        self.check(BinaryOperator('|', IntegerLiteral(1), IntegerLiteral(1)), 1)
        self.check(BinaryOperator('&', IntegerLiteral(1), IntegerLiteral(0)), 0) 
        self.check(BinaryOperator('&', IntegerLiteral(0), IntegerLiteral(0)), 0)
        self.check(BinaryOperator('&', IntegerLiteral(1), IntegerLiteral(1)), 1)

    def test_basic_comparison(self):
        self.check(BinaryOperator('<', IntegerLiteral(5), IntegerLiteral(3)), 0) 
        self.check(BinaryOperator('<', IntegerLiteral(1), IntegerLiteral(4)), 1)
        self.check(BinaryOperator('<', IntegerLiteral(5), IntegerLiteral(5)), 0)
        self.check(BinaryOperator('<=', IntegerLiteral(5), IntegerLiteral(3)), 0) 
        self.check(BinaryOperator('<=', IntegerLiteral(1), IntegerLiteral(4)), 1)
        self.check(BinaryOperator('<=', IntegerLiteral(5), IntegerLiteral(5)), 1)
        self.check(BinaryOperator('>', IntegerLiteral(5), IntegerLiteral(3)), 1) 
        self.check(BinaryOperator('>', IntegerLiteral(1), IntegerLiteral(4)), 0)
        self.check(BinaryOperator('>', IntegerLiteral(5), IntegerLiteral(5)), 0)
        self.check(BinaryOperator('>=', IntegerLiteral(5), IntegerLiteral(3)), 1) 
        self.check(BinaryOperator('>=', IntegerLiteral(1), IntegerLiteral(4)), 0)
        self.check(BinaryOperator('>=', IntegerLiteral(5), IntegerLiteral(5)), 1)
        self.check(BinaryOperator('=', IntegerLiteral(3), IntegerLiteral(5)), 0) 
        self.check(BinaryOperator('=', IntegerLiteral(5), IntegerLiteral(5)), 1)
        self.check(BinaryOperator('<>', IntegerLiteral(3), IntegerLiteral(5)), 1) 
        self.check(BinaryOperator('<>', IntegerLiteral(5), IntegerLiteral(5)), 0)

    def test_ifthenelse(self):
        self.parse_check('if 1 then 100 else 200 + 300', 100)
        self.parse_check('if 0 then 100 else 200 + 300', 500)

if __name__ == '__main__':
    unittest.main()
