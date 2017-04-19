from codegen.instr import LABEL as L, MOVE as M

def liveness_analysis(frame, instrs):
    """Annotate instructions with liveness analysis. Return the interferences
    and coalesces dictionaries as a pair.

    The interferences dictionary gives, for every temporary, the list of
    temporaries it conflicts with.

    The coalesces dictionary gives, for every temporary, the list of other
    temporaries involved in a direct MOVE operation. Those are susceptible
    of merging."""
    raise NotImplementedError("liveness analysis")
