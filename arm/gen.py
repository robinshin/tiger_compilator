from codegen.instr import LABEL as L, MOVE as M, OPER as O
from ir.nodes import *
from utils.visitor import *

class Gen:
    """This traverses a tree to generate instructions for a given function.

    This visitor is particular in that it returns different types for Stm
    and Sxp nodes:

        - Stm nodes return a list of Instr.
        - Sxp nodes return a pair with a list of Instr and a temporary
        containing the result.

    This way, we can define only one visitor for both kind of constructs."""

    def __init__(self, frame):
        self.frame = frame

    # Visitors are mandatory

    @visitor(None)
    def visit(self, node):
        raise AssertionError("no code generator for node {}".format(type(node)))

    # Visitors for Stm nodes

    @visitor(SEQ)
    def visit(self, seq):
        return [i for stm in seq.stms for i in stm.accept(self)]

    @visitor(JUMP)
    def visit(self, jmp):
        return [O("jmp {}".format(jmp.target.label.name), [], [], [jmp.target.label])]

    @visitor(CJUMP)
    def visit(self, cjump):
        left_stms, left_temp = cjump.left.accept(self)
        right_stms, right_temp = cjump.right.accept(self)
        if cjump.op == "=":
            op = "beq"
        elif cjump.op == "<>":
            op = "bne"
        else:
            raise AssertionError("unimplemented operator {}".format(op))
        return left_stms + right_stms + [O("cmp {}, {}", srcs=[left_temp, right_temp]),
                                         O("{} {}".format(op, cjump.ifTrue.label.name),
                                           jmps=[cjump.ifTrue.label, cjump.ifFalse.label])]

    @visitor(LABEL)
    def visit(self, label):
        l = L("{}:".format(label.label), label.label)
        if label.label == self.frame.end_label:
            # The end label marks the place of the return instruction
            srcs = [self.frame.lr]
            if self.frame.returns_value:
                srcs.append(self.frame.r0)
            return [l, O("bx {}", srcs=srcs)]
        else:
            return [l]

    @visitor(MOVE)
    def visit(self, move):
        src_stms, src_temp = move.src.accept(self)
        if isinstance(move.dst, MEM):
            # If we try to move into memory, use a store
            dst_stms, dst_temp = move.dst.exp.accept(self)
            return src_stms + dst_stms + [O("str {1}, [{0}]", srcs=[src_temp, dst_temp])]
        else:
            # The only other possibility is a temporary, this is a move instruction
            return src_stms + [M("mov {}, {}", dst=move.dst.temp, src=src_temp)]

    @visitor(SXP)
    def visit(self, sxp):
        return sxp.exp.accept(self)[0]

    # Visitors for Sxp nodes

    @visitor(TEMP)
    def visit(self, temp):
        # Already in a temporary
        return [], temp.temp

    @visitor(CONST)
    def visit(self, const):
        temp = Temp.create("const")
        return [O("mov {{}}, #{}".format(const.value), dsts=[temp])], temp
