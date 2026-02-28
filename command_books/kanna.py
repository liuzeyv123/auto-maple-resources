"""A collection of all commands that a Kanna can use to interact with the game."""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up

# Cooldowns for SkillRotation (key -> sec). 0 = no cooldown (spam).
SKILL_COOLDOWNS = {
    'ctrl': 0,         # Soul-Shatter Talisman (no cd)
    'shift': 12,       # Spinning Strike 12 sec
    'a': 30,           # Pulverizing Strike 30 sec
    's': 30,           # Execute 30 sec
    'd': 30,           # Shade Fletched Arrow 30 sec
    'f': 30,           # Heart Wreck Talisman 30 sec
    'q': 60,           # Summon Tengu 60 sec
    'w': 60,           # Summon Oni 60 sec
    't': 60,           # Barrier Curse Ward 60 sec
    '4': 60,           # Erda Shower (shared) 60 sec
    'home': 60,        # Call of Unit 60 sec
    'e': 120,          # Summon Orochi 120 sec
    'r': 120,          # Unleash Radiant Flame 120 sec
    'v': 120,          # Unleash Black Winged Destruction 120 sec
    'h': 120,          # Unleash Soul-Searing Venom 120 sec
    '1': 120,          # Twilight Bloom 120 sec
    '2': 120,          # Princess Sakuno's Blessing 120 sec
    '3': 120,          # Hakumenkonmou Juubi 120 sec
    'page up': 120,    # Spirit Chains 120 sec
    'page down': 120,  # True Name Revolution 120 sec
    'end': 120,        # Akatsuki Blessing 120 sec
    '5': 250,          # True Arachnid Reflection (shared) 250 sec
}


# List of key mappings
class Key:
    # Movement (teleport class: no double jump; use teleport to get around)
    JUMP = 'space'
    TELEPORT = 'c'
    ROPE_LIFT = 'x'
    PICK_UP = 'z'

    # Decent skills (F1–F4), 3 min rotation
    DECENT_SHARP_EYES = 'f1'
    DECENT_HYPER_BODY = 'f2'
    DECENT_COMBAT_ORDERS = 'f3'
    DECENT_HOLY_SYMBOL = 'f4'

    # Shared skills (all classes)
    ERDA_SHOWER = '4'              # 60 sec
    TRUE_ARACHNID_REFLECTION = '5' # 250 sec

    # 6th job skills
    ORIGIN = '7'
    ASCENT = '8'

    # Kanna-specific: main attack and movement skills
    SOUL_SHATTER_TALISMAN = 'ctrl'  # No cd – primary attack
    SPINNING_STRIKE = 'shift'       # 12 sec
    SUMMON_TENGU = 'q'              # 60 sec
    SUMMON_ONI = 'w'                # 60 sec
    SUMMON_OROCHI = 'e'             # 120 sec
    UNLEASH_RADIANT_FLAME = 'r'     # 120 sec
    BARRIER_CURSE_WARD = 't'        # 60 sec
    PULVERIZING_STRIKE = 'a'        # 30 sec
    EXECUTE = 's'                   # 30 sec
    SHADE_FLETCHED_ARROW = 'd'      # 30 sec
    HEART_WRECK_TALISMAN = 'f'      # 30 sec
    UNLEASH_BLACK_WINGED_DESTRUCTION = 'v'  # 120 sec
    UNLEASH_SOUL_SEARING_VENOM = 'h'        # 120 sec
    TWILIGHT_BLOOM = '1'            # 120 sec
    PRINCESS_SAKUNO_BLESSING = '2'  # 120 sec
    HAKUMENKONMOU_JUUBI = '3'       # 120 sec
    CALL_OF_UNIT = 'home'           # 60 sec
    SPIRIT_CHAINS = 'page up'       # 120 sec
    TRUE_NAME_REVOLUTION = 'page down'  # 120 sec
    AKATSUKI_BLESSING = 'end'       # 120 sec


#########################
#       Commands        #
#########################
def step(direction, target):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    For up: Rope Lift only (no up+jump). 1.5s sleep for regular, 3s for very high.
    For down: optional jump, then teleport. For left/right: teleport.
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
    press(Key.TELEPORT, num_presses)


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
        y_threshold = settings.adjust_tolerance
        while config.enabled and counter > 0 and error > settings.adjust_tolerance:
            if toggle:
                d_x = self.target[0] - config.player_pos[0]
                if abs(d_x) > xy_threshold:
                    walk_counter = 0
                    if d_x < 0:
                        key_down('left')
                        while config.enabled and d_x < -1 * xy_threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('left')
                    else:
                        key_down('right')
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
                        Teleport('up').main()
                    else:
                        key_down('down')
                        time.sleep(0.05)
                        press(Key.JUMP, 3, down_time=0.1)
                        key_up('down')
                        time.sleep(0.05)
                    counter -= 1
            error = utils.distance(config.player_pos, self.target)
            toggle = not toggle


