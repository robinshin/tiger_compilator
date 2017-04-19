from frame.frame import Frame
from ir.nodes import BINOP, CONST, Label, MOVE, TEMP, Temp


class IrvmFrame(Frame):
    """Frame for a function."""

    # Word size for the target architecture.
    word_size = 4

    # Infinite number of parameter registers in IRVM. 128 is close
    # enough to infinity, right?
    param_regs = [Temp("i%d" % i) for i in range(128)]

    # Predefined registers used at many places.
    rv = Temp("rv")
    sp = Temp("sp")
    fp = Temp("fp")

    # List of callee save registers.
    callee_save = []

    # List of caller save registers.
    # caller_save = list(Temp("i%d" % i) for i in range(0, 4))
    caller_save = []

    def __init__(self, label):
        super().__init__(label)
        self.end_label = Label("end")

    def wrap_result(self, sxp):
        super().wrap_result(sxp)
        return MOVE(TEMP(self.rv), sxp)

    def label_name(self, suffix):
        return "L%s" % suffix

    def allocate_frame_size(self):
        """In IRVM, we know the frame size at this stage already since
        we have an infinite number of registers and thus no spills."""
        return [MOVE(TEMP(self.sp),
                     BINOP('+', TEMP(self.sp), CONST(-self.offset)))] \
               if self.offset else []
