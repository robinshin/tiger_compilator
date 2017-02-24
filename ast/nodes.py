#
# This file contains the definition of the nodes used in the Tiger
# project. It must not be modified.
#


class Node:
    """The Node type represents a node in the AST. Its notable fields are:
      - children: a list of children to visit when visiting the AST and no
                  treatment has been given for this kind of node.
    """

    def __init__(self):
        self.children = []

    def accept(self, visitor):
        return visitor.visit(self)


class IntegerLiteral(Node):

    def __init__(self, intValue):
        super().__init__()
        assert isinstance(intValue, int), "IntegerLiteral only accept integers"
        self.intValue = intValue


class BinaryOperator(Node):

    def __init__(self, op, left, right):
        super().__init__()
        assert isinstance(op, str), "operator must be a string"
        assert isinstance(left, Node), "left operand must be a Node instance"
        assert isinstance(right, Node), "right operand must be a Node instance"
        self.op = op
        self.left = left
        self.right = right
        self.children = [left, right]


class Let(Node):

    def __init__(self, decls, exps):
        super().__init__()
        assert isinstance(decls, list), "declarations must be put in a list"
        for decl in decls:
            assert isinstance(decl, Node), \
                    "declarations must be Node instances"
        assert isinstance(exps, list), "expressions must be put in a list"
        for exp in exps:
            assert isinstance(exp, Node), "expressions must be Node instances"
        self.decls = decls
        self.exps = exps
        self.children = decls + exps


class Identifier(Node):

    def __init__(self, name):
        super().__init__()
        assert isinstance(name, str), "name must be a string"
        self.name = name
        self.decl = None


class IfThenElse(Node):

    def __init__(self, condition, then_part, else_part):
        super().__init__()
        assert isinstance(condition, Node), "condition must be a Node instance"
        assert isinstance(then_part, Node), "then_part must be a Node instance"
        assert isinstance(else_part, Node), "else_part must be a Node instance"
        self.condition = condition
        self.then_part = then_part
        self.else_part = else_part
        self.children = [condition, then_part, else_part]
