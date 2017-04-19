from ir.nodes import Label, Temp

class Instr:
    """A class of assembler instructions."""

    def __init__(self, template):
        """The template argument will be given a list with
        all the defs followed by all the uses. Register names
        must be templated as they may be replaced later on."""
        self.template = template
        self.live_in = set()
        self.live_out = set()
        # The extra_conflicts field may be used to record
        # that some instruction operands may not be in some
        # registers, or in identical parameters. It will be
        # used by liveness analysis. It is represented as
        # a list of pairs.
        self.extra_conflicts = []

    def defs(self):
        """Return Temp instances defined by this instruction."""
        return []

    def uses(self):
        """Return Temp instances read by this instruction."""
        return []

    def jumps(self):
        """Return jump targets from this instruction. If empty,
        it means that this instruction jumps to the next one."""
        return []

    def replace_with(self, old_temp, new_temp):
        """Replace a temporary with another, for example when spilling
        occurs."""
        assert isinstance(old_temp, Temp), "old_temp must be a Temp"
        assert isinstance(new_temp, Temp), "new_temp must be a Temp"
        self.extra_conflicts = [(new_temp, b) if a == old_temp
                                else (a, new_temp) if b == old_temp
                                else (a, b) for (a, b) in self.extra_conflicts
                               ]

    def record_conflict(self, a, b):
        """Record a conflict between temporaries used in this instruction.
        For example, in the ARM instruction set, the mul instruction cannot
        use the same physical register as Rd and Rm."""
        assert isinstance(a, Temp), "a must be a Temp"
        assert isinstance(b, Temp), "a must be a Temp"
        self.extra_conflicts.append((a, b))
        # Return self allows us to use this method in chain mode
        return self

    def __str__(self):
        indent = 0 if isinstance(self, LABEL) else 8
        return " " * indent + self.template.format(*(self.defs() + self.uses()))

    def dump(self, verbose):
        """Dump instruction with all relevant information."""
        if verbose:
            defs = ["defs: {}".format(self.defs())] if self.defs() else []
            uses = ["uses: {}".format(self.uses())] if self.uses() else []
            live_in = ["live in: {}".format(sorted(list(self.live_in), key=lambda t: t.name))] \
                      if self.live_in else []
            live_out = ["live out: {}".format(sorted(list(self.live_out), key=lambda t: t.name))] \
                       if self.live_out else []
            jumps = ["jumps: {}".format(self.jumps())] if self.jumps() else []
            conflicts = ["extra conflicts: {}".format(self.extra_conflicts)] \
                        if self.extra_conflicts else []
            comments = ", ".join(defs + uses + live_in + live_out + jumps + conflicts)
            if comments:
                comments = " ; {}".format(comments)
        else:
            comments = ""
        return "{!s:40}{}".format(self, comments)

class OPER(Instr):
    """A regular instruction which is neither a direct transfer
    between registers or a label."""

    def __init__(self, template, dsts = [], srcs = [], jmps = []):
        assert all(isinstance(jmp, Label) for jmp in jmps)
        assert all(isinstance(o, Temp) for o in dsts + srcs)
        super().__init__(template)
        self.dsts = dsts
        self.srcs = srcs
        self.jmps = jmps

    def defs(self):
        return self.dsts

    def uses(self):
        return self.srcs

    def jumps(self):
        return self.jmps

    def replace_with(self, old_temp, new_temp):
        super().replace_with(old_temp, new_temp)
        self.dsts = [new_temp if t == old_temp else t for t in self.dsts]
        self.srcs = [new_temp if t == old_temp else t for t in self.srcs]


class MOVE(Instr):
    """A direct transfer instruction between registers."""

    def __init__(self, template, dst, src):
        assert isinstance(dst, Temp)
        assert isinstance(src, Temp)
        super().__init__(template)
        self.dst = dst
        self.src = src

    def defs(self):
        return [self.dst]

    def uses(self):
        return [self.src]

    def replace_with(self, old_temp, new_temp):
        super().replace_with(old_temp, new_temp)
        if self.src == old_temp:
            self.src = new_temp
        if self.dst == old_temp:
            self.dst = new_temp

class LABEL(Instr):
    """A label definition."""

    def __init__(self, template, label, updates = []):
        assert isinstance(label, Label)
        assert all(isinstance(u, Temp) for u in updates)
        super().__init__(template)
        self.label = label
        self.updates = updates

    def defs(self):
        return self.updates

    def uses(self):
        return self.updates

    def replace_with(self, old_temp, new_temp):
        super().replace_with(old_temp, new_temp)
        self.updates = [new_temp if t == old_temp else t for t in self.updates]
