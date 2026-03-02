"""A collection of all commands that Lynn can use to interact with the game."""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up

# Cooldowns for SkillRotation (Key attribute name -> sec). 0 = no cooldown (spam).
# Uses Key attribute names so user rebinds are respected.
SKILL_COOLDOWNS = {
    'STRIKE': 0,
    'EARTH_PULVERIZATION': 30,
    'SWEEP': 10,
    'RAID': 30,
    'BEASTS_RAGE': 120,
    'AWAKE': 120,
    'ROAR': 30,
    'WHIRLWIND': 15,
    'PREDATORS_BLOW': 30,
    'LYNN_BUFF': 90,
    'ERDA_SHOWER': 60,
    'TRUE_ARACHNID_REFLECTION': 250,
}


# List of key mappings
class Key:
    # Movement
    JUMP = 'space'
    ROPE_LIFT = 'c'
    PICK_UP = 'z'

    # Buffs
    DECENT_SHARP_EYES = 'f1'
    DECENT_HYPER_BODY = 'f2'
    DECENT_COMBAT_ORDERS = 'f3'
    DECENT_HOLY_SYMBOL = 'f4'

    # Shared skills (all classes)
    ERDA_SHOWER = '4'        # 60 sec
    TRUE_ARACHNID_REFLECTION = '5'   # 250 sec

    # Lynn-specific skills
    STRIKE = 'ctrl'              # Primary attack, 0 cd
    EARTH_PULVERIZATION = 'shift'  # 30 sec cd
    SWEEP = 'x'                  # Movement skill, fake 10 sec cd
    RAID = '1'                   # 30 sec cd
    BEASTS_RAGE = '2'            # 120 sec cd
    AWAKE = '3'                  # 120 sec cd
    ROAR = 'q'                   # 30 sec cd
    WHIRLWIND = 'w'              # 15 sec cd
    PREDATORS_BLOW = 'e'         # 30 sec cd
    LYNN_BUFF = '='              # Class buff 90 sec

    # 6th job skills
    ORIGIN = '7'
    ASCENT = '8'


#########################
#       Commands        #
#########################

