"""A collection of all commands that Hayato can use to interact with the game."""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up

# Cooldowns for SkillRotation (Key attribute name -> sec). 0 = no cooldown (spam).
# Uses Key attribute names so user rebinds are respected.
# 主要攻击按键
MAIN_ATTACK_TYPE = 'jump_att'
# 是否在控制台打印按键信息
PRINT_PRESS_MSG = False
# 技能冷却时间配置（技能名称 -> 冷却时间秒数）。0 = 无冷却时间（可连续使用）。
# 使用 Key 属性名称，以便尊重用户的按键绑定。
SKILL_COOLDOWNS = {
    'MIST_SLASH_IV': 0,
    'CROSSING_DRAW': 21,
    'LIGHT_CUTTER': 11,
    'CRASHING_TIDE': 61,
    'DARK_MOON_CUT': 21,
    'WAILING_HEAVENS': 121,
    'SILENT_ARC': 21,
    'FULL_MOON_RAGE': 61,
}


# 按键映射列表
class Key:
    # 移动
    JUMP = 'c'
    ROPE_LIFT = 'v'
    PICK_UP = 'z'

    # 增益技能
    AUTO_BUFF_LIST = '3'

    # 共享技能（所有职业）
    ERDA_SHOWER = '5'        # 60秒
    TRUE_ARACHNID_REFLECTION = '6'   # 250秒

    # Hayato 特有技能
    MIST_SLASH_IV = 'x'              # 主要攻击，无冷却时间
    CROSSING_DRAW = 'q'  # 20秒冷却
    LIGHT_CUTTER = 'd'                  # 移动技能，假10秒冷却以避免 spam
    CRASHING_TIDE = 'f'                   # 60秒冷却
    DARK_MOON_CUT = 's'            # 20秒冷却
    WAILING_HEAVENS = 'r'                  # 120秒冷却
    SILENT_ARC = 'ctrl'                  # 20秒冷却
    FULL_MOON_RAGE = 'e'                  # 60秒冷却
    
    # 6th 职业技能
    ORIGIN = '7'
    ASCENT = '8'



#########################
#       Commands        #
#########################

def step(direction, target):
    """
    在给定方向上向目标执行一步移动。
    向上：仅使用绳索升降机（不使用上+跳跃）。普通高度1.5秒睡眠，非常高的高度3秒睡眠。
    向下：可选三级跳，然后闪现跳跃。向左/右：闪现跳跃。
    """
    if direction == 'up':
        time.sleep(0.3)
        # 使用绳索升降机
        press(Key.ROPE_LIFT, 1)
        # 计算目标与当前位置的垂直距离
        d_y = target[1] - config.player_pos[1]
        # 根据距离调整睡眠时间
        time.sleep(2.0 if abs(d_y) > 0.08 else 1.2)
        return
    # 默认为2次跳跃（闪现跳跃）
    num_presses = 2
    # 向下方向只需要1次跳跃
    if direction == 'down':
        num_presses = 1
    # 如果启用了stage_fright且有75%的概率，添加随机延迟以模拟人类操作
    if config.stage_fright and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.1, 0.3))
    # 计算目标与当前位置的垂直距离
    d_y = target[1] - config.player_pos[1]
    # 如果垂直距离大于移动公差的1.5倍且方向是向下，执行三级跳
    if abs(d_y) > settings.move_tolerance * 1.5 and direction == 'down':
        press(Key.JUMP, 3)
    # 执行闪现跳跃
    press(Key.JUMP, num_presses)
    press(Key.MIST_SLASH_IV, 4, down_time=0.05, up_time=0.05)


