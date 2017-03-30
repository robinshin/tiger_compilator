from ir.nodes import *
from frame.frame import Frame


def reorder_blocks(seq, frame):
    """Reorder blocks in seq so that the negative branch of a CJUMP always
    follows the CJUMP itself. frame is the frame of the corresponding
    function."""
    assert(isinstance(seq, SEQ))
    assert(isinstance(frame, Frame))
    
    blocks = []
    previous_stm = None
    for stm in seq.stms:
        if isinstance(stm, LABEL):
            if previous_stm and not isinstance(previous_stm, JUMP) and not isinstance(previous_stm, CJUMP):
                blocks[-1].append(JUMP(stm))
            blocks.append([stm])
        else:
            blocks[-1].append(stm)
        previous_stm = stm


    return seq
