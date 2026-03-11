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
    '传染': 25,
    '毒球': 25,
    '火球': 25,
    '炎魔召唤': 270,
    '炎魔爆发': 60,
    '弹球': 50,
    '毒火陨石': 10,
    '毒阵放置': 60,
    '爱尔达放置': 60,
    '终极无限1号': 180,
    '终极无限2号': 340,
    '威尔蜘蛛腿': 250,
}

# 技能轮换黑名单，这些技能不会被加入技能轮换模式
# 示例：SKILL_ROTATION_BLACKLIST = ['炎魔召唤', '终极无限2号']
SKILL_ROTATION_BLACKLIST = ['传染','毒球','火球','弹球','毒阵放置','炎魔召唤']


class Key:
    # Movement (teleport class: no double jump; use teleport to get around)
    JUMP = 'c'
    TELEPORT = 'shift'
    ROPE_LIFT = 'v'
    PICK_UP = 'z'

    # Decent skills (F1–F4), 3 min rotation
    bufff2 = 'f2'

    # Shared skills (all classes)
    爱尔达放置 = '4'              # 60 sec
    威尔蜘蛛腿 = '5' # 250 sec

    # 6th job skills
    ORIGIN = 'w'
    ASCENT = 'ctrl'

    # PMAGIC-specific skills
    主攻 = 'x'
    传染 = 's'
    毒球 = 'd'
    火球 = 'f'
    炎魔召唤 = 'f1'
    炎魔爆发 = 'alt'
    弹球 = 'r'
    毒火陨石 = 'a'
    毒阵放置 = 'q'
    终极无限1号 = '1'
    终极无限2号 = '2'


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
    """Uses decent skills (F1–F4) on 3 min rotation."""

    def __init__(self):
        super().__init__(locals())
        self.decent_buff_time = 0

    def main(self):
        decent_buffs = [
            Key.bufff2,
        ]
        DECENT_CD = 180  # 3 min
        now = time.time()
        if self.decent_buff_time == 0 or now - self.decent_buff_time > DECENT_CD:
            for key in decent_buffs:
                press(key, 3, up_time=0.3)
            self.decent_buff_time = now


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


class 传染(Command):
    """Uses 传染 once (25 sec cd)."""

    def main(self):
        press(Key.传染, 2, up_time=0.05)


class 毒球(Command):
    """Uses 毒球 once (25 sec cd)."""

    def main(self):
        press(Key.毒球, 2, up_time=0.05)


class 火球(Command):
    """Uses 火球 once (25 sec cd)."""

    def main(self):
        press(Key.火球, 2, up_time=0.05)


class 炎魔召唤(Command):
    """Uses 炎魔召唤 once (270 sec cd)."""

    def main(self):
        press(Key.炎魔召唤, 3)


class 炎魔爆发(Command):
    """Uses 炎魔爆发 once (60 sec cd)."""

    def main(self):
        press(Key.炎魔爆发, 3)


class 弹球(Command):
    """Uses 弹球 once (50 sec cd)."""

    def main(self):
        press(Key.弹球, 3)


class 毒火陨石(Command):
    """Uses 毒火陨石 once (10 sec cd)."""

    def main(self):
        press(Key.毒火陨石, 2, up_time=0.05)


class 毒阵放置(Command):
    """Uses 毒阵放置 once (10 sec cd)."""

    def main(self):
        press(Key.毒阵放置, 2, up_time=0.05)


class 爱尔达放置(Command):
    """Uses 爱尔达放置 once (60 sec cd, shared)."""

    def main(self):
        press(Key.爱尔达放置, 3)


class 终极无限1号(Command):
    """Uses 终极无限1号 once (180 sec cd)."""

    def main(self):
        press(Key.终极无限1号, 3)


class 终极无限2号(Command):
    """Uses 终极无限2号 once (360 sec cd)."""

    def main(self):
        press(Key.终极无限2号, 3)


class 威尔蜘蛛腿(Command):
    """Uses 威尔蜘蛛腿 once (250 sec cd, shared)."""

    def main(self):
        press(Key.威尔蜘蛛腿, 3)


class Origin(Command):
    """Uses Origin (6th job skill) once."""

    def main(self):
        press(Key.ORIGIN, 3)


class Ascent(Command):
    """Uses Ascent (6th job skill) once."""

    def main(self):
        press(Key.ASCENT, 3)