def step(direction, target):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    For up: Rope Lift only (no up+jump). 1.5s sleep for regular, 3s for very high.
    For down: optional triple jump, then flash jump. For left/right: flash jump.
    """
    if direction == 'up':
        press(Key.ROPE_LIFT, 1)
        d_y = target[1] - config.player_pos[1]
        time.sleep(3.0 if abs(d_y) > 0.08 else 1.5)
        return
    num_presses = 2
    if direction == 'down':
        num_presses = 1
    if config.stage_fright and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.1, 0.3))
    d_y = target[1] - config.player_pos[1]
    if abs(d_y) > settings.move_tolerance * 1.5 and direction == 'down':
        press(Key.JUMP, 3)
    press(Key.JUMP, num_presses)


class Adjust(Command):
    """Fine-tunes player position using small movements."""

    def __init__(self, x, y, max_steps=5):
        super().__init__(locals())
        self.target = (float(x), float(y))
        self.max_steps = settings.validate_nonnegative_int(max_steps)

    def main(self):
        counter = self.max_steps
        toggle = True
        error = utils.distance(config.player_pos, self.target)
        while config.enabled and counter > 0 and error > settings.adjust_tolerance:
            if toggle:
                d_x = self.target[0] - config.player_pos[0]
                threshold = settings.adjust_tolerance / math.sqrt(2)
                if abs(d_x) > threshold:
                    walk_counter = 0
                    if d_x < 0:
                        key_down('left')
                        while config.enabled and d_x < -1 * threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('left')
                    else:
                        key_down('right')
                        while config.enabled and d_x > threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('right')
                    counter -= 1
            else:
                d_y = self.target[1] - config.player_pos[1]
                if abs(d_y) > settings.adjust_tolerance / math.sqrt(2):
                    if d_y < 0:
                        press(Key.ROPE_LIFT, 1)
                        time.sleep(1.5)
                    else:
                        key_down('down')
                        time.sleep(0.05)
                        press(Key.JUMP, 3, down_time=0.1)
                        key_up('down')
                        time.sleep(0.05)
                    counter -= 1
            error = utils.distance(config.player_pos, self.target)
            toggle = not toggle


class Buff(Command):
    """Decent skills (F1–F4) on 3 min rotation."""

    def __init__(self):
        super().__init__(locals())
        self.decent_buff_time = 0

    def main(self):
        decent_buffs = [
            Key.DECENT_SHARP_EYES,
            Key.DECENT_HYPER_BODY,
            Key.DECENT_COMBAT_ORDERS,
            Key.DECENT_HOLY_SYMBOL,
        ]
        DECENT_CD = 180  # 3 min
        now = time.time()
        if self.decent_buff_time == 0 or now - self.decent_buff_time > DECENT_CD:
            for key in decent_buffs:
                press(key, 3, up_time=0.3)
            self.decent_buff_time = now


class FlashJump(Command):
    """Performs a flash jump in the given direction (JUMP key, 2 presses). For up: Rope Lift only."""

    def __init__(self, direction):
        super().__init__(locals())
        self.direction = settings.validate_arrows(direction)

    def main(self):
        if self.direction == 'up':
            press(Key.ROPE_LIFT, 1)
            time.sleep(1.5)
            return
        key_down(self.direction)
        time.sleep(0.1)
        press(Key.JUMP, 2)
        key_up(self.direction)
        time.sleep(0.5)


class Strike(Command):
    """Attacks using Strike (ctrl) in a given direction. Primary attack, 0 cd."""

    def __init__(self, direction, attacks=2, repetitions=1):
        super().__init__(locals())
        self.direction = settings.validate_horizontal_arrows(direction)
        self.attacks = int(attacks)
        self.repetitions = int(repetitions)

    def main(self):
        time.sleep(0.05)
        key_down(self.direction)
        time.sleep(0.05)
        if config.stage_fright and utils.bernoulli(0.7):
            time.sleep(utils.rand_float(0.1, 0.3))
        for _ in range(self.repetitions):
            press(Key.STRIKE, self.attacks, up_time=0.05)
        key_up(self.direction)
        if self.attacks > 2:
            time.sleep(0.3)
        else:
            time.sleep(0.2)


class Sweep(Command):
    """Uses Sweep (x) - movement skill. Fake 10 sec cd to avoid spam."""

    def main(self):
        press(Key.SWEEP, 2, up_time=0.05)


class EarthPulverization(Command):
    """Uses Earth Pulverization once (30 sec cd)."""

    def main(self):
        press(Key.EARTH_PULVERIZATION, 3)


class Raid(Command):
    """Uses Raid once (30 sec cd)."""

    def main(self):
        press(Key.RAID, 3)


class BeastsRage(Command):
    """Uses Beasts Rage once (120 sec cd)."""

    def main(self):
        press(Key.BEASTS_RAGE, 3)


class Awake(Command):
    """Uses Awake once (120 sec cd)."""

    def main(self):
        press(Key.AWAKE, 3)


class Roar(Command):
    """Uses Roar once (30 sec cd)."""

    def main(self):
        press(Key.ROAR, 3)


class Whirlwind(Command):
    """Uses Whirlwind once (15 sec cd)."""

    def main(self):
        press(Key.WHIRLWIND, 3)


class PredatorsBlow(Command):
    """Uses Predator's Blow once (30 sec cd)."""

    def main(self):
        press(Key.PREDATORS_BLOW, 3)


class LynnBuff(Command):
    """Uses Lynn class buff (=). 90 sec duration, occasional use in rotation."""

    def main(self):
        press(Key.LYNN_BUFF, 2, up_time=0.3)


class ErdaShower(Command):
    """Uses Erda Shower once (60 sec cd, shared)."""

    def main(self):
        press(Key.ERDA_SHOWER, 3)


class TrueArachnidReflection(Command):
    """Uses True Arachnid Reflection once (250 sec cd, shared)."""

    def main(self):
        press(Key.TRUE_ARACHNID_REFLECTION, 3)


class Origin(Command):
    """Uses Origin (6th job skill) once."""

    def main(self):
        press(Key.ORIGIN, 3)


class Ascent(Command):
    """Uses Ascent (6th job skill) once."""

    def main(self):
        press(Key.ASCENT, 3)
