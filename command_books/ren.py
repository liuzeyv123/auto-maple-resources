"""A collection of all commands that Ren can use to interact with the game."""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up

# Cooldowns for SkillRotation (key -> sec). 0 = no cooldown (spam).
SKILL_COOLDOWNS = {
    'ctrl': 0,       # Plum Blossom Sword (hold left/right and spam)
    'shift': 17,     # Spirit Sword: 5 presses to trigger, then 17 sec cd
    '4': 60,         # Erda Shower 60 sec (shared)
    '5': 250,        # True Arachnid Reflection 250 sec (shared)
    '1': 120,        # Thousand Blossom Flurry 120 sec
    '2': 120,        # Soul Immeasurable 120 sec
    '3': 120,        # Dancing Annihilation 120 sec
}
# Keys that need multiple presses when used in rotation (e.g. Spirit Sword = 5)
SKILL_PRESS_COUNTS = {
    'shift': 5,
}


# List of key mappings (space = jump, z = pick up; no alt)
class Key:
    # Movement (flash jump = same key as jump, more presses)
    JUMP = 'space'
    ROPE_LIFT = 'c'
    PICK_UP = 'z'

    # Decent skills (F1–F4), 3 min rotation
    DECENT_SHARP_EYES = 'f1'
    DECENT_HYPER_BODY = 'f2'
    DECENT_COMBAT_ORDERS = 'f3'
    DECENT_HOLY_SYMBOL = 'f4'

    # Shared skills (all classes)
    ERDA_SHOWER = '4'        # 60 sec cd
    TRUE_ARACHNID_REFLECTION = '5'   # 250 sec cd
    # Ren-specific skills
    PLUM_BLOSSOM_SWORD = 'ctrl'   # Primary attack, spam while walking left/right
    SPIRIT_SWORD = 'shift'        # 5 presses in rapid succession, then 17 sec cd
    THOUSAND_BLOSSOM_FLURRY = '1'    # Final Plum Blossom Sword Thousand Blossom Flurry, 120 sec (attack buff)
    SOUL_IMMEASURABLE = '2'          # 120 sec cd
    DANCING_ANNIHILATION = '3'       # Final Plum Blossom Sword Dancing Annihilation, 120 sec cd

    # 6th job skills
    ORIGIN = '7'
    ASCENT = '8'


#########################
#       Commands        #
#########################
def step(direction, target):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    When direction is up, presses Rope Lift once. Optional vertical jump, then 2 presses of
    JUMP for left/right, 1 for up/down (flash jump).
    """
    num_presses = 2
    if direction == 'up' or direction == 'down':
        num_presses = 1
    if direction == 'up':
        press(Key.ROPE_LIFT, 1)
    if config.stage_fright and direction != 'up' and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.1, 0.3))
    d_y = target[1] - config.player_pos[1]
    if abs(d_y) > settings.move_tolerance * 1.5:
        if direction == 'down':
            press(Key.JUMP, 3)
        elif direction == 'up':
            press(Key.JUMP, 2)
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
                        FlashJump('up').main()
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
    """Decent skills (3 min) and Ren's 120 sec buffs: Thousand Blossom Flurry, Soul Immeasurable, Dancing Annihilation."""

    def __init__(self):
        super().__init__(locals())
        self.decent_buff_time = 0
        self.cd120_time = 0

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
        if self.cd120_time == 0 or now - self.cd120_time > 120:
            press(Key.THOUSAND_BLOSSOM_FLURRY, 2)
            press(Key.SOUL_IMMEASURABLE, 2)
            press(Key.DANCING_ANNIHILATION, 2)
            self.cd120_time = now


class FlashJump(Command):
    """Performs a flash jump in the given direction (JUMP key, 2 presses)."""

    def __init__(self, direction):
        super().__init__(locals())
        self.direction = settings.validate_arrows(direction)

    def main(self):
        key_down(self.direction)
        time.sleep(0.1)
        press(Key.JUMP, 2)
        key_up(self.direction)
        time.sleep(0.5)


class PlumBlossomSword(Command):
    """Attacks using Plum Blossom Sword (ctrl) in a given direction (hold)."""

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
            press(Key.PLUM_BLOSSOM_SWORD, self.attacks, up_time=0.05)
        key_up(self.direction)
        time.sleep(0.2)


class SpiritSword(Command):
    """Uses Spirit Sword: 5 presses in rapid succession to trigger, then 17 sec cd."""

    def main(self):
        press(Key.SPIRIT_SWORD, 5, down_time=0.05, up_time=0.03)


class ErdaShower(Command):
    """Uses Erda Shower once (60 sec cd)."""

    def main(self):
        press(Key.ERDA_SHOWER, 3)


class TrueArachnidReflection(Command):
    """Uses True Arachnid Reflection once (250 sec cd)."""

    def main(self):
        press(Key.TRUE_ARACHNID_REFLECTION, 3)


class ThousandBlossomFlurry(Command):
    """Uses Final Plum Blossom Sword Thousand Blossom Flurry (120 sec cd, attack buff)."""

    def main(self):
        press(Key.THOUSAND_BLOSSOM_FLURRY, 2)


class SoulImmeasurable(Command):
    """Uses Soul Immeasurable once (120 sec cd)."""

    def main(self):
        press(Key.SOUL_IMMEASURABLE, 2)


class DancingAnnihilation(Command):
    """Uses Final Plum Blossom Sword Dancing Annihilation once (120 sec cd)."""

    def main(self):
        press(Key.DANCING_ANNIHILATION, 2)


class Origin(Command):
    """Uses Origin (6th job skill) once."""

    def main(self):
        press(Key.ORIGIN, 3)


class Ascent(Command):
    """Uses Ascent (6th job skill) once."""

    def main(self):
        press(Key.ASCENT, 3)
