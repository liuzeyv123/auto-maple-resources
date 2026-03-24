"""豹弩游侠可以使用的所有命令集合。"""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up

# 设置主攻模式tap或者hold
MAIN_ATTACK_TYPE = 'hold'

# 全局变量
down_jump_count = 0
previous_x_direction = 'right'
up_move_fail_count = 0 

# 技能冷却时间配置（按键属性名 -> 秒）。0 = 无冷却（可连续使用）。
# 使用按键属性名以便尊重用户的键位绑定。
SKILL_COOLDOWNS = {
    '主攻': 0,
    '豹子1': 20,     # 5次按键触发，然后17秒冷却
    '豹子2': 20,
    '全屏': 20,
    '大招2': 120,
    '放置': 60,
    'ERDA_SHOWER': 60,
    'TRUE_ARACHNID_REFLECTION': 250,
}
SKILL_ROTATION_BLACKLIST = ['放置','ERDA_SHOWER']

# 按键映射列表（空格 = 跳跃，z = 拾取；无alt键）
class Key:
    # 移动（闪现跳跃 = 与跳跃同一按键，多按几次）
    JUMP = 'c'
    ROPE_LIFT = 'v'
    PICK_UP = 'z'

    # buff (F1), 3 min rotation
    DECENT_SHARP_EYES = 'f1'
    # 共享技能（所有职业）
    ERDA_SHOWER = 'f'        # 60秒冷却
    TRUE_ARACHNID_REFLECTION = '5'   # 250秒冷却
    # 职业特有技能
    主攻 = 'x'   # 主要攻击，左右移动时连续使用
    豹子1 = 'a'       
    豹子2 = 's'    
    全屏 = 'e'         
    大招2 = 'w'       
    放置 = 'd'         # 放置技能，60秒冷却

    # 6转技能
    ORIGIN = '7'
    ASCENT = '8'


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
    from src.common import config
    config.executing_movement = True
    
    # 记录X轴移动方向
    if direction in ['left', 'right']:
        previous_x_direction = direction
    
    # 处理向下跳跃计数
    if direction == 'down':
        # 增加向下跳跃计数器
        down_jump_count += 1
        # print(f'向下跳跃次数: {down_jump_count}')
        
        # 如果连续执行了3次向下跳跃，向之前X轴移动的方向进行一次跳跃
        if down_jump_count >= 3:
            print(f'连续执行向下跳跃 {down_jump_count}次，向{previous_x_direction}方向跳跃')
            # 向之前X轴移动的方向跳跃并按住主攻技能
            key_down(previous_x_direction)
            time.sleep(0.1)
            key_down(Key.主攻)
            press(Key.JUMP, 1)
            time.sleep(0.3)
            key_up(Key.主攻)
            key_up(previous_x_direction)
            # 重置计数器
            down_jump_count = 0
    else:
        # 如果不是向下方向，重置计数器
        down_jump_count = 0
    
    if direction == 'up':
        global up_move_fail_count
        # 计算目标与当前位置的垂直距离
        d_y = target[1] - config.player_pos[1]
        # 记录移动前的位置
        before_pos = config.player_pos
        
        time.sleep(0.3)
        # 使用绳索升降机
        press(Key.ROPE_LIFT, 2)
        # 根据距离调整睡眠时间
        time.sleep(1.8 if abs(d_y) > 0.08 else 1)

        # 检查Y轴移动是否成功
        after_pos = config.player_pos
        if abs(after_pos[1] - before_pos[1]) < 0.02:
            # 向上移动失败，增加失败计数器
            up_move_fail_count += 1
            print(f'向上移动失败，失败次数: {up_move_fail_count}')
            # 只有连续失败两次才会触发跳跃
            if up_move_fail_count >= 2:
                import random
                random_direction = random.choice(['left', 'right'])
                print(f'向上移动连续失败{up_move_fail_count}次，尝试向{random_direction}方向跳跃')
                # 向随机方向跳跃并按住主攻技能
                key_down(random_direction)
                time.sleep(0.1)
                key_down(Key.主攻)
                press(Key.JUMP, 2)
                time.sleep(0.2)
                key_up(Key.主攻)
                key_up(previous_x_direction)
                # 重置失败计数器
                up_move_fail_count = 0
        else:
            # 向上移动成功，重置失败计数器
            up_move_fail_count = 0
        return

    # 默认为2次跳跃（闪现跳跃）
    num_presses = 2
    # 向下方向只需要1次跳跃
    if direction == 'down':
        # print('step的向下跳跃1次')
        num_presses = 1
    # 如果启用了stage_fright且有75%的概率，添加随机延迟以模拟人类操作
    if config.stage_fright and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.075, 0.15))
    
    # 左右移动时持续按住主攻技能（不跳跃）
    if direction in ['left', 'right']:
        key_down(direction)
        time.sleep(0.05)
        key_down(Key.主攻)
        time.sleep(0.6)
        key_up(Key.主攻)
        key_up(direction)
    # 向下移动时持续按住主攻技能
    elif direction == 'down':
        time.sleep(0.05)
        key_down(Key.主攻)
        press(Key.JUMP, num_presses)
        time.sleep(0.6)
        key_up(Key.主攻)
    
    time.sleep(0.05)
    config.executing_movement = False


