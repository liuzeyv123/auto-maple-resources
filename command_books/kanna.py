"""A collection of all commands that a Kanna can use to interact with the game."""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up

# Cooldowns for SkillRotation (Key attribute name -> sec). 0 = no cooldown (spam).
# Uses Key attribute names so user rebinds are respected.
Jump_Attack_TYPE = False
# 主攻模式选择，按住或者点按 hold or tap
MAIN_ATTACK_TYPE = 'tap'
# 是否在控制台打印按键信息
PRINT_PRESS_MSG = True

# 向下跳跃计数器和之前X轴移动方向
down_jump_count = 0
previous_x_direction = 'right'  # 默认向右
# 向上移动失败计数器
up_move_fail_count = 0

SKILL_COOLDOWNS = {
    '主攻': 0,
    '感应_鬼1': 12,
    '感应_鬼2': 30,
    '感应_鸦1': 30,
    '感应_蛇1': 30,
    '大符咒': 30,
    'V_鸦': 120,
    'V_蛇': 120,
}

# 技能轮换黑名单，这些技能不会被加入技能轮换模式
# 示例：SKILL_ROTATION_BLACKLIST = ['炎魔召唤', '终极无限2号']
# SKILL_ROTATION_BLACKLIST = ['传染','毒球','火球','弹球','毒阵放置','炎魔召唤']

# 依赖爆发的技能配置：{技能名: (爆发1窗口, 爆发2窗口)}
# 窗口时间为0表示不依赖该爆发，大于0表示在该爆发激活后的窗口时间内可用
DEPENDENT_SKILLS = {
    '感应_鬼1': (55, 55),
    '感应_鬼2': (55, 55),
    '感应_鸦1': (25, 25),
    'V_鸦': (25, 25),
    '感应_蛇1': (0, 25),   # 爆发1不能用，爆发2可以用
    'V_蛇': (0, 25),       # 爆发1不能用，爆发2可以用
    '大符咒': (0, 0),      # 不依赖爆发
}


class Key:
    # Movement (teleport class: no double jump; use teleport to get around)
    JUMP = 'c'
    TELEPORT = 'shift'
    ROPE_LIFT = 'v'
    PICK_UP = 'z'

    # Decent skills (F1–F4), 3 min rotation
    bufff2 = 'f2'
    爆发1 = '1'     #一键爆发60s
    爆发2 = '2'     #一键爆发120s

    # Shared skills (all classes)
    爱尔达放置 = 'f'              # 60 sec
    威尔蜘蛛腿 = '5' # 250 sec

    # 6th job skills
    ORIGIN = 'w'
    ASCENT = 'ctrl'

    # PMAGIC-specific skills
    主攻 = 'x'
    感应_鬼1 = 'a'
    感应_鬼2 = 'q'
    感应_鸦1 = 'w'
    感应_蛇1 = 'e'
    大符咒 = 'r'
    V_鸦 = 's'
    V_蛇 = 'd'


