"""A collection of all commands that a Phantom can use to interact with the game."""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up

# Cooldowns for SkillRotation (Key attribute name -> sec). 0 = no cooldown (spam).
# Uses Key attribute names so user rebinds are respected.
SKILL_COOLDOWNS = {
    'MILLE_AIGUILLES': 0,
    'HEX_TEMPEST': 18,
    'ACE_IN_THE_HOLE': 15,
    'PHANTOM_MARK': 30,
    'RIFT_BREAK': 30,
    'CARTE_ROSE_FINALE': 30,
    'ERDA_SHOWER': 60,
    'TRUE_ARACHNID_REFLECTION': 250,
}

# If Alt never registers in-game for double jump, set to True and bind jump to Space in-game.
USE_SPACE_FOR_MOVEMENT_JUMP = False


# List of key mappings
class Key:
    # Movement (double jump = press jump twice; game triggers Phantom Swiftness automatically)
    JUMP = 'space'
    ROPE_LIFT = 'c'
    PICK_UP = 'z'

    # Buffs
    # Decent skills (F1–F4), 3 min rotation
    DECENT_SHARP_EYES = 'f1'
    DECENT_HYPER_BODY = 'f2'
    DECENT_COMBAT_ORDERS = 'f3'
    DECENT_HOLY_SYMBOL = 'f4'
    FINAL_FEINT = '-'   # 30 min CD

    # Shared skills (all classes)
    ERDA_SHOWER = '4'        # 60 sec
    TRUE_ARACHNID_REFLECTION = '5'  # 250 sec
    # Phantom-specific skills (keys match SKILL_COOLDOWNS above)
    MILLE_AIGUILLES = 'ctrl'  # 0 cd – primary attack, hold left/right 1–3 sec
    RIFT_BREAK = '1'          # 30 sec
    CARTE_ROSE_FINALE = '2'   # 30 sec
    ACE_IN_THE_HOLE = 'q'    # 15 sec
    PHANTOM_MARK = 'w'       # 30 sec
    HEX_TEMPEST = 'shift'    # 18 sec
    PENOMBRE = 'x'           # attack while teleporting backwards

    # 6th job skills
    ORIGIN = '7'
    ASCENT = '8'


#########################
#       Commands        #
#########################
# ShroudWalk is available as a command for routines; step() uses only triple jump for fluid movement.


def step(direction, target):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    For up: Rope Lift only (no up+jump). 1.5s sleep for regular, 3s for very high.
    For down: optional triple jump, then double jump. For left/right: triple jump.
    """
    if direction == 'up':
        press(Key.ROPE_LIFT, 1)
        d_y = target[1] - config.player_pos[1]
        time.sleep(3.0 if abs(d_y) > 0.08 else 1.5)
        return
    num_presses = 3
    if direction == 'down':
        num_presses = 2
    if config.stage_fright and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.075, 0.15))
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
        xy_threshold = settings.adjust_tolerance / math.sqrt(2)
        # Only do vertical adjust when Y error is at least full tolerance (avoids random jump-up from jitter)
        y_threshold = settings.adjust_tolerance
        while config.enabled and counter > 0 and error > settings.adjust_tolerance:
            if toggle:
                d_x = self.target[0] - config.player_pos[0]
                if abs(d_x) > xy_threshold:
                    walk_counter = 0
                    if d_x < 0:
                        key_down('left')
                        press(Key.JUMP, 1, down_time=0.05, up_time=0.05)  # jump while moving left
                        while config.enabled and d_x < -1 * xy_threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('left')
                    else:
                        key_down('right')
                        press(Key.JUMP, 1, down_time=0.05, up_time=0.05)  # jump while moving right
                        while config.enabled and d_x > xy_threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('right')
                    counter -= 1
            else:
                d_y = self.target[1] - config.player_pos[1]
                if abs(d_y) > y_threshold:
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


class Buff(Command):
    """Uses each of Phantom's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.cd1800_buff_time = 0   # Final Feint 30 min
        self.decent_buff_time = 0

    def main(self):
        # Decent Sharp Eyes, Decent Hyper Body, Decent Combat Orders, Decent Holy Symbol (3 min CD)
        decent_buffs = [
            Key.DECENT_SHARP_EYES,
            Key.DECENT_HYPER_BODY,
            Key.DECENT_COMBAT_ORDERS,
            Key.DECENT_HOLY_SYMBOL,
        ]
        DECENT_CD = 180  # 3 min
        now = time.time()

        if self.cd1800_buff_time == 0 or now - self.cd1800_buff_time > 1800:
            press(Key.FINAL_FEINT, 2)
            self.cd1800_buff_time = now
        if self.decent_buff_time == 0 or now - self.decent_buff_time > DECENT_CD:
            for key in decent_buffs:
                press(key, 3, up_time=0.3)
            self.decent_buff_time = now



class MilleAiguilles(Command):
    """Attacks using Mille Aiguilles in a given direction (hold)."""

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
            press(Key.MILLE_AIGUILLES, self.attacks, up_time=0.05)
        key_up(self.direction)
        if self.attacks > 2:
            time.sleep(0.3)
        else:
            time.sleep(0.2)


class HexTempest(Command):
    """Uses Hex Tempest (18 sec cd); hold 3s and walk left/right to clear mobs."""

    def main(self):
        press(Key.HEX_TEMPEST, 1, down_time=3)


class AceInTheHole(Command):
    """Uses Ace in the Hole once."""

    def main(self):
        press(Key.ACE_IN_THE_HOLE, 2, up_time=0.05)


class CarteRoseFinale(Command):
    """Uses Carte Rose Finale (hyper) once."""

    def main(self):
        press(Key.CARTE_ROSE_FINALE, 3)


class PhantomMark(Command):
    """Uses Phantom's Mark once."""

    def main(self):
        press(Key.PHANTOM_MARK, 3)


class RiftBreak(Command):
    """Uses Rift Break once (30 sec cd)."""

    def main(self):
        press(Key.RIFT_BREAK, 3)


class ErdaShower(Command):
    """Uses Erda Shower once (60 sec cd)."""

    def main(self):
        press(Key.ERDA_SHOWER, 3)


class TrueArachnidReflection(Command):
    """Uses True Arachnid Reflection once (250 sec cd)."""

    def main(self):
        press(Key.TRUE_ARACHNID_REFLECTION, 3)


class Penombre(Command):
    """Uses Penombre once (leap back and attack)."""

    def main(self):
        press(Key.PENOMBRE, 2, up_time=0.05)


class Origin(Command):
    """Uses Origin (6th job skill) once."""

    def main(self):
        press(Key.ORIGIN, 3)


class Ascent(Command):
    """Uses Ascent (6th job skill) once."""

    def main(self):
        press(Key.ASCENT, 3)