class Adjust(Command):
    """使用小幅度移动微调玩家位置。"""

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
    """Decent技能（3分钟）和豹弩的120秒 buff。"""

    def __init__(self):
        super().__init__(locals())
        self.decent_buff_time = 0
        self.cd120_time = 0

    def main(self):
        decent_buffs = [
            Key.DECENT_SHARP_EYES,
        ]
        DECENT_CD = 180  # 3 min
        now = time.time()

        if self.decent_buff_time == 0 or now - self.decent_buff_time > DECENT_CD:
            for key in decent_buffs:
                press(key, 3, up_time=0.3)
            self.decent_buff_time = now


class FlashJump(Command):
    """向指定方向执行闪现跳跃（跳跃键，按2次）。向上：仅使用绳索升降。"""

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


class ZhuGong(Command):
    """向指定方向使用主攻（x键，按住）。"""

    def __init__(self, direction, duration=0.5):
        super().__init__(locals())
        self.direction = settings.validate_horizontal_arrows(direction)
        self.duration = float(duration)

    def main(self):
        time.sleep(0.05)
        key_down(self.direction)
        time.sleep(0.05)
        if config.stage_fright and utils.bernoulli(0.7):
            time.sleep(utils.rand_float(0.1, 0.3))
        key_down(Key.主攻)
        time.sleep(self.duration)
        key_up(Key.主攻)
        key_up(self.direction)
        time.sleep(0.2)


class BaoZi1(Command):
    """使用豹子1,20秒冷却。"""

    def main(self):
        press(Key.豹子1, 1, down_time=0.1, up_time=0.1)


class BaoZi2(Command):
    """使用豹子2一次。"""

    def main(self):
        press(Key.豹子2, 2)


class QuanPing(Command):
    """使用全屏一次。"""

    def main(self):
        press(Key.全屏, 2)


class DaZhao2(Command):
    """使用大招2一次。"""

    def main(self):
        press(Key.大招2, 2)

class FangZhi(Command):
    """使用放置一次。"""
    def __init__(self, direction):
        super().__init__(locals())
        self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        press(self.direction, 1)
        time.sleep(0.1)
        press(Key.放置, 3)


class ErdaShower(Command):
    """使用Erda Shower一次（60秒冷却）。"""

    def main(self):
        press(Key.ERDA_SHOWER, 3)


class TrueArachnidReflection(Command):
    """使用True Arachnid Reflection一次（250秒冷却）。"""

    def main(self):
        press(Key.TRUE_ARACHNID_REFLECTION, 3)


class Origin(Command):
    """使用Origin（6转技能）一次。"""

    def main(self):
        press(Key.ORIGIN, 3)


class Ascent(Command):
    """使用Ascent（6转技能）一次。"""

    def main(self):
        press(Key.ASCENT, 3)


