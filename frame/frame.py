from ir.nodes import BINOP, CONST, LABEL, Label, MEM, MOVE, SEQ, TEMP, Temp


class Access:
    """Represent an access to a parameter or variable.

    The `toSxp` method takes a Sxp representing the frame pointer of
    the frame where the parameter or variable is located and returns
    a new Sxp representing this parameter or variable."""
    pass


class InRegister(Access):
    """Represent an access to a parameter or variable in a register."""

    def __init__(self, prefix=None):
        self.temp = TEMP(Temp.create(prefix))

    def toSxp(self, fp):
        return self.temp


class InFrame(Access):
    """Represent an access to a parameter within a frame."""

    def __init__(self, offset):
        self.offset = offset

    def toSxp(self, fp):
        return MEM(BINOP('+', fp, CONST(self.offset)))


class Frame:
    """Frame for a given architecture, to be overloaded by child classes."""

    # Word size for the target architecture.
    word_size = -1

    # List of register temps parameters are passed into.
    param_regs = []

    # Stack pointer register (Temp)
    sp = None

    # Frame pointer register (Temp)
    fp = None

    # List of callee save registers temps.
    callee_save = []

    # List of caller save registers temps.
    caller_save = []

    def __init__(self, label):
        assert isinstance(label, Label), "label must be a Label"
        self.label = label
        self.end_label = label + "$end"
        self.restore_label = label + "$restore"
        self.allocate_frame_size_label = label + "$allocateFrameSize"
        self.returns_value = False
        self.offset = self.word_size   # We will at least save the static link
        self.offsets = {}
        self.param_access = []
        self.max_params_in_regs = len(self.param_regs)

    def label_name(self, suffix):
        """Return the name suitable for a temporary label with the given
        suffix."""
        return ".L%s" % suffix

    def alloc_parameter(self, escapes):
        """Returns an `Access` representing this parameter."""
        a = self.alloc(escapes)
        self.param_access.append(a)
        return a

    def alloc(self, escapes, temp_prefix=None):
        """Allocate a new `Access`."""
        return InFrame(self.alloc_spill()) if escapes \
            else InRegister(temp_prefix)

    def alloc_spill(self):
        """Return the offset of a new variable or parameter stored in the
        frame. The offset is relative to the frame pointer."""
        try:
            return -self.offset
        finally:
            self.offset += self.word_size

    def wrap_result(self, sxp):
        """Return a Stm which takes the result of the `sxp` parameter and
        stores it into the appropriate register. Also, remember that the
        function returns a value."""
        self.returns_value = True
        # The child must override this method and call super()

    def allocate_frame_size(self):
        """Return a Stm to allocate the frame size."""
        return LABEL(self.allocate_frame_size_label)

    def decorate(self, stm):
        """Decorate the `stm` with code which sets up the frame, the stack
        pointer, the registers holding the parameters, the preservation of
        the callee saved registers, and the end label."""

        # Begin, restore, and end label creation
        begin_label = [LABEL(self.label)]
        restore_label = [LABEL(self.restore_label)]
        end_label = [LABEL(self.end_label)]

        # Code to save and restore the previous frame pointer and set-it up
        # wrt the stack pointer. Also, a label is put at the place where the
        # frame size will be allocated later (we will only know this
        # information once all the code has been generated and physical
        # registers have been allocated).
        saved_fp = Temp.create("savedfp")
        save_fp = [MOVE(TEMP(saved_fp), TEMP(self.fp)),
                   MOVE(TEMP(self.fp), TEMP(self.sp)),
                   self.allocate_frame_size()]
        restore_fp = [MOVE(TEMP(self.sp), TEMP(self.fp)),
                      MOVE(TEMP(self.fp), TEMP(saved_fp))]

        # Code to save the static link register into the frame at offset 0.
        save_static_link = [MOVE(MEM(TEMP(self.fp)), TEMP(self.param_regs[0]))]

        # Code to save and restore the callee-save registers.
        callee_save_map = dict((reg, Temp.create("callee_save"))
                               for reg in self.callee_save)
        save_callee_save = [MOVE(TEMP(callee_save_map[reg]), TEMP(reg))
                            for reg in self.callee_save]
        restore_callee_save = [MOVE(TEMP(reg), TEMP(callee_save_map[reg]))
                               for reg in reversed(self.callee_save)]

        # Code to transfer the parameters from registers or call stack into the
        # register or the frame position they belong to (according to their
        # Access parameter). The first parameter (r0, in which the static link
        # had been written) has already been handled above.
        store_parameters = \
            [MOVE(access.toSxp(TEMP(self.fp)),
                  TEMP(self.param_regs[idx + 1])
                  if idx < self.max_params_in_regs - 1
                  else InFrame((idx - self.max_params_in_regs + 1) *
                               self.word_size).toSxp(TEMP(self.fp)))
             for (idx, access) in enumerate(self.param_access)]

        return SEQ(begin_label +
                   save_fp + save_static_link + save_callee_save +
                   store_parameters + [stm] +
                   restore_label + restore_callee_save +
                   restore_fp + end_label)
