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
    
    examinated_blocks = []
    examinated_blocks.append(blocks[0])
    del blocks[0]

    while len(blocks) > 0:
        current_block = examinated_blocks[-1]
        ## JUMP case
        if isinstance(current_block[-1], JUMP):
            current_block_target = current_block[-1].target
            if current_block_target in blocks:
                examinated_blocks.append(current_block_target)
                blocks.remove(current_block_target)
            else:
                examinated_blocks.append(blocks[0])
                del blocks[0]
        ## CJUMP case
        elif isinstance(current_block[-1], CJUMP):
            true_block = current_block[-1].ifTrue
            false_block = current_block[-1].ifFalse
            if is_block_in_list(current_block[-1].ifFalse.label, blocks):
                block_index = find_block_index(current_block[-1].ifFalse.label, blocks)
                examinated_blocks.append(blocks[block_index])
                del blocks[block_index]
            elif is_block_in_list(current_block[-1].ifTrue.label, blocks):
                block_index = find_block_index(current_block[-1].ifTrue.label, blocks)
                temp = current_block[-1].ifTrue
                current_block[-1].ifTrue = current_block[-1].ifFalse
                current_block[-1].ifFalse = temp
                inverse(current_block[-1].op)
                examinated_blocks.append(blocks[block_index])
                del blocks[block_index]
            else:
                new_label = LABEL(Label.create(frame))
                examinated_blocks.append([new_label, JUMP(false_block)])
                current_block[-1].ifFalse = new_label
                examinated_blocks.append(blocks[0])
                del blocks[0]
        ## Last block
        else:
            examinated_blocks.append(blocks[0])
            del blocks[0]

    # Linearisation
    linearized_seq = []
    for index, block in enumerate(examinated_blocks):
        for stm in block:
            if isinstance(examinated_blocks[index-1][-1], JUMP) and examinated_blocks[index-1][-1].target.label == block[0].label:
                del examinated_blocks[index-1][-1]
            linearized_seq.append(stm)
    return SEQ(linearized_seq)

def is_block_in_list(label, block_list):
    for block in block_list:
        if block[0].label == label:
            return True
    return False

def find_block_index(label, block_list):
    for index, block in enumerate(block_list):
        if block[0].label == label:
            return index
    return -1