class Adjust(Command):
    """使用小幅度移动微调玩家位置。"""

    def __init__(self, x, y, max_steps=5):
        """
        初始化调整命令。
        :param x: 目标X坐标
        :param y: 目标Y坐标
        :param max_steps: 最大调整步数
        """
        super().__init__(locals())
        self.target = (float(x), float(y))  # 目标位置坐标
        self.max_steps = settings.validate_nonnegative_int(max_steps)  # 验证并设置最大调整步数

    def main(self):
        """
        执行调整逻辑，通过小幅度移动微调玩家位置到目标点。
        """
        counter = self.max_steps  # 剩余调整步数
        toggle = True  # 切换标志，用于在X和Y方向调整之间切换
        error = utils.distance(config.player_pos, self.target)  # 当前位置与目标位置的距离
        y_fail_count = 0  # Y轴调整失败次数
        last_x_direction = ''  # 上一次X轴移动方向
        
        # 当机器人启用、还有剩余步数且误差大于调整容差时继续调整
        while config.enabled and counter > 0 and error > settings.adjust_tolerance:
            if toggle:
                # 调整X方向
                d_x = self.target[0] - config.player_pos[0]  # X方向误差
                threshold = settings.adjust_tolerance / math.sqrt(2)  # 调整阈值
                
                if abs(d_x) > threshold:  # 如果X方向误差超过阈值
                    walk_counter = 0  # 步行计数器，防止无限循环
                    
                    if d_x < 0:  # 需要向左移动
                        last_x_direction = 'left'  # 记录X轴移动方向
                        key_down('left')  # 按下左方向键
                        # 持续移动直到误差在阈值内或达到最大步行次数
                        while config.enabled and d_x < -1 * threshold and walk_counter < 60:
                            time.sleep(0.05)  # 短暂延迟
                            walk_counter += 1  # 增加步行计数
                            d_x = self.target[0] - config.player_pos[0]  # 更新误差
                        key_up('left')  # 释放左方向键
                    else:  # 需要向右移动
                        last_x_direction = 'right'  # 记录X轴移动方向
                        key_down('right')  # 按下右方向键
                        # 持续移动直到误差在阈值内或达到最大步行次数
                        while config.enabled and d_x > threshold and walk_counter < 60:
                            time.sleep(0.05)  # 短暂延迟
                            walk_counter += 1  # 增加步行计数
                            d_x = self.target[0] - config.player_pos[0]  # 更新误差
                        key_up('right')  # 释放右方向键
                    
                    counter -= 1  # 减少剩余调整步数
                    y_fail_count = 0  # 重置Y轴失败次数
            else:
                # 调整Y方向
                d_y = self.target[1] - config.player_pos[1]  # Y方向误差
                
                if abs(d_y) > settings.adjust_tolerance / math.sqrt(2):  # 如果Y方向误差超过阈值
                    if d_y < 0:  # 需要向上移动
                        press(Key.ROPE_LIFT, 1)  # 使用绳索上升
                        time.sleep(1.5)  # 等待动作完成
                    else:  # 需要向下移动
                        key_down('down')  # 按下下方向键
                        time.sleep(0.05)  # 短暂延迟
                        press(Key.JUMP, 3, down_time=0.1)  # 按跳跃键
                        key_up('down')  # 释放下方向键
                        time.sleep(0.05)  # 短暂延迟
                    
                    counter -= 1  # 减少剩余调整步数
                    
                    # 检查Y轴调整是否成功
                    new_error = utils.distance(config.player_pos, self.target)
                    if new_error >= error:  # 如果误差没有减小，认为调整失败
                        y_fail_count += 1
                    else:
                        y_fail_count = 0  # 重置失败次数
                    
                    # 当Y轴调整失败次数大于2时，向之前的X轴移动方向继续移动一个move_tolerance
                    if y_fail_count > 2 and last_x_direction:
                        print(f"Y轴调整失败次数过多({y_fail_count}次)，向{last_x_direction}方向移动0.5个move_tolerance")
                        
                        # 计算需要移动的距离（0.5个move_tolerance）
                        move_distance = settings.move_tolerance * 0.5
                        
                        # 向之前的X轴移动方向移动
                        key_down(last_x_direction)
                        time.sleep(0.2)  # 移动一段时间
                        key_up(last_x_direction)
                        time.sleep(0.1)  # 等待移动完成
                        
                        # 重置失败次数
                        y_fail_count = 0
                else:
                    y_fail_count = 0  # 重置失败次数
            
            error = utils.distance(config.player_pos, self.target)  # 更新当前误差
            toggle = not toggle  # 切换调整方向


