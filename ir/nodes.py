# List of logical binary operators.
logical_operators = ['<', '<=', '>', '>=', '=', '<>']


class Label:
    """A label which can be declared in the assembly file (through
    a `LABEL` node) or referenced (through a `NAME` node).

    It is possible to create a new Label instance by calling
    `Label.create()`."""

    def __init__(self, name):
        assert isinstance(name, str), "label name must be a string"
        self.name = name

    _idx = 0

    def create(frame):
        """Return a new local label with a unique name suitable for
        the given frame."""
        try:
            return Label(frame.label_name(str(Label._idx)))
        finally:
            Label._idx += 1

    def __eq__(self, other):
        return isinstance(other, Label) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return self.name

    def __add__(self, subname):
        assert isinstance(subname, str), "subname must be a string"
        return Label("%s$%s" % (self.name, subname))


class Temp:
    """A temporary register, which can be either a physical register
    or a virtual register.

    It is possible to create a new virtual register by calling
    `Temp.create(prefix)`. The `prefix` argument is an optional string
    which may help determine where the register comes from in the output."""

    def __init__(self, name):
        assert isinstance(name, str), "register name must be a string"
        self.name = name

    _idx = 0

    def create(prefix=None):
        """Return a new temporary register with a unique name and
        an optional prefix."""
        assert prefix is None or isinstance(prefix, str), \
            "prefix for register name must be a string or None"
        prefix = "t_%s_" % prefix if prefix else "t_"
        try:
            return Temp("%s%d" % (prefix or "", Temp._idx))
        finally:
            Temp._idx += 1

    def __eq__(self, other):
        return isinstance(other, Temp) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return self.name


class Node:
    """A node in the IR tree."""

    def __init__(self):
        # Kids are sub-expressions
        self.kids = []

    def accept(self, visitor):
        return visitor.visit(self)

    def build(self, kids):
        raise AssertionError("build must be implemented for %s" %
                             self.__class__)


class Sxp(Node):
    """Node class representing an expression returning a value.

    The `side_effect_free` field is True when the evaluation can
    be dropped without affecting the result."""

    def __init__(self):
        super().__init__()
        self.is_side_effect_free = False


class Stm(Node):
    """Node class representing an expression which does not return
    a value (statement).

    The `is_nop` field is True when the statement can be dropped
    without affecting the result."""

    def __init__(self):
        super().__init__()
        self.is_nop = False

    def commutes_with(self, sxp):
        return self.is_nop or sxp.is_side_effect_free


class BINOP(Sxp):
    """Binary operator."""

    def __init__(self, op, left, right):
        super().__init__()
        assert isinstance(op, str), "operator must be a string"
        assert isinstance(left, Sxp), "left argument must be a Sxp"
        assert isinstance(right, Sxp), "right argument must be a Sxp"
        self.op = op
        self.left = left
        self.right = right
        self.kids = [left, right]
        # The binary operator is side effect free when the evaluation
        # of its arguments is side effect free and its computation
        # cannot have side effects. The only possible side effect in
        # our case is a division by zero error, so if we have a
        # division by a non-zero constant we are safe.
        self.is_side_effect_free = \
            left.is_side_effect_free and right.is_side_effect_free and \
            (op != '/' or (isinstance(right, CONST) and right.value != 0))

    def build(self, kids):
        return BINOP(self.op, kids[0], kids[1])


class CALL(Sxp):
    """Function call."""

    def __init__(self, func, args):
        super().__init__()
        assert isinstance(func, Sxp), "func must be a Sxp"
        assert isinstance(args, list), "args must be a list of Sxp"
        assert all(isinstance(arg, Sxp) for arg in args), \
            "args must be a list of Sxp"
        self.func = func
        self.args = args
        self.kids = [func] + args
        # The following variable can be set to False by the translator
        self.return_result = True

    def build(self, kids):
        call = CALL(kids[0], kids[1:])
        call.return_result = self.return_result
        return call


