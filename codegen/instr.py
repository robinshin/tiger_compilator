from ir.nodes import Label, Temp

class Instr:
    """A class of assembler instructions."""

    def __init__(self, template):
        """The template argument will be given a list with
        all the defs followed by all the uses. Register names
        must be templated as they may be replaced later on."""
        self.template = template

    def defs(self):
        return []

    def uses(self):
        return []

    def jumps(self):
        return []

    def __str__(self):
        indent = 0 if isinstance(self, LABEL) else 8
        return " " * indent + self.template.format(*(self.defs() + self.uses()))


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

    def __init__(self, template, label):
        assert isinstance(label, Label)
        super().__init__(template)
        self.label = label
