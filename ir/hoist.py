from ir.nodes import *
from utils.visitor import *


class HoistCalls(Visitor):

    # Transform every expression representing a CALL node returning a value
    # into an ESEQ returning a simple temporary (after copying the result
    # of the call to this temporary).

    @visitor(None)
    def visit(self, node):
        return node.build([child.accept(self) for child in node.kids])

    @visitor(CALL)
    def visit(self, call):
        hoisted = call.build(self.visit_all(call.kids))
        if hoisted.return_result:
            temp = TEMP(Temp.create("call"))
            return ESEQ(MOVE(temp, call.build(self.visit_all(call.kids))),
                        temp)
        return hoisted

    @visitor(SEQ)
    def visit(self, seq):
        return SEQ([stm.accept(self) for stm in seq.stms])

    @visitor(ESEQ)
    def visit(self, eseq):
        return ESEQ(eseq.stm.accept(self), eseq.exp.accept(self))