#########################
#       Commands        #
#########################
def step(direction, target):
    """
    在给定方向上向目标执行一步移动。
    向上：仅使用绳索升降机（不使用上+跳跃）。普通高度1.5秒睡眠，非常高的高度3秒睡眠。
    向下：可选三级跳。
    向左/右：闪现跳跃+攻击。
    """
    global down_jump_count, previous_x_direction
    
    # 记录X轴移动方向
    if direction in ['left', 'right']:
        previous_x_direction = direction
    
    # 处理向下跳跃计数
    if direction == 'down':
        # 增加向下跳跃计数器
        down_jump_count += 1
        print(f'向下跳跃次数: {down_jump_count}')
        
        # 如果连续执行了3次向下跳跃，向之前X轴移动的方向进行一次跳跃
        if down_jump_count >= 3:
            print(f'连续执行向下跳跃 {down_jump_count}次，向{previous_x_direction}方向跳跃')
            # 向之前X轴移动的方向跳跃
            key_down(previous_x_direction)
            time.sleep(0.05)
            press(Key.JUMP, 1)
            key_up(previous_x_direction)
            time.sleep(0.2)
            # 重置计数器
            down_jump_count = 0
    else:
        # 如果不是向下方向，重置计数器
        down_jump_count = 0
    
    # 默认为1次闪现
    num_presses = 1
    
    if direction == 'up':
        global up_move_fail_count
        # 计算目标与当前位置的垂直距离
        d_y = target[1] - config.player_pos[1]
        # 记录移动前的位置
        before_pos = config.player_pos
        # 当垂直距离大于0.25时，需要使用绳索升降机
        if abs(d_y) > 0.25:
            time.sleep(0.3)
            # 使用绳索升降机
            press(Key.ROPE_LIFT, 2)
            # 根据距离调整睡眠时间
            time.sleep(2.0 if abs(d_y) > 0.08 else 1)
        # 当垂直距离小于0.25时执行闪现
        else:
            key_down("up")
            time.sleep(0.1)
            press(Key.TELEPORT, num_presses)
            key_up("up")
        # 检查Y轴移动是否成功
        after_pos = config.player_pos
        if abs(after_pos[1] - before_pos[1]) < 0.02:
            # 向上移动失败，增加失败计数器
            up_move_fail_count += 1
            print(f'向上移动失败，失败次数: {up_move_fail_count}')
            # 只有连续失败两次才会触发跳跃
            if up_move_fail_count >= 2:
                print(f'向上移动连续失败{up_move_fail_count}次，尝试向{previous_x_direction}方向跳跃')
                # 向之前的X轴移动方向跳跃
                key_down(previous_x_direction)
                time.sleep(0.1)
                key_up(previous_x_direction)
                time.sleep(0.3)
                # 重置失败计数器
                up_move_fail_count = 0
        else:
            # 向上移动成功，重置失败计数器
            up_move_fail_count = 0
        return
    # 向下方向只需要1次跳跃
    if direction == 'down':
        print('step的向下跳跃1次')
        num_presses = 1
    # 如果启用了stage_fright且有75%的概率，添加随机延迟以模拟人类操作
    if config.stage_fright and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.075, 0.15))
    # 记录移动前的位置
    before_pos = config.player_pos
    # 计算目标与当前位置的垂直距离
    d_y = target[1] - config.player_pos[1]
    # if abs(d_y) > settings.move_tolerance * 1.5 and direction == 'down':
    if abs(d_y) > 0.25 and direction == 'down':
        press(Key.JUMP, 1)
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
        y_fail_count = 0  # Y轴调整失败次数
        last_x_direction = 'right'  # 上一次X轴移动方向，默认为右
        last_position = config.player_pos  # 上一次位置
        last_position_time = time.time()  # 上一次位置记录时间
        while config.enabled and counter > 0 and error > settings.adjust_tolerance:
            # 检查位置是否超过2秒未变化
            current_time = time.time()
            if current_time - last_position_time > 2.0 and last_x_direction:
                print(f"位置超过2秒未变化，向{last_x_direction}方向跳跃1次")
                # 向之前的X轴移动方向跳跃
                key_down(last_x_direction)
                time.sleep(0.1)
                press(Key.JUMP, 1)
                key_up(last_x_direction)
                time.sleep(0.5)
                # 更新位置和时间
                last_position = config.player_pos
                last_position_time = current_time
            
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
                        # 更新位置和时间
                        last_position = config.player_pos
                        last_position_time = time.time()
                    else:  # 需要向右移动
                        last_x_direction = 'right'  # 记录X轴移动方向
                        key_down('right')  # 按下右方向键
                        # 持续移动直到误差在阈值内或达到最大步行次数
                        while config.enabled and d_x > threshold and walk_counter < 60:
                            time.sleep(0.05)  # 短暂延迟
                            walk_counter += 1  # 增加步行计数
                            d_x = self.target[0] - config.player_pos[0]  # 更新误差
                        key_up('right')  # 释放右方向键
                        # 更新位置和时间
                        last_position = config.player_pos
                        last_position_time = time.time()
                    
                    counter -= 1  # 减少剩余调整步数
                    y_fail_count = 0  # 重置Y轴失败次数
            else:
                # 调整Y方向
                d_y = self.target[1] - config.player_pos[1]  # Y方向误差
                
                if abs(d_y) > settings.adjust_tolerance / math.sqrt(2):  # 如果Y方向误差超过阈值
                    if d_y < 0:  # 需要向上移动
                        Teleport('up').main()
                        # 更新位置和时间
                        last_position = config.player_pos
                        last_position_time = time.time()
                    else:  # 需要向下移动
                        key_down('down')  # 按下下方向键
                        time.sleep(0.1)  # 短暂延迟
                        press(Key.JUMP, 2, down_time=0.1)  # 按跳跃键
                        key_up('down')  # 释放下方向键
                        time.sleep(0.3)  # 短暂延迟
                        # 更新位置和时间
                        last_position = config.player_pos
                        last_position_time = time.time()
                    
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
                        # 更新位置和时间
                        last_position = config.player_pos
                        last_position_time = time.time()
                        
                        # 重置失败次数
                        y_fail_count = 0
                else:
                    y_fail_count = 0  # 重置失败次数
            
            error = utils.distance(config.player_pos, self.target)  # 更新当前误差
            toggle = not toggle  # 切换调整方向


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
            time.sleep(0.4)
            # 使用绳索升降机技能
            press(Key.ROPE_LIFT, 2)
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
        time.sleep(0.4)
        press(Key.ROPE_LIFT, 1)


