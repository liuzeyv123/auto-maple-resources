"""A collection of all commands that Adele can use to interact with the game."""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up

# Cooldowns for SkillRotation (key -> sec). 0 = no cooldown (spam).
SKILL_COOLDOWNS = {
    'ctrl': 0,     # Cleave (primary attack)
    'x': 1.5,      # Plummet (use in air; jump first)
    'shift': 20,   # Aether Bloom
    'q': 30,       # Reign of Destruction
    'w': 12,       # Noble Summons
    'e': 0.5,      # Hunting Decree
    '1': 120,      # Blade Torrent
    '2': 120,      # Shardbreaker
    '4': 60,       # Erda Shower (shared)
    '5': 250,      # True Arachnid Reflection (shared)
}


# List of key mappings
class Key:
    # Movement (flash jump = same key as jump, 2 presses double / 3 triple)
    JUMP = 'space'
    ROPE_LIFT = 'c'
    PICK_UP = 'z'

    # Decent skills (F1–F4), 3 min rotation
    DECENT_SHARP_EYES = 'f1'
    DECENT_HYPER_BODY = 'f2'
    DECENT_COMBAT_ORDERS = 'f3'
    DECENT_HOLY_SYMBOL = 'f4'

    # Shared skills (all classes)
    ERDA_SHOWER = '4'        # 60 sec
    TRUE_ARACHNID_REFLECTION = '5'   # 250 sec

    # 6th job skills
    ORIGIN = '7'
    ASCENT = '8'

    # Adele-specific skills
    CLEAVE = 'ctrl'              # Primary attack, 0 cd
    PLUMMET = 'x'                # Use in air (jump first), 1.5 sec cd
    AETHER_BLOOM = 'shift'       # 20 sec cd
    REIGN_OF_DESTRUCTION = 'q'   # 30 sec cd
    NOBLE_SUMMONS = 'w'          # 12 sec cd
    HUNTING_DECREE = 'e'         # 0.5 sec cd
    BLADE_TORRENT = '1'          # 120 sec cd
    SHARDBREAKER = '2'           # 120 sec cd


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


class Cleave(Command):
    """Attacks using Cleave (ctrl) in a given direction. Primary attack, 0 cd."""

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
            press(Key.CLEAVE, self.attacks, up_time=0.05)
        key_up(self.direction)
        if self.attacks > 2:
            time.sleep(0.3)
        else:
            time.sleep(0.2)


class Plummet(Command):
    """Uses Plummet (x) in the air. Jumps first then uses skill; 1.5 sec cd."""

    def main(self):
        press(Key.JUMP, 1, down_time=0.1, up_time=0.15)
        press(Key.PLUMMET, 2, up_time=0.05)


class AetherBloom(Command):
    """Uses Aether Bloom once (20 sec cd)."""

    def main(self):
        press(Key.AETHER_BLOOM, 3)


class ReignOfDestruction(Command):
    """Uses Reign of Destruction (30 sec cd) in a direction or toward map center."""

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        if self.direction:
            press(self.direction, 1, down_time=0.1, up_time=0.05)
        else:
            if config.player_pos[0] > 0.5:
                press('left', 1, down_time=0.1, up_time=0.05)
            else:
                press('right', 1, down_time=0.1, up_time=0.05)
        press(Key.REIGN_OF_DESTRUCTION, 3)


class NobleSummons(Command):
    """Uses Noble Summons once (12 sec cd)."""

    def main(self):
        press(Key.NOBLE_SUMMONS, 3)


class HuntingDecree(Command):
    """Uses Hunting Decree once (0.5 sec cd)."""

    def main(self):
        press(Key.HUNTING_DECREE, 2, up_time=0.05)


class BladeTorrent(Command):
    """Uses Blade Torrent once (120 sec cd)."""

    def main(self):
        press(Key.BLADE_TORRENT, 3, down_time=0.1)


class Shardbreaker(Command):
    """Uses Shardbreaker (120 sec cd) in a direction or toward map center."""

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        if self.direction:
            press(self.direction, 1, down_time=0.1, up_time=0.05)
        else:
            if config.player_pos[0] > 0.5:
                press('left', 1, down_time=0.1, up_time=0.05)
            else:
                press('right', 1, down_time=0.1, up_time=0.05)
        press(Key.SHARDBREAKER, 3)


class ErdaShower(Command):
    """Uses Erda Shower once (60 sec cd, shared)."""

    def main(self):
        press(Key.ERDA_SHOWER, 3)


class Arachnid(Command):
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
