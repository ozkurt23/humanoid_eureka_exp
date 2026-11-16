from catch import Catch
from plant import Reflex as Plant
from shortstep import ShortStep
from sidestep import RecoverySteps
from blindbalance import Balance
import numpy as np


class SideStep(RecoverySteps):
    def update(self, t, m, d):
        if not self.pulse and abs(self.val) < 1.0:
            return Balance.update(self, t, m, d)
        if not self.pulse:
            self.t0 = t
        refs = super().update(t, m, d)
        self.holding = self.pulse
        return refs


def select(controller, candidate):
    if not hasattr(controller, "restwidth"):
        controller.restwidth = controller.base[1, 0] - controller.base[0, 0]
    if not hasattr(controller, "pending"):
        controller.pending = np.zeros(2)
    controller.holding = False
    if 20 <= candidate < 24:
        controller.__class__ = SideStep
        controller.pulse = False
        controller.config = {}
    elif candidate >= 41:
        controller.__class__ = ShortStep
        controller.mode = None
        controller.committed = False
    elif 24 <= candidate < 27:
        controller.__class__ = Plant
        controller.mode = None
    else:
        controller.__class__ = Catch
