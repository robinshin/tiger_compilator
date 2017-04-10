from ir.nodes import BINOP, CONST, LABEL, Label, MEM, MOVE, SEQ, Sxp, TEMP, Temp


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

    # List of callee save registers temps. The frame pointer is handled
    # separately.
    callee_save = []

    # List of caller save registers temps.
    caller_save = []

    # List of all physical registers in the CPU, used for register allocation.
    registers = []

    def __init__(self, label):
        assert isinstance(label, Label), "label must be a Label"
        self.label = label
        self.end_label = label + "$end"
        self.restore_label = label + "$restore"
        self.allocate_frame_size_label = label + "$allocateFrameSize"
        self.returns_value = False
        self.offset = 0
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
        self.offset += self.word_size
        return -self.offset

    def wrap_result(self, sxp):
        """Return a Stm which takes the result of the `sxp` parameter and
        stores it into the appropriate register. Also, remember that the
        function returns a value."""
        self.returns_value = True
        # The child must override this method and call super()

    def preserve_callee_save(self):
        """Save all the callee save registers and return
        a list of move instructions to save them and a list
        of move instructions to restore them."""
        callee_save_map = dict((reg, Temp.create("callee_save"))
                               for reg in self.callee_save)
        save_callee_save = [MOVE(TEMP(callee_save_map[reg]), TEMP(reg))
                            for reg in self.callee_save]
        restore_callee_save = [MOVE(TEMP(reg), TEMP(callee_save_map[reg]))
                               for reg in reversed(self.callee_save)]
        return save_callee_save, restore_callee_save

    def transfer_parameters(self):
        """Return a list of move instructions to transfer the parameters
        from registers or call stack into the register or the frame
        position they belong to (according to their Access parameter).
        The first parameter in which the static link has been passed
        must be handled separately."""
        return \
            [MOVE(access.toSxp(TEMP(self.fp)),
                  TEMP(self.param_regs[idx + 1])
                  if idx < self.max_params_in_regs - 1
                  else InFrame((idx - self.max_params_in_regs + 1) *
                               self.word_size).toSxp(TEMP(self.fp)))
             for (idx, access) in enumerate(self.param_access)]

    def prologue(self):
        """Return the function prologue and some opaque value
        which will be passed to the epilogue. It can be used to
        pass a register map to be restored from the epilogue for
        example.

        In this generic method, we will pass around a list of
        move instructions needed to restore the callee-save
        registers and the frame pointer.

        It is expected that specific frames will generate more
        specialized prologues, using dedicated instructions
        such as push and pop that cannot be easily represented
        using the IR."""

        begin_label = LABEL(self.label)

        # Push the previous frame pointer and the static link to the stack
        # and setup the new frame pointer.
        save_fp = [MOVE(TEMP(self.sp),
                        BINOP("+", TEMP(self.sp), CONST(-self.word_size))),
                   MOVE(MEM(TEMP(self.sp)),
                        TEMP(self.fp)),
                   MOVE(TEMP(self.sp),
                       BINOP("+", TEMP(self.sp), CONST(-self.word_size))),
                    MOVE(MEM(TEMP(self.sp)),
                        TEMP(self.param_regs[0])),
                    MOVE(TEMP(self.fp), TEMP(self.fp))]
        restore_fp = [MOVE(TEMP(self.sp),
                           BINOP("+", TEMP(self.fp), CONST(self.word_size))),
                      MOVE(TEMP(self.fp), MEM(TEMP(self.sp))),
                      MOVE(TEMP(self.sp),
                           BINOP("+", TEMP(self.sp), CONST(self.word_size)))]

        # Code to save and restore the callee-save registers.
        save_callee_save, restore_callee_save = self.preserve_callee_save()

        # Code to transfer the parameters from registers or call stack into the
        # register or the frame position they belong to (according to their
        # Access parameter). The first parameter (r0, in which the static link
        # had been written) has already been handled above.
        store_parameters = self.transfer_parameters()

        return [begin_label] + save_fp + save_callee_save + \
               store_parameters, restore_callee_save + restore_fp

    def epilogue(self, data):
        """Return the function epilogue with data passed from the prologue."""
        restore_label, end_label = LABEL(self.restore_label), LABEL(self.end_label)
        return [restore_label] + data + [end_label]

    def decorate(self, stm):
        """Decorate the `stm` with code which sets up the frame, the stack
        pointer, the registers holding the parameters, the preservation of
        the callee saved registers, and the end label."""
        prologue, data = self.prologue()
        return SEQ(prologue + [stm] + self.epilogue(data))

    def one_frame_up(self, current_fp):
        """Return the frame pointer one frame above this one. fp is an Sxp
        with the current frame pointer, return value is a MEM expression
        with the frame pointer one level up."""
        assert isinstance(current_fp, Sxp), "fp must be an expression"
        return MEM(current_fp)

    def load_spill(self, temp, offset):
        """Return a list of instructions (wrapped in Instr instances) that
        take care of loading the content of the given offset relative to
        the frame pointer into the temporary."""
        raise AssertionError("unimplemented")

    def save_spill(self, temp, offset):
        """Return a list of instructions (wrapped in Instr instances) that
        take care of saving the given temporary into the content of the
        offset relative to the frame pointer."""
        raise AssertionError("unimplemented")

    def reserve_stack_space(self):
        """Return a list of instructions (wrapped in Instr instances) to
        reserve the stack space needed for the static link and the spills.
        This will replace the self.allocate_frame_size_label LABEL
        declaration at a late stage when all the spills have been determined."""
        raise AssertionError("unimplemented")
