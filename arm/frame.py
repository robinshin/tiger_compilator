from frame.frame import Frame
from ir.nodes import LABEL, MOVE, TEMP, Temp


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

    # List of callee save registers (the frame pointer is handled separately).
    callee_save = list(Temp("r%d" % i) for i in range(4, 11))

    # List of caller save registers.
    caller_save = list(Temp("r%d" % i) for i in range(4)) + [lr]

    def __init__(self, label):
        super().__init__(label)

    def wrap_result(self, sxp):
        super().wrap_result(sxp)
        return MOVE(TEMP(self.r0), sxp)

    def prologue(self):
        save_callee_save, restore_callee_save = self.preserve_callee_save()
        store_parameters = self.transfer_parameters()
        # The fp save and static link will be saved while generating the code
        # with ARM specific instructions.
        return [LABEL(self.label)] + self.allocate_frame_size() + \
               save_callee_save + store_parameters, \
               restore_callee_save

    def epilogue(self, data):
        return [LABEL(self.restore_label)] + data + [LABEL(self.end_label)]
