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
            comments = ", ".join(defs + uses + live_in + live_out + jumps)
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