class Pickup(Command):
    """Uses Pick Up once."""

    def main(self):
        press(Key.PICK_UP, 1)


class Buff(Command):
    """Uses decent skills and burst skills."""

    def __init__(self):
        super().__init__(locals())
        # 技能配置：(技能按键, CD时间)
        self.buff_config = {
            Key.bufff2: 180,
            Key.爆发1: 60,
            Key.爆发2: 120,
        }
        # 记录每个技能的上次使用时间
        self.buff_times = {key: 0 for key in self.buff_config.keys()}

    def main(self):
        now = time.time()

        # 1. 检查当前哪个爆发生效（爆发2优先于爆发1）
        burst1_active = (self.buff_times[Key.爆发1] > 0 and
                          now - self.buff_times[Key.爆发1] <= 60)
        burst2_active = (self.buff_times[Key.爆发2] > 0 and
                          now - self.buff_times[Key.爆发2] <= 60)

        # 如果爆发2激活，则爆发2生效；否则如果爆发1激活，则爆发1生效
        if burst2_active:
            burst_elapsed = now - self.buff_times[Key.爆发2]
            is_burst2 = True
        elif burst1_active:
            burst_elapsed = now - self.buff_times[Key.爆发1]
            is_burst2 = False
        else:
            # 没有爆发激活
            burst_elapsed = 0
            is_burst2 = False

        # 2. 使用独立技能
        # 优先使用爆发2，如果爆发2CD好了就用爆发2
        burst2_ready = (self.buff_times[Key.爆发2] == 0 or now - self.buff_times[Key.爆发2] > 120)
        burst1_ready = (self.buff_times[Key.爆发1] == 0 or now - self.buff_times[Key.爆发1] > 60)
        
        for skill_key, cd in self.buff_config.items():
            last_time = self.buff_times[skill_key]
            if last_time == 0 or now - last_time > cd:
                # 如果是爆发1，检查爆发2是否也准备好了
                if skill_key == Key.爆发1 and burst2_ready:
                    # 爆发2也准备好了，跳过爆发1，优先使用爆发2
                    continue
                press(skill_key, 3, up_time=0.3)
                self.buff_times[skill_key] = now



