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
        self.type = None

    def accept(self, visitor):
        return visitor.visit(self)


class IntegerLiteral(Node):

    def __init__(self, intValue):
        super().__init__()
        assert isinstance(intValue, int), "IntegerLiteral only accept integers"
        self.intValue = intValue

    def __repr__(self):
        return "Int(%d)" % self.intValue


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
            assert isinstance(decl, Decl), \
                    "declarations must be VarDecl or FunDecl instances"
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
        self.depth = None

    def __repr__(self):
        return "Id(%s)" % self.name


class IfThenElse(Node):

    def __init__(self, condition, then_part, else_part):
        super().__init__()
        assert isinstance(condition, Node), "condition must be a Node instance"
        assert isinstance(then_part, Node), "then_part must be a Node instance"
        assert else_part is None or isinstance(else_part, Node), \
            "else_part must be a Node instance or None"
        self.condition = condition
        self.then_part = then_part
        self.else_part = else_part
        self.children = [condition, then_part]
        if else_part is not None:
            self.children.append(else_part)


class Type(Node):

    def __init__(self, typename):
        super().__init__()
        assert isinstance(typename, str), "type name must be a string"
        self.typename = typename

    def __repr__(self):
        return "Type(%s)" % self.typename


class Decl(Node):
    """Abstract type regrouping various entity declarations"""

    def __init__(self):
        super().__init__()
        self.escapes = False
        self.depth = None


class VarDecl(Decl):

    def __init__(self, name, type, exp):
        super().__init__()
        assert isinstance(name, str), "variable name must be a string"
        assert isinstance(type, Type) or type is None, \
            "type must be a Type instance or None"
        assert isinstance(exp, Node) or exp is None, \
            "expression must be a Node instance or None"
        self.name = name
        self.type = type
        self.exp = exp
        self.children = [c for c in [type, exp] if c is not None]

    def __repr__(self):
        return "VarDecl(%s)" % self.name


class FunDecl(Decl):

    def __init__(self, name, args, type, exp):
        super().__init__()
        assert isinstance(name, str), "function name must be a string"
        assert isinstance(args, list), "arguments must be a list"
        for arg in args:
            assert isinstance(arg, VarDecl), \
              "arguments must be a list of VarDecl instances"
        assert isinstance(type, Type) or type is None, \
            "type must be a Type instance or None"
        assert isinstance(exp, Node), "expression must be a Node instance"
        self.name = name
        self.args = args
        self.type = type
        self.exp = exp
        self.children = [c for c in args + [type, exp] if c is not None]

    def __repr__(self):
        return "FunDecl(%s)" % self.name


class FunCall(Node):

    def __init__(self, identifier, params):
        super().__init__()
        assert isinstance(identifier, Identifier), \
            "function name must be an Identifier instance"
        assert isinstance(params, list), \
            "parameters must be a list"
        for param in params:
            assert isinstance(param, Node), \
                "parameters must be a list of Node instances"
        self.identifier = identifier
        self.params = params
        self.children = [identifier] + params


class SeqExp(Node):

    def __init__(self, exps):
        super().__init__()
        assert isinstance(exps, list), \
            "expressions must be a list"
        for exp in exps:
            assert isinstance(exp, Node), \
                "expressions must be a list of Node instances"
        self.exps = exps
        self.children = exps


class Loop(Node):

    def __init__(self):
        super().__init__()


class While(Loop):

    def __init__(self, condition, exp):
        super().__init__()
        assert isinstance(condition, Node), "condition must be a Node instance"
        assert isinstance(exp, Node), "expression must be a Node instance"
        self.condition = condition
        self.exp = exp
        self.children = [condition, exp]


class For(Loop):

    def __init__(self, indexdecl, low_bound, high_bound, exp):
        super().__init__()
        assert isinstance(indexdecl, IndexDecl), \
            "index declaration must be a IndexDecl instance"
        assert isinstance(low_bound, Node), \
            "low bound must be a Node instance"
        assert isinstance(high_bound, Node), \
            "high bound must be a Node instance"
        assert isinstance(exp, Node), \
            "expression must be a Node instance"
        self.indexdecl = indexdecl
        self.low_bound = low_bound
        self.high_bound = high_bound
        self.exp = exp
        self.children = [indexdecl, low_bound, high_bound, exp]


class IndexDecl(Decl):

    def __init__(self, name):
        super().__init__()
        assert isinstance(name, str), "variable name must be a string"
        self.name = name

    def __repr__(self):
        return "Idx(%s)" % self.name


class Break(Node):

    def __init__(self):
        super().__init__()
        self.loop = None


class Assignment(Node):

    def __init__(self, identifier, exp):
        super().__init__()
        assert isinstance(identifier, Identifier), \
            "left-hand side of assignment must be an Identifier instance"
        assert isinstance(exp, Node), \
            "right-hande side of assignment must be a Node instance"
        self.identifier = identifier
        self.exp = exp
        self.children = [identifier, exp]


class Intrinsics(Node):

    def __init__(self):
        super().__init__()
