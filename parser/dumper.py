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

    @visitor(Let)
    def visit(self, let):
        decls = ''
        expr = ''
        length_decls = len(let.decls)
        length_exps = len(let.exps)
        i = 1
        for decl in let.decls:
            decls += decl.accept(self) + ('\n' if length_decls != 1 else '')
        for exp in let.exps:
            expr += exp.accept(self) + ("; " if i != length_exps else "")
            i += 1
        return "let %s in %s end" % (decls, expr) if length_decls == 1 else "let\n%sin\n%s\nend" %(decls, expr)

    @visitor(Identifier)
    def visit(self, id):
        if self.semantics:
            diff = id.depth - id.decl.depth
            scope_diff = "/*%d*/" % diff if diff else ''
        else:
            scope_diff = ''
        return '%s%s' % (id.name, scope_diff)

    @visitor(IfThenElse)
    def visit(self, ifthenelse):
        return "if %s then %s" % (ifthenelse.condition.accept(self), ifthenelse.then_part.accept(self)) + (" else %s" % ifthenelse.else_part.accept(self) if (ifthenelse.else_part is not None) else "")

    @visitor(VarDecl)
    def visit(self, decl):
        if decl.type == None:
            return "var %s" % decl.name + ("/*e*/" if decl.escapes and self.semantics else "") + " := %s" % decl.exp.accept(self)
        else:
            return "var %s" % decl.name + ("/*e*/" if decl.escapes and self.semantics else "") + ": %s := %s" % (decl.type.typename, decl.exp.accept(self))

    @visitor(FunDecl)
    def visit(self, func):
        args = ''
        length = len(func.args)
        i = 1
        if length != 0:
            for arg in func.args:
                args += "%s: %s" % (arg.name, arg.type.typename) + (", " if i != length else "")
                i += 1

        if func.type == None or func.type.typename == "void":
            return "function %s(%s) = %s" % (func.name, args, func.exp.accept(self))
        else:
            return "function %s(%s): %s = %s" % (func.name, args, func.type.typename, func.exp.accept(self))

    @visitor(FunCall)
    def visit(self, func):
        params = ''
        length = len(func.params)
        i = 1
        if length != 0:
            for param in func.params:
                params += param.accept(self) + (", " if i != length else "")
                i = i + 1
        return "%s(%s)" % (func.identifier.name, params)

    @visitor(SeqExp)
    def visit(self, exprs):
        length = len(exprs.exps)
        exps = ''
        i = 1
        for expr in exprs.exps:
            exps += "%s" % expr.accept(self) + ("; " if i != length else "")
            i += 1
        return ("(" if length != 1 else "") + "%s" % exps + (")" if length != 1 else "")

    @visitor(While)
    def visit(self, whi):
        return "while %s do %s" % (whi.condition.accept(self), whi.exp.accept(self))

    @visitor(For)
    def visit(self, fo):
        return "for %s := %s to %s do %s" % (fo.indexdecl.name, fo.low_bound.accept(self), fo.high_bound.accept(self), fo.exp.accept(self))

    @visitor(Break)
    def visit(self, bre):
        return "break"

    @visitor(Assignment)
    def visit(self, ass):
        return "%s := %s" % (ass.identifier.accept(self), ass.exp.accept(self))