class Teleport(Command):
    """
    Teleports in a given direction, jumping if specified. Adds the player's position
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
        press(Key.TELEPORT, num_presses)
        key_up(self.direction)
        if settings.record_layout:
            config.layout.add(*config.player_pos)


class RopeLift(Command):
    """Uses Rope Lift once (e.g. for going up)."""

    def main(self):
        press(Key.ROPE_LIFT, 1)


class Pickup(Command):
    """Uses Pick Up once."""

    def main(self):
        press(Key.PICK_UP, 1)


class Buff(Command):
    """Uses decent skills (F1–F4) on 3 min rotation."""

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


class SoulShatterTalisman(Command):
    """Attacks using Soul-Shatter Talisman in a given direction (primary attack, no cd)."""

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
            press(Key.SOUL_SHATTER_TALISMAN, self.attacks, up_time=0.05)
        key_up(self.direction)
        if self.attacks > 2:
            time.sleep(0.3)
        else:
            time.sleep(0.2)


class SpinningStrike(Command):
    """Uses Spinning Strike once (12 sec cd)."""

    def main(self):
        press(Key.SPINNING_STRIKE, 2, up_time=0.05)


class SummonTengu(Command):
    """Uses Summon Tengu once (60 sec cd)."""

    def main(self):
        press(Key.SUMMON_TENGU, 2, up_time=0.05)


class SummonOni(Command):
    """Uses Summon Oni once (60 sec cd)."""

    def main(self):
        press(Key.SUMMON_ONI, 2, up_time=0.05)


class SummonOrochi(Command):
    """Uses Summon Orochi once (120 sec cd)."""

    def main(self):
        press(Key.SUMMON_OROCHI, 3)


class UnleashRadiantFlame(Command):
    """Uses Unleash Radiant Flame once (120 sec cd)."""

    def main(self):
        press(Key.UNLEASH_RADIANT_FLAME, 3)


class BarrierCurseWard(Command):
    """Uses Barrier Curse Ward once (60 sec cd)."""

    def main(self):
        press(Key.BARRIER_CURSE_WARD, 2)


class PulverizingStrike(Command):
    """Uses Pulverizing Strike once (30 sec cd)."""

    def main(self):
        press(Key.PULVERIZING_STRIKE, 2, up_time=0.05)


class Execute(Command):
    """Uses Execute once (30 sec cd)."""

    def main(self):
        press(Key.EXECUTE, 2, up_time=0.05)


class ShadeFletchedArrow(Command):
    """Uses Shade Fletched Arrow once (30 sec cd)."""

    def main(self):
        press(Key.SHADE_FLETCHED_ARROW, 2, up_time=0.05)


class HeartWreckTalisman(Command):
    """Uses Heart Wreck Talisman once (30 sec cd)."""

    def main(self):
        press(Key.HEART_WRECK_TALISMAN, 2, up_time=0.05)


class UnleashBlackWingedDestruction(Command):
    """Uses Unleash Black Winged Destruction once (120 sec cd)."""

    def main(self):
        press(Key.UNLEASH_BLACK_WINGED_DESTRUCTION, 3)


class UnleashSoulSearingVenom(Command):
    """Uses Unleash Soul-Searing Venom once (120 sec cd)."""

    def main(self):
        press(Key.UNLEASH_SOUL_SEARING_VENOM, 3)


class TwilightBloom(Command):
    """Uses Twilight Bloom once (120 sec cd)."""

    def main(self):
        press(Key.TWILIGHT_BLOOM, 3)


class PrincessSakunoBlessing(Command):
    """Uses Princess Sakuno's Blessing once (120 sec cd)."""

    def main(self):
        press(Key.PRINCESS_SAKUNO_BLESSING, 3)


class HakumenkonmouJuubi(Command):
    """Uses Hakumenkonmou Juubi once (120 sec cd)."""

    def main(self):
        press(Key.HAKUMENKONMOU_JUUBI, 3)


class ErdaShower(Command):
    """Uses Erda Shower once (60 sec cd, shared)."""

    def main(self):
        press(Key.ERDA_SHOWER, 3)


class TrueArachnidReflection(Command):
    """Uses True Arachnid Reflection once (250 sec cd, shared)."""

    def main(self):
        press(Key.TRUE_ARACHNID_REFLECTION, 3)


class CallOfUnit(Command):
    """Uses Call of Unit once (60 sec cd)."""

    def main(self):
        press(Key.CALL_OF_UNIT, 2)


class SpiritChains(Command):
    """Uses Spirit Chains once (120 sec cd)."""

    def main(self):
        press(Key.SPIRIT_CHAINS, 3)


class TrueNameRevolution(Command):
    """Uses True Name Revolution once (120 sec cd)."""

    def main(self):
        press(Key.TRUE_NAME_REVOLUTION, 3)


class AkatsukiBlessing(Command):
    """Uses Akatsuki Blessing once (120 sec cd)."""

    def main(self):
        press(Key.AKATSUKI_BLESSING, 3)


class Origin(Command):
    """Uses Origin (6th job skill) once."""

    def main(self):
        press(Key.ORIGIN, 3)


class Ascent(Command):
    """Uses Ascent (6th job skill) once."""

    def main(self):
        press(Key.ASCENT, 3)
