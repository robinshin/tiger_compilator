from frame.frame import Frame
from ir.nodes import MOVE, TEMP, Temp


class ArmFrame(Frame):
    """Frame for an ARM function."""

    # Word size for the target architecture.
    word_size = 4

    param_regs = [Temp("r0"), Temp("r1"), Temp("r2"), Temp("r3")]

    # Predefined registers used at many places.
    r0 = Temp("r0")
    lr = Temp("lr")
    sp = Temp("sp")
    fp = Temp("r11")

    # List of callee save registers.

    callee_save = list(Temp("r%d" % i) for i in range(4, 11))

    # List of caller save registers.
    caller_save = list(Temp("r%d" % i) for i in range(0, 4))

    def __init__(self, label):
        super().__init__(label)

    def wrap_result(self, sxp):
        super().wrap_result(sxp)
        return MOVE(TEMP(self.r0), sxp)
