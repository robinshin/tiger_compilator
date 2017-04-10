from codegen.liveness import liveness_analysis
from codegen.instr import LABEL as L, MOVE as M, OPER as O
from ir.nodes import Temp

class Spill(Exception):

    def __init__(self, temp):
        super().__init__("Temporary {} requires spilling".format(temp))
        self.temp = temp

def colorize(frame, instrs):
    """Return a map of registers allocation or fail with a Spill exception if
    a color cannot be allocated for a register."""
    interferences, coalesces = liveness_analysis(frame, instrs)
    # List of mappings after register allocation or coalescing
    remapped = {}
    # Number of registers
    k = len(frame.registers)
    # Stack of registers to later color when unstacking
    stack = []
    # Temporaries not stacked yet
    temporaries = set(interferences.keys()).difference(frame.registers)

    def canon(reg):
        """Find the canonical representation of a register in the remapping table.
        Mappings are updated to the final destination while the call chain gets rewound."""
        target = remapped.get(reg)
        if target:
            final = canon(target)
            if final != target:
                remapped[reg] = final
            return final
        return reg

    def mark_coalesced(a, b):
        """Coalesce a and b. Physical registers are always selected as the target. If one of them
        is a physical register, it will always be the target of the remapping. The interferences
        entry for a will be merged into the one of b then removed, same for the coalesces entries.
        Also, a will be removed from the temporaries as it has been taken care of."""
        a, b = canon(a), canon(b)
        if a in frame.registers:
            assert b not in frame.registers, "cannot coalesce physical registers {} and {}".format(a, b)
            a, b = b, a
        remapped[a] = b
        raise NotImplementedError("marking registers as coalesced")

    def push_to_stack(t):
        """Push a temporary and its interferences to the stack, and clear its
        interferences in the live tree. Also remove it from the temporaries list.
        Pushing the interferences of the temporary along with it allows to easily
        determine an available color when unstacking."""
        raise NotImplementedError("push to stack")

    def simplify():
        """Push one temporary of insignificant degree not involved in a MOVE operation
        to the stack and return it. It gets removed from the temporaries list. If none is
        found, return None."""
        raise NotImplementedError("simplify")

    def coalesce():
        """Coalesce two temporaries involved in a MOVE operation so that they do not
        prevent the new node from being simplified. Return the pair that has been coalesced
        or None otherwise."""
        raise NotImplementedError("coalesce")

    def spill_candidate():
        """Find a spill candidate with the best score. We do not take loops into account."""
        raise NotImplementedError("spill candidate")

    def unstack():
        """Pop and color temporaries from the stack. If a temporary cannot
        get a color that none of his neighbour has, we need to spill it. A Spill
        exception will be raised to indicate that spilling needs to occur and
        the whole process must be started again. The parameter of the exception
        will indicate the register that needs spilling"""
        raise NotImplementedError("unstack")

    def apply_mappings():
        """Apply register mappings and return a list of instructions with
        only physical registers. Redundant move operations and non-jumped-to
        labels will be removed to. The stack size for the function is now
        known and the appropriate label will be replaced by a stack
        allocation. The cleaned up list of instructions will be returned."""
        raise NotImplementedError("apply mappings")

    while temporaries:
        simplified_or_coalesced = False

        # Simplify as much as possible
        while True:
            n = simplify()
            if n:
                simplified_or_coalesced = True
            else:
                break

        # Coalesce as much as possible
        while True:
            p = coalesce()
            if p:
                simplified_or_coalesced = True
            else:
                break

        # We went a full round without simplification or coalescing.
        # If possible, we will break a coalescing bound, otherwise,
        # we will have to spill a potential candidate. Hopefully,
        # when unstacking, several neighbours will have the same color
        # and we will not have to really spill it.
        if not simplified_or_coalesced:
            candidates = temporaries.intersection(coalesces.keys())
            if candidates:
                weights = dict((node, len(interferences[node])) for node in candidates)
                to_remove = min(weights.keys(), key=lambda n: weights[n])
                for n in coalesces[to_remove]:
                    coalesces[n].remove(to_remove)
                del coalesces[to_remove]
            else:
                potential_spill = spill_candidate()
                push_to_stack(potential_spill)

    # Unstack and color the temporaries with physical registers.
    unstack()

    # So far so good, apply mappings and return.
    return apply_mappings()

def allocate_registers(frame, instrs):
    """Allocate registers for the given instructions. If we get a
    Spill exception from colorize, we need to spill the given
    temporary and start over."""
    while True:
        try:
            return colorize(frame, instrs)
        except Spill as spill_exception:
            instrs = spill_temporary(frame, instrs, spill_exception.temp)

def spill_temporary(frame, instrs, spill):
    """Spill a temporary, reload it before every use through a new temporary,
    save it after every def through a new temporary. Those temporary will
    replace the spilled temporary in the original instructions, so that
    the new lifetimes are kept very short."""
    # Allocate a new spill space in the frame
    saved_offset = frame.alloc_spill()
    raise NotImplementedError("spill temporary for {}".format(spill))
