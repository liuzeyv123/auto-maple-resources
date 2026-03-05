"""A collection of all commands that a Kanna can use to interact with the game."""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up

# 设置主攻模式tap或者hold
MAIN_ATTACK_TYPE = 'tap' 
# Cooldowns for SkillRotation (Key attribute name -> sec). 0 = no cooldown (spam).
# Uses Key attribute names so user rebinds are respected.
Jump_Attack_TYPE = False
# 主攻模式选择，按住或者点按 hold or tap
MAIN_ATTACK_TYPE = 'tap'

SKILL_COOLDOWNS = {
    'SOUL_SHATTER_TALISMAN': 0,
    'SPINNING_STRIKE': 12,
    'PULVERIZING_STRIKE': 30,
    'EXECUTE': 30,
    'SHADE_FLETCHED_ARROW': 30,
    'HEART_WRECK_TALISMAN': 30,
    'SUMMON_TENGU': 60,
    'SUMMON_ONI': 60,
    'BARRIER_CURSE_WARD': 60,
    'ERDA_SHOWER': 60,
    'CALL_OF_UNIT': 60,
    'SUMMON_OROCHI': 120,
    'UNLEASH_RADIANT_FLAME': 120,
    'UNLEASH_BLACK_WINGED_DESTRUCTION': 120,
    'UNLEASH_SOUL_SEARING_VENOM': 120,
    'TWILIGHT_BLOOM': 120,
    'PRINCESS_SAKUNO_BLESSING': 120,
    'HAKUMENKONMOU_JUUBI': 120,
    'SPIRIT_CHAINS': 120,
    'TRUE_NAME_REVOLUTION': 120,
    'AKATSUKI_BLESSING': 120,
    'TRUE_ARACHNID_REFLECTION': 250,
}

# 技能按键次数配置
SKILL_PRESS_COUNTS = {
    'ERDA_SHOWER': 3,
    'TRUE_ARACHNID_REFLECTION': 3,
    'SUMMON_OROCHI': 3,
    'UNLEASH_RADIANT_FLAME': 3,
    'UNLEASH_BLACK_WINGED_DESTRUCTION': 3,
    'UNLEASH_SOUL_SEARING_VENOM': 3,
    'TWILIGHT_BLOOM': 3,
    'PRINCESS_SAKUNO_BLESSING': 3,
    'HAKUMENKONMOU_JUUBI': 3,
    'SPIRIT_CHAINS': 3,
    'TRUE_NAME_REVOLUTION': 3,
    'AKATSUKI_BLESSING': 3,
    'ORIGIN': 3,
    'ASCENT': 3,
    'BARRIER_CURSE_WARD': 2,
    'SUMMON_TENGU': 2,
    'SUMMON_ONI': 2,
    'PULVERIZING_STRIKE': 2,
    'EXECUTE': 2,
    'SHADE_FLETCHED_ARROW': 2,
    'HEART_WRECK_TALISMAN': 2,
    'CALL_OF_UNIT': 2,
    'SPINNING_STRIKE': 2,
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
        # 处理向上移动的情况
        if self.direction == 'up':
            # 使用绳索升降机技能
            press(Key.ROPE_LIFT, 1)
            # 等待1.5秒，确保角色完成上升动作
            time.sleep(1.5)
            # 如果启用了布局记录，将当前位置添加到布局中
            if settings.record_layout:
                config.layout.add(*config.player_pos)
            # 结束当前步骤
            return
        # 非向上方向时，默认使用3次跳跃（闪现跳跃）
        num_presses = 3
        # 短暂延迟，确保操作流畅
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
        """初始化SoulShatterTalisman命令
        
        Args:
            direction: 攻击方向（水平方向箭头键）
            attacks: 每次重复的攻击次数，默认为2
            repetitions: 攻击重复次数，默认为1
        """
        super().__init__(locals())
        # 验证并设置方向键
        self.direction = settings.validate_horizontal_arrows(direction)
        # 转换攻击次数为整数
        self.attacks = int(attacks)
        # 转换重复次数为整数
        self.repetitions = int(repetitions)

    def main(self):
        """执行Soul-Shatter Talisman攻击
        
        执行流程：
        1. 短暂延迟确保操作流畅
        2. 按下方向键
        3. 短暂延迟
        4. 如果启用了stage_fright且有70%的概率，添加随机延迟以模拟人类操作
        5. 按照指定的重复次数执行攻击
        6. 释放方向键
        7. 根据攻击次数添加不同的延迟以确保攻击完成
        """
        # 短暂延迟，确保操作流畅
        time.sleep(0.05)
        # 按下方向键
        key_down(self.direction)
        # 短暂延迟
        time.sleep(0.05)
        # 如果启用了stage_fright且有70%的概率，添加随机延迟以模拟人类操作
        if config.stage_fright and utils.bernoulli(0.7):
            time.sleep(utils.rand_float(0.1, 0.3))
        # 按照指定的重复次数执行攻击
        for _ in range(self.repetitions):
            press(Key.SOUL_SHATTER_TALISMAN, self.attacks, up_time=0.05)
        # 释放方向键
        key_up(self.direction)
        # 根据攻击次数添加不同的延迟以确保攻击完成
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
