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
        if decl.type == None:
            return "var %s" % decl.name + ("/*e*/" if decl.escapes else "") + " := %s" % decl.exp.accept(self)
        else:
            return "var %s" % decl.name + ("/*e*/" if decl.escapes else "") + ": %s := %s" % (decl.type.typename, decl.exp.accept(self))

    @visitor(FunDecl)
    def visit(self, func):
        args = ''
        size = len(func.args)
        i = 1
        if size != 0:
            for arg in func.args:
                args += "%s: %s" % (arg.name, arg.type.typename) + (", " if i != size else "")
                i += 1

        if func.type == None:
            return "function %s(%s) = %s" % (func.name, args, func.exp.accept(self))
        else:
            return "function %s(%s): %s = %s" % (func.name, args, func.type.typename, func.exp.accept(self))

    @visitor(Let)
    def visit(self, let):
        decls = ''
        expr = ''
        size = len(let.decls)
        for decl in let.decls:
            decls += decl.accept(self) + ('\n' if size != 1 else '')
        for exp in let.exps:
            expr += exp.accept(self)
        return "let %s in %s end" % (decls, expr) if size == 1 else "let\n%sin\n%s\nend" %(decls, expr)

    @visitor(Identifier)
    def visit(self, id):
        if self.semantics:
            diff = id.depth - id.decl.depth
            scope_diff = "/*%d*/" % diff if diff else ''
        else:
            scope_diff = ''
        return '%s%s' % (id.name, scope_diff)

    @visitor(FunCall)
    def visit(self, func):
        params = ''
        size = len(func.params)
        i = 1
        if size != 0:
            for param in func.params:
                params += param.accept(self) + (", " if i != size else "")
                i = i + 1
        return "%s(%s)" % (func.identifier.name, params)
