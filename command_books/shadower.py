"""A collection of all commands that Shadower can use to interact with the game."""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up

# Cooldowns for SkillRotation (Key attribute name -> sec). Uses Key names so rebinds work.
SKILL_COOLDOWNS = {
    'CRUEL_STAB': 0,
    'MESO_EXPLOSION': 10,   # fake 10s - costs mesos
    'DARK_FLARE': 60,
    'SUDDEN_RAID': 30,
    'SMOKESCREEN': 120,
    'SHADOW_VEIL': 60,
}


# List of key mappings
class Key:
    # Movement (flash jump = same key as jump, 2 presses double / 3 triple)
    JUMP = 'space'
    ROPE_LIFT = 'c'
    PICK_UP = 'z'
    SHADOW_ASSAULT = 't'

    # Decent skills (F1–F4), 3 min rotation
    DECENT_SHARP_EYES = 'f1'
    DECENT_HYPER_BODY = 'f2'
    DECENT_COMBAT_ORDERS = 'f3'
    DECENT_HOLY_SYMBOL = 'f4'

    # Shadow Partner buff (reapply every 180 sec)
    SHADOW_PARTNER = '1'

    # Shared skills (all classes)
    ERDA_SHOWER = '4'        # 60 sec
    TRUE_ARACHNID_REFLECTION = '5'   # 250 sec

    # 6th job skills
    ORIGIN = '7'
    ASCENT = '8'

    # Shadower-specific skills
    CRUEL_STAB = 'ctrl'      # Primary attack
    MESO_EXPLOSION = 'shift' # Fake 10s cd in rotation (costs mesos)
    DARK_FLARE = 'q'         # 60 sec
    SUDDEN_RAID = 'w'        # 30 sec
    SMOKESCREEN = 'e'        # 120 sec
    SHADOW_VEIL = 'r'        # 60 sec


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
    """Decent skills (3 min) and Shadow Partner every 180 sec."""

    def __init__(self):
        super().__init__(locals())
        self.decent_buff_time = 0
        self.shadow_partner_time = 0

    def main(self):
        decent_buffs = [
            Key.DECENT_SHARP_EYES,
            Key.DECENT_HYPER_BODY,
            Key.DECENT_COMBAT_ORDERS,
            Key.DECENT_HOLY_SYMBOL,
        ]
        DECENT_CD = 180  # 3 min
        SHADOW_PARTNER_CD = 180  # 3 min
        now = time.time()

        if self.decent_buff_time == 0 or now - self.decent_buff_time > DECENT_CD:
            for key in decent_buffs:
                press(key, 3, up_time=0.3)
            self.decent_buff_time = now
        if self.shadow_partner_time == 0 or now - self.shadow_partner_time > SHADOW_PARTNER_CD:
            press(Key.SHADOW_PARTNER, 2)
            self.shadow_partner_time = now

			
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


class ShadowAssault(Command):
    """
    ShadowAssault in a given direction, jumping if specified. Adds the player's position
    to the current Layout if necessary.
    """

    def __init__(self, direction, jump='False'):
        super().__init__(locals())
        self.direction = settings.validate_arrows(direction)
        self.jump = settings.validate_boolean(jump)

    def main(self):
        if self.direction == 'up':
            press(Key.ROPE_LIFT, 1)
            time.sleep(1.5)
            if settings.record_layout:
                config.layout.add(*config.player_pos)
            return
        num_presses = 3
        time.sleep(0.05)
        if self.direction == 'down':
            num_presses = 2
        key_down(self.direction)
        time.sleep(0.05)
        if self.jump:
            if self.direction == 'down':
                press(Key.JUMP, 3, down_time=0.1)
            else:
                press(Key.JUMP, 1)
        press(Key.SHADOW_ASSAULT, num_presses)
        key_up(self.direction)
        if settings.record_layout:
            config.layout.add(*config.player_pos)


class CruelStab(Command):
    """Attacks using 'CruelStab' in a given direction."""

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
            press(Key.CRUEL_STAB, self.attacks, up_time=0.05)
        key_up(self.direction)
        if self.attacks > 2:
            time.sleep(0.3)
        else:
            time.sleep(0.2)


class MesoExplosion(Command):
    """Uses Meso Explosion once (fake 10s cd in SkillRotation so it's not spammed; costs mesos)."""

    def main(self):
        press(Key.MESO_EXPLOSION, 1, up_time=0.05)
		
class CruelStabRandomDirection(Command):
    """Uses 'CruelStab' once."""

    def main(self):
        press(Key.CRUEL_STAB, 1, up_time=0.05)	
        
class DarkFlare(Command):
    """
    Uses Dark Flare (60 sec cd) in a given direction, or towards the center of the map if
    no direction is specified.
    """

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
        press(Key.DARK_FLARE, 3)

class ErdaShower(Command):
    """
    Use ErdaShower in a given direction, Placing ErdaFountain if specified. Adds the player's position
    to the current Layout if necessary.
    """

    def __init__(self, direction, jump='False'):
        super().__init__(locals())
        self.direction = settings.validate_arrows(direction)
        self.jump = settings.validate_boolean(jump)

    def main(self):
        if self.direction == 'up':
            press(Key.ROPE_LIFT, 1)
            time.sleep(1.5)
            if settings.record_layout:
                config.layout.add(*config.player_pos)
            return
        num_presses = 3
        time.sleep(0.05)
        if self.direction == 'down':
            num_presses = 2
        key_down(self.direction)
        time.sleep(0.05)
        if self.jump:
            if self.direction == 'down':
                press(Key.JUMP, 3, down_time=0.1)
            else:
                press(Key.JUMP, 1)
        press(Key.ERDA_SHOWER, num_presses)
        key_up(self.direction)
        if settings.record_layout:
            config.layout.add(*config.player_pos)


class SuddenRaid(Command):
    """Uses Sudden Raid once (30 sec cd)."""

    def main(self):
        press(Key.SUDDEN_RAID, 3)


class Smokescreen(Command):
    """Uses Smokescreen once (120 sec cd)."""

    def main(self):
        press(Key.SMOKESCREEN, 3)


class ShadowVeil(Command):
    """
    Uses Shadow Veil (60 sec cd) in a given direction, or towards the center of the map if
    no direction is specified.
    """

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
        press(Key.SHADOW_VEIL, 3)


class Arachnid(Command):
    """Uses True Arachnid Reflection once (250 sec cd)."""

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