class CJUMP(Stm):
    """Conditional jump."""

    def __init__(self, op, left, right, ifTrue, ifFalse):
        super().__init__()
        assert isinstance(op, str), "operator must be a string"
        assert isinstance(left, Sxp), "left argument must be a Sxp"
        assert isinstance(right, Sxp), "right argument must be a Sxp"
        assert isinstance(ifTrue, Sxp), "ifTrue must be a Sxp"
        assert isinstance(ifFalse, Sxp), "ifFalse must be a Sxp"
        self.op = op
        self.left = left
        self.right = right
        self.ifTrue = ifTrue
        self.ifFalse = ifFalse
        self.kids = [left, right]

    def build(self, kids):
        return CJUMP(self.op, kids[0], kids[1],
                     self.ifTrue, self.ifFalse)


class CONST(Sxp):
    """Integer constant."""

    def __init__(self, value):
        super().__init__()
        assert isinstance(value, int), "value must be an integer"
        self.value = value
        self.is_side_effect_free = True

    def build(self, kids):
        return self


class ESEQ(Sxp):
    """Expression to be evaluated after a sequence of statements."""

    def __init__(self, stm, exp):
        super().__init__()
        assert isinstance(stm, Stm), "stm must be a Stm"
        assert isinstance(exp, Sxp), "exp must be a Sxp"
        self.stm = stm
        self.exp = exp
        self.is_side_effect_free = stm.is_nop and exp.is_side_effect_free
        self.kids = [exp]


class SXP(Stm):
    """Transform an expression into a statement."""

    def __init__(self, exp):
        super().__init__()
        assert isinstance(exp, Sxp), "exp must be a Sxp"
        self.exp = exp
        self.is_nop = exp.is_side_effect_free
        self.kids = [exp]

    def build(self, kids):
        return SXP(kids[0])


class JUMP(Stm):
    """Inconditionnal jump."""

    def __init__(self, target):
        super().__init__()
        assert isinstance(target, Sxp), "target must be a Sxp"
        self.target = target
        self.kids = [target]

    def build(self, kids):
        return JUMP(kids[0])


class LABEL(Stm):
    """Label."""

    def __init__(self, label):
        super().__init__()
        assert isinstance(label, Label), "label must be a Label"
        self.label = label

    def build(self, kids):
        return self


class MEM(Sxp):
    """Memory reference."""

    def __init__(self, exp):
        super().__init__()
        assert isinstance(exp, Sxp), "exp must be a Sxp"
        self.exp = exp
        self.kids = [exp]
        # In an embedded system, we would not set `is_side_effect_free`
        # because a memory access can trigger an action on a peripheral.
        self.is_side_effect_free = exp.is_side_effect_free

    def build(self, kids):
        return MEM(kids[0])


class MOVE(Stm):
    """Assignment."""

    def __init__(self, dst, src):
        super().__init__()
        assert isinstance(dst, Sxp) and \
            (isinstance(dst, MEM) or isinstance(dst, TEMP)), \
            "dst must be a Sxp (MEM or TEMP)"
        assert isinstance(src, Sxp), "src must be a Sxp"
        self.dst = dst
        self.src = src
        self.kids = [dst.exp if isinstance(dst, MEM) else dst, src]

    def build(self, kids):
        return MOVE(MEM(kids[0]) if isinstance(self.dst, MEM)
                    else kids[0],
                    kids[1])


class NAME(Sxp):
    """Named reference."""

    def __init__(self, label):
        super().__init__()
        assert isinstance(label, Label), "label must be a Label"
        self.label = label
        self.is_side_effect_free = True

    def build(self, kids):
        return self


class SEQ(Stm):
    """Sequence of statements to execute in order."""

    def __init__(self, stms):
        super().__init__()
        assert isinstance(stms, list), "stms must be a list of Stm"
        assert all(isinstance(stm, Stm) for stm in stms), \
            "stms must be a list of Stm"
        self.stms = stms
        self.is_nop = all(stm.is_nop for stm in stms)


class TEMP(Sxp):
    """Temporary register (physical or virtual)."""

    def __init__(self, temp):
        super().__init__()
        assert isinstance(temp, Temp), "temp must be a Temp"
        self.temp = temp
        self.is_side_effect_free = True

    def build(self, kids):
        return self
