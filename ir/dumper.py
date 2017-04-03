from ir.nodes import *
from utils.visitor import *


class Dumper(Visitor):

    def __init__(self):
        self.indent_level = 0

    def pr(self, cmd, *args):
        if len(args) == 1 and isinstance(args[0], list):
            args = args[0]
        sargs = [arg.accept(self) if isinstance(arg, Node) else str(arg)
                 for arg in args]
        if any(" " in s for s in sargs):
            return "\n  ".join([cmd] +
                               [s for sa in sargs for s in sa.split("\n")])
        return " ".join([cmd] + sargs)

    @visitor(None)
    def visit(self, node):
        return self.pr(str(node))

    @visitor(LABEL)
    def visit(self, label):
        return self.pr("label", label.label)

    @visitor(TEMP)
    def visit(self, temp):
        return self.pr("temp", temp.temp)

    @visitor(MOVE)
    def visit(self, move):
        return self.pr("move", move.dst, move.src)

    @visitor(CONST)
    def visit(self, const):
        return self.pr("const", const.value)

    @visitor(MEM)
    def visit(self, mem):
        return self.pr("mem", mem.exp)

    @visitor(SEQ)
    def visit(self, seq):
        return self.pr("seq", seq.stms) + "\n" + self.pr("seq end")

    @visitor(ESEQ)
    def visit(self, eseq):
        return self.pr("eseq", [eseq.stm, eseq.exp])

    @visitor(JUMP)
    def visit(self, jump):
        return self.pr("jump", jump.target)

    @visitor(CJUMP)
    def visit(self, cj):
        return self.pr("cjump (%s)" % cj.op,
                       [cj.left, cj.right, cj.ifTrue, cj.ifFalse])

    @visitor(BINOP)
    def visit(self, binop):
        return self.pr("binop (%s)" % binop.op,
                       [binop.left, binop.right])

    @visitor(SXP)
    def visit(self, exp):
        return self.pr("sxp", exp.exp)

    @visitor(NAME)
    def visit(self, name):
        return self.pr("name", name.label)

    @visitor(CALL)
    def visit(self, call):
        return self.pr("call", [call.func] + call.args) + "\n" + \
            self.pr("call end")
