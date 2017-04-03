from ir.nodes import *


def flatten(s):
    """If s is a SEQ, flatten all the SEQ directly inside it recursively."""
    if isinstance(s, SEQ):
        result = []
        for ss in s.stms:
            result = result + flatten(ss).stms
        return SEQ(result)
    if s.is_nop:
        return SEQ([])
    return SEQ([s])


def reorder(sxps):
    """Take a list of expressions and return a pair of
    (statement, expressions) with statement being everything that need to
    be done before the expressions. statement is a flattend statement."""
    assert all(isinstance(sxp, Sxp) for sxp in sxps)
    if sxps == []:
        return (SEQ([]), [])
    h = reorder_sxp(sxps[0])
    (tstm, texps) = reorder(sxps[1:])
    if tstm.commutes_with(h.exp):
        return flatten(SEQ([h.stm, tstm])), [h.exp] + texps
    else:
        temp = TEMP(Temp.create("reorder"))
        return flatten(SEQ([h.stm, MOVE(temp, h.exp), tstm])), \
            [temp] + texps


def reorder_sxp(sxp):
    """Return an ESEQ with a reordering of sxp."""
    assert isinstance(sxp, Sxp)
    rs, res = reorder(sxp.kids)
    if isinstance(sxp, ESEQ):
        return ESEQ(flatten(SEQ([reorder_stm(sxp.stm), rs])), res[0])
    return ESEQ(rs, sxp.build(res))


def reorder_stm(stm):
    """Return a Stm with a reordering of stm."""
    assert isinstance(stm, Stm)
    if isinstance(stm, SEQ):
        return flatten(SEQ([reorder_stm(s) for s in stm.stms]))
    if isinstance(stm, MOVE) and isinstance(stm.dst, ESEQ):
        return reorder_stm(SEQ([stm.dst.stm, MOVE(stm.dst.exp, stm.src)]))
    s, exps = reorder(stm.kids)
    return flatten(SEQ([s, stm.build(exps)]))


def canon(node):
    """Return a canonical representation of node."""
    if isinstance(node, Sxp):
        return reorder_sxp(node)
    return reorder_stm(node)
