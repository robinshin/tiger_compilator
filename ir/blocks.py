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
    while len(blocks) != 0:
        current_block_type = examinated_blocks[-1]
        if isinstance(current_block_type, JUMP):
            current_block = current_block_type.target
            if current_block in blocks:
                examinated_blocks.append(current_block)
                blocks.remove(current_block)
            else:
                examinated_blocks.append(blocks[0])
                del blocks[0]
        elif isinstance(current_block_type, CJUMP):
            true_block = current_block_type.ifTrue
            false_block = current_block_type.ifFalse
            if false_block in blocks:
                examinated_blocs.append(false_block)
                blocks.remove(false_block)
            elif true_block in blocks:
                right_tmp = current_block_type.right
                current_block_type.right = current_block_type.left
                current_block_type.left = right_tmp
                current_block_type.ifTrue = false_block
                current_block_type.ifFalse = true_block
                examinated_blocks.append(true_block)
                blocks.remove(true_block)
            else:
                examinated_blocks.append([Label("new_label"), JUMP(NAME(false_block.label))])
                current_block_type.ifFalse.label = Label("new_label")


    return seq
