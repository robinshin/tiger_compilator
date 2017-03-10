from ast.nodes import *
from utils.visitor import *


class Dumper(Visitor):

    def __init__(self, semantics):
        """Initialize a new Dumper visitor. If semantics is True,
        additional information will be printed along with declarations
        and identifiers."""
        self.semantics = semantics

    @visitor(None)
    def visit(self, node):
        raise Exception("unable to dump %s" % node)

    @visitor(IntegerLiteral)
    def visit(self, i):
        return str(i.intValue)

    @visitor(BinaryOperator)
    def visit(self, binop):
        # Always use parentheses to reflect grouping and associativity,
        # even if they may be superfluous.
        return "(%s %s %s)" % \
               (binop.left.accept(self), binop.op, binop.right.accept(self))

    @visitor(IfThenElse)
    def visit(self, ifthenelse):
        return "if %s then %s else %s" % (ifthenelse.condition.accept(self), ifthenelse.then_part.accept(self), ifthenelse.else_part.accept(self))

    @visitor(VarDecl)
    def visit(self, decl):
        return "var %s := %s" % (decl.name, decl.exp.accept(self))

    @visitor(Let)
    def visit(self, let):
        decls = ''
        expr = ''
        for decl in let.decls:
            decls += decl.accept(self)
        for exp in let.exps:
            expr += exp.accept(self)
        return "let %s in %s end" % (decls, expr)

    @visitor(Identifier)
    def visit(self, id):
        if self.semantics:
            diff = id.depth - id.decl.depth
            scope_diff = "{%d}" % diff if diff else ''
        else:
            scope_diff = ''
        return '%s%s' % (id.name, scope_diff)
