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
                blocks[-1].append(JUMP(NAME(stm.label)))
            blocks.append([stm])
        else:
            blocks[-1].append(stm)
        previous_stm = stm

    examinated_blocks = blocks[0]
    del blocks[0]
    while len(blocks) > 0:
        current_block = examinated_blocks[-1]
        ## JUMP case
        if isinstance(current_block, JUMP):
            current_block_target = current_block.target
            if current_block_target in blocks:
                examinated_blocks.append(current_block_target)
                blocks.remove(current_block_target)
            else:
                examinated_blocks.append(blocks[0])
                del blocks[0]
        ## CJUMP case
        elif isinstance(current_block, CJUMP):
            true_block = current_block.ifTrue
            false_block = current_block.ifFalse
            if false_block in blocks:
                examinated_blocks.append(false_block)
                blocks.remove(false_block)
            elif true_block in blocks:
                inverse(current_block.op)             
                current_block.ifTrue = false_block
                current_block.ifFalse = true_block
                examinated_blocks.append(true_block)
                blocks.remove(true_block)
            else:
                new_label = LABEL(Label.create(frame))
                examinated_blocks.append([new_label, JUMP(false_block)])
                current_block_type.ifFalse = new_label
                examinated_blocks.append(blocks[0])
                del blocks[0]
        ## Last block
        else:
            examinated_blocks.append(blocks[0])
            del blocks[0]

    return seq