class 主攻(Command):
    """Attacks using 主攻 in a given direction (primary attack, no cd)."""

    def __init__(self, direction, attacks=2, repetitions=1):
        """初始化主攻命令
        
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
        """执行主攻攻击
        
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
            time.sleep(utils.rand_float(0.075, 0.15))
        # 按照指定的重复次数执行攻击
        for _ in range(self.repetitions):
            press(Key.主攻, self.attacks, up_time=0.05)
        # 释放方向键
        key_up(self.direction)
        # 根据攻击次数添加不同的延迟以确保攻击完成
        if self.attacks > 2:
            time.sleep(0.3)
        else:
            time.sleep(0.2)


class 感应_鬼1(Command):
    """Uses 感应_鬼1 once (12 sec cd)."""

    def main(self):
        press(Key.感应_鬼1, 2, up_time=0.05)


class 感应_鬼2(Command):
    """Uses 感应_鬼2 once (30 sec cd)."""

    def main(self):
        press(Key.感应_鬼2, 2, up_time=0.05)


class 感应_鸦1(Command):
    """Uses 感应_鸦1 once (30 sec cd)."""

    def main(self):
        press(Key.感应_鸦1, 2, up_time=0.05)


class 感应_蛇1(Command):
    """Uses 感应_蛇1 once (30 sec cd)."""

    def main(self):
        press(Key.感应_蛇1, 2, up_time=0.05)


class 大符咒(Command):
    """Uses 大符咒 once (30 sec cd)."""

    def main(self):
        press(Key.大符咒, 2, up_time=0.05)


class V_鸦(Command):
    """Uses V_鸦 once (120 sec cd)."""

    def main(self):
        press(Key.V_鸦, 3)


class V_蛇(Command):
    """Uses V_蛇 once (120 sec cd)."""

    def main(self):
        press(Key.V_蛇, 3)


class 爱尔达放置(Command):
    """Uses 爱尔达放置 once (60 sec cd, shared)."""

    def main(self):
        press(Key.爱尔达放置, 3)


class 威尔蜘蛛腿(Command):
    """Uses 威尔蜘蛛腿 once (250 sec cd)."""

    def main(self):
        press(Key.威尔蜘蛛腿, 3)


class ORIGIN(Command):
    """Uses 6th job ORIGIN skill once."""

    def main(self):
        press(Key.ORIGIN, 3)


class ASCENT(Command):
    """Uses 6th job ASCENT skill once."""

    def main(self):
        press(Key.ASCENT, 3)