class Buff(Command):
    """Decent skills (F1–F4) on 3 min rotation."""

    def __init__(self):
        super().__init__(locals())
        self.decent_buff_time = 0

    def main(self):
        decent_buffs = [
            Key.AUTO_BUFF_LIST,
        ]
        DECENT_CD = 180  # 3 min
        now = time.time()
        if self.decent_buff_time == 0 or now - self.decent_buff_time > DECENT_CD:
            for key in decent_buffs:
                press(key, 3, up_time=0.3)
            self.decent_buff_time = now


class FlashJump(Command):
    """执行闪现跳跃到指定方向（使用JUMP键，按2次）。向上方向：仅使用绳索升降机。"""

    def __init__(self, direction):
        """初始化FlashJump命令
        
        Args:
            direction: 跳跃方向（上、下、左、右）
        """
        super().__init__(locals())
        # 验证并设置方向键
        self.direction = settings.validate_arrows(direction)

    def main(self):
        """执行闪现跳跃
        
        执行流程：
        1. 如果方向是向上，则使用绳索升降机
        2. 否则，按下方向键，执行闪现跳跃，释放方向键
        """
        if self.direction == 'up':
            # 使用绳索升降机
            press(Key.ROPE_LIFT, 1)
            time.sleep(1.5)
            return
        # 按下方向键
        key_down(self.direction)
        time.sleep(0.1)
        # 执行闪现跳跃（按2次跳跃键）
        press(Key.JUMP, 2)
        # 释放方向键
        key_up(self.direction)
        time.sleep(0.5)


class MistSlashIV(Command):
    """使用Mist SlashIV（ctrl）在指定方向攻击。主要攻击，无冷却时间。"""

    def __init__(self, direction, attacks=2, repetitions=1):
        """初始化MistSlashIV命令
        
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
        """执行MistSlashIV攻击
        
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
            press(Key.MIST_SLASH_IV, self.attacks, up_time=0.05)
        # 释放方向键
        key_up(self.direction)
        # 根据攻击次数添加不同的延迟以确保攻击完成
        if self.attacks > 2:
            time.sleep(0.3)
        else:
            time.sleep(0.2)


class LightCutter(Command):
    """使用Light Cutter (x) - 移动技能。假10秒冷却以避免 spam。"""

    def main(self):
        press(Key.LIGHT_CUTTER, 2, up_time=0.05)


class CrossingDraw(Command):
    """使用Crossing Draw一次（20秒冷却）。"""

    def main(self):
        press(Key.CROSSING_DRAW, 3)


class CrashingTide(Command):
    """使用Crashing Tide一次（60秒冷却）。"""

    def main(self):
        press(Key.CRASHING_TIDE, 3)


class DarkMoonCut(Command):
    """使用Dark Moon Cut一次（20秒冷却）。"""

    def main(self):
        press(Key.DARK_MOON_CUT, 3)


class WailingHeavens(Command):
    """使用Wailing Heavens一次（120秒冷却）。"""

    def main(self):
        press(Key.WAILING_HEAVENS, 3)


class SilentArc(Command):
    """使用Silent Arc一次（20秒冷却）。"""

    def main(self):
        press(Key.SILENT_ARC, 3)


class FullMoonRage(Command):
    """使用Full Moon Rage一次（60秒冷却）。"""

    def main(self):
        press(Key.FULL_MOON_RAGE, 3)


class ErdaShower(Command):
    """使用Erda Shower一次（60秒冷却，共享）。"""

    def main(self):
        press(Key.ERDA_SHOWER, 3)


class TrueArachnidReflection(Command):
    """使用True Arachnid Reflection一次（250秒冷却，共享）。"""

    def main(self):
        press(Key.TRUE_ARACHNID_REFLECTION, 3)


class Origin(Command):
    """使用Origin（6th职业技能）一次。"""

    def main(self):
        press(Key.ORIGIN, 3)


class Ascent(Command):
    """使用Ascent（6th职业技能）一次。"""

    def main(self):
        press(Key.ASCENT, 3)