class IdleSkillRotation(Command):
    """站在原地随机释放技能（不进行主攻），若技能都在cd或不符合依赖则在原地等待。"""

    def __init__(self, duration):
        super().__init__(locals())
        self.duration = settings.validate_nonnegative_int(duration)
        # 技能配置：(技能ID, 技能按键, CD时间, 爆发1窗口, 爆发2窗口)
        self.skill_config = [
            ('感应_鬼1', Key.感应_鬼1, 12, 55, 55),
            ('感应_鬼2', Key.感应_鬼2, 30, 55, 55),
            ('感应_鸦1', Key.感应_鸦1, 30, 25, 25),
            ('V_鸦', Key.V_鸦, 120, 25, 25),
            ('感应_蛇1', Key.感应_蛇1, 30, 0, 25),  # 爆发1不能用，爆发2可以用
            ('V_蛇', Key.V_蛇, 120, 0, 25),    # 爆发1不能用，爆发2可以用
            ('大符咒', Key.大符咒, 30, 0, 0),     # 不依赖爆发
        ]

    def main(self):
        import random
        import src.common.config as config
        from src.routine.cooldown_tracker import CooldownTracker
        start_time = time.time()
        end_time = start_time + self.duration

        while config.enabled and time.time() < end_time:
            now = time.time()

            # 1. 手动调用buff.main()，确保在IdleSkillRotation期间也能自动补buff
            try:
                if hasattr(config.bot, 'command_book') and hasattr(config.bot.command_book, 'buff'):
                    config.bot.command_book.buff.main()
            except Exception as e:
                print(f'[!] IdleSkillRotation调用buff失败: {e}')

            # 2. 检查当前哪个爆发生效（爆发2优先于爆发1）
            burst1_active = False
            burst2_active = False
            burst_elapsed = 0
            is_burst2 = False
            
            # 尝试获取Buff类的实例并检查爆发状态
            try:
                if hasattr(config.bot, 'command_book') and hasattr(config.bot.command_book, 'buff'):
                    buff_instance = config.bot.command_book.buff
                    if hasattr(buff_instance, 'buff_times'):
                        # 检查爆发2是否激活（优先）
                        if Key.爆发2 in buff_instance.buff_times:
                            burst2_time = buff_instance.buff_times[Key.爆发2]
                            if burst2_time > 0 and now - burst2_time <= 60:
                                burst2_active = True
                                burst_elapsed = now - burst2_time
                                is_burst2 = True
                            else:
                                burst2_active = False
                        # 如果爆发2未激活，检查爆发1
                        if not burst2_active and Key.爆发1 in buff_instance.buff_times:
                            burst1_time = buff_instance.buff_times[Key.爆发1]
                            if burst1_time > 0 and now - burst1_time <= 60:
                                burst1_active = True
                                burst_elapsed = now - burst1_time
                                is_burst2 = False
                            else:
                                burst1_active = False
                                burst_elapsed = 0
                                is_burst2 = False
                        if not burst1_active and not burst2_active:
                            burst_elapsed = 0
                            is_burst2 = False
            except Exception:
                pass

            # 3. 获取或创建冷却追踪器（与移动中的技能共享）
            module = getattr(config.bot.command_book, 'module', None) if getattr(config.bot, 'command_book', None) else None
            cooldowns = getattr(module, 'SKILL_COOLDOWNS', None) if module else None
            if cooldowns is None:
                time.sleep(0.5)
                continue
            
            tracker = getattr(config.bot, 'cooldown_tracker', None)
            if tracker is None or getattr(tracker, '_cooldowns_ref', None) is not cooldowns:
                tracker = CooldownTracker(cooldowns)
                tracker._cooldowns_ref = cooldowns
                setattr(config.bot, 'cooldown_tracker', tracker)
            
            # 获取所有冷却完毕的技能
            available_from_tracker = tracker.get_available()

            # 4. 收集所有可用的技能（根据爆发状态过滤）
            available_skills = []
            for skill_id, skill_key, cd, burst1_window, burst2_window in self.skill_config:
                # 检查冷却时间（使用CooldownTracker）
                if skill_id not in available_from_tracker:
                    continue
                
                # 检查爆发依赖
                if burst_elapsed > 0:
                    # 有爆发激活，检查是否在窗口时间内
                    window_time = burst2_window if is_burst2 else burst1_window
                    if window_time == 0:
                        available_skills.append(skill_key)
                    elif burst_elapsed <= window_time:
                        available_skills.append(skill_key)
                else:
                    # 没有爆发激活，只添加不依赖爆发的技能（窗口时间为0）
                    if burst1_window == 0 and burst2_window == 0:
                        available_skills.append(skill_key)

            # 5. 随机选择一个可用技能释放
            if available_skills:
                selected_skill = random.choice(available_skills)
                press(selected_skill, 2, up_time=0.05)
                # 记录技能使用时间（更新CooldownTracker）
                # 找到对应的技能ID
                for skill_id, skill_key, cd, burst1_window, burst2_window in self.skill_config:
                    if skill_key == selected_skill:
                        tracker.record_used(skill_id)
                        break
                time.sleep(0.5)
            else:
                time.sleep(0.5)




