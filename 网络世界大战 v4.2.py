import pygame
import random
import sys
import time
import math

# 初始化Pygame
pygame.init()
pygame.font.init()

# 基础配置参数
DEFAULT_RES = (1200, 800)
MAP_SIZE = 20  # 20x20地图网格
CELL_SIZE = 35  # 单个格子大小
RESOLUTIONS = {
    "800x600": (800, 600),
    "1200x800": (1200, 800),
    "1920x1080": (1920, 1080)
}
FRAMES = [30, 60, 120]
AI_DIFFICULTIES = ["简单", "普通", "困难"]

# 颜色定义
COLORS = {
    "我的世界": (50, 150, 255),       # 蓝色
    "我的世界浅": (100, 180, 255),    # 浅蓝色（我的世界边境）
    "我的世界防御": (180, 100, 255),  # 紫色（我的世界防御）
    "迷你世界": (255, 80, 80),        # 红色
    "迷你世界浅": (255, 120, 120),    # 浅红色（迷你世界边境）
    "迷你世界防御": (255, 165, 0),    # 橙色（迷你世界防御）
    "中立": (200, 200, 200),          # 灰色
    "共同边境": (100, 255, 100),      # 浅绿色（共同边境）
    "防御中": (100, 255, 100),        # 绿色（防御状态）
    "观察者": (150, 150, 150),        # 深灰色
    "进度条底": (180, 180, 180),      # 进度条背景
    "文字": (0, 0, 0),                # 黑色文字
    "文字白": (255, 255, 255),        # 白色文字
    "按钮": (180, 180, 180),          # 按钮颜色
    "按钮悬停": (200, 200, 200),      # 按钮悬停颜色
    "胜利背景": (240, 240, 240),      # 胜利界面背景
    "重来按钮": (100, 200, 100),      # 重来按钮颜色
    "返回按钮": (200, 100, 100)       # 返回按钮颜色
}

# 游戏状态枚举
class GameState:
    SETTINGS = 0      # 设置界面
    CAMP_SELECT = 1   # 阵营选择
    DIFFICULTY_SELECT = 2  # AI难度选择
    BATTLE = 3        # 战斗中（事件前）
    EVENT = 4         # 萨拉热窝事件触发
    FULL_BATTLE = 5   # 全屏占领后对抗
    VICTORY = 6       # 胜利界面
    LAWSUIT = 7       # 官司胜利界面

# 阵营数据类
class Faction:
    def __init__(self, name, color, defense_color):
        self.name = name
        self.color = color
        self.defense_color = defense_color
        self.morale = 50  # 初始士气（0-100）
        self.territory = 0  # 领土数量
        self.defense_count = 0  # 防御成功次数
        self.surrender = 0  # 投降值（0-100）
        self.territory_percent = 0  # 领土占比（%）
        self.defense_cells = set()  # 防御格子

# 游戏主类
class Game:
    def __init__(self):
        # 设置参数
        self.resolution = "1200x800"
        self.fps = 60
        self.fullscreen = False
        self.screen = pygame.display.set_mode(RESOLUTIONS[self.resolution], pygame.RESIZABLE)
        pygame.display.set_caption("中国游戏界第一次网络大战")
        self.clock = pygame.time.Clock()

        # 游戏状态
        self.state = GameState.SETTINGS
        self.player_camp = ""  # 玩家阵营
        self.ai_difficulty = "普通"  # AI难度
        self.event_triggered = False  # 萨拉热窝事件是否触发
        self.full_territory = False  # 是否双方已占领全屏
        self.victor = None  # 胜利者
        self.last_morale_regen = time.time()  # 上次士气恢复时间
        self.lawsuit_triggered = False  # 官司是否触发
        self.lawsuit_time = 0  # 官司触发时间

        # 初始化阵营
        self.mc = Faction("我的世界", COLORS["我的世界"], COLORS["我的世界防御"])
        self.mini = Faction("迷你世界", COLORS["迷你世界"], COLORS["迷你世界防御"])
        self.factions = [self.mc, self.mini]

        # 地图数据（0=中立，1=我的世界，2=迷你世界）
        self.map = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        self.init_map()  # 初始化地图边缘领地

        # 边境与防御数据
        self.mc_border = []  # 我的世界边境格子
        self.mini_border = []  # 迷你世界边境格子
        self.common_border = []  # 共同边境格子

        # AI计时器
        self.ai_timer_mc = 0
        self.ai_timer_mini = 0
        self.ai_action_interval = 60  # AI行动间隔（帧数）

        # 字体初始化（支持中文）
        try:
            self.font = pygame.font.SysFont("simhei", 24)
            self.small_font = pygame.font.SysFont("simhei", 18)
            self.title_font = pygame.font.SysFont("simhei", 36)
            self.big_font = pygame.font.SysFont("simhei", 48)
        except:
            self.font = pygame.font.SysFont(None, 24)
            self.small_font = pygame.font.SysFont(None, 18)
            self.title_font = pygame.font.SysFont(None, 36)
            self.big_font = pygame.font.SysFont(None, 48)

    def init_map(self):
        """初始化地图：随机分配6个起始领地"""
        # 清空地图
        self.map = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        
        # 随机选择6个起始位置
        all_cells = [(i, j) for i in range(MAP_SIZE) for j in range(MAP_SIZE)]
        
        # 我的世界初始领地
        mc_start = random.sample(all_cells, 6)
        for i, j in mc_start:
            self.map[i][j] = 1
            
        # 迷你世界初始领地（确保不重叠）
        remaining_cells = [cell for cell in all_cells if cell not in mc_start]
        mini_start = random.sample(remaining_cells, 6)
        for i, j in mini_start:
            self.map[i][j] = 2
            
        # 清空防御格子
        self.mc.defense_cells = set()
        self.mini.defense_cells = set()
        
        self.update_territory()  # 更新领土数据

    def reset_game(self):
        """重置游戏"""
        self.event_triggered = False
        self.full_territory = False
        self.victor = None
        self.lawsuit_triggered = False
        self.mc.morale = 50
        self.mini.morale = 50
        self.mc.territory = 0
        self.mini.territory = 0
        self.mc.defense_count = 0
        self.mini.defense_count = 0
        self.mc.surrender = 0
        self.mini.surrender = 0
        self.init_map()

    def apply_settings(self):
        """应用分辨率和全屏设置"""
        w, h = RESOLUTIONS[self.resolution]
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode((w, h), flags | pygame.RESIZABLE)

    def toggle_fullscreen(self):
        """切换全屏/窗口模式"""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(RESOLUTIONS[self.resolution], pygame.RESIZABLE)

    def update_border(self):
        """更新边境格子（己方与非己方相邻的格子）"""
        self.mc_border = []
        self.mini_border = []
        self.common_border = []
        
        for x in range(MAP_SIZE):
            for y in range(MAP_SIZE):
                # 我的世界边境：非己方格子且与己方相邻
                if self.map[x][y] != 1:
                    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nx, ny = x+dx, y+dy
                        if 0<=nx<MAP_SIZE and 0<=ny<MAP_SIZE and self.map[nx][ny] == 1:
                            if (x, y) not in self.mc_border:
                                self.mc_border.append((x, y))
                # 迷你世界边境：非己方格子且与己方相邻
                if self.map[x][y] != 2:
                    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nx, ny = x+dx, y+dy
                        if 0<=nx<MAP_SIZE and 0<=ny<MAP_SIZE and self.map[nx][ny] == 2:
                            if (x, y) not in self.mini_border:
                                self.mini_border.append((x, y))
        
        # 找出共同边境格子
        self.common_border = [cell for cell in self.mc_border if cell in self.mini_border]

    def update_territory(self):
        """更新领土数量和占比，同时检查是否触发事件或胜利"""
        total = MAP_SIZE * MAP_SIZE
        self.mc.territory = sum(row.count(1) for row in self.map)
        self.mini.territory = sum(row.count(2) for row in self.map)
        self.mc.territory_percent = round(self.mc.territory / total * 100, 1)
        self.mini.territory_percent = round(self.mini.territory / total * 100, 1)
        
        # 检查胜利条件
        if self.mc.territory_percent >= 100:
            self.victor = self.mc
            self.state = GameState.VICTORY
            return
        elif self.mini.territory_percent >= 100:
            self.victor = self.mini
            self.state = GameState.VICTORY
            return

        # 检查是否触发萨拉热窝事件（任意一方领土超过25%）
        if not self.event_triggered and (
            self.mc.territory_percent >= 25 or 
            self.mini.territory_percent >= 25
        ):
            self.event_triggered = True
            self.state = GameState.EVENT
            self.event_start_time = time.time()
            self.lawsuit_time = time.time()  # 开始计时官司

        # 检查是否双方已占领全屏（中立格子<5%）
        neutral = total - self.mc.territory - self.mini.territory
        if neutral / total < 0.05 and not self.full_territory:
            self.full_territory = True
            if self.event_triggered:
                self.state = GameState.FULL_BATTLE

    def check_lawsuit(self):
        """检查是否触发官司胜利"""
        if (self.event_triggered and not self.lawsuit_triggered and 
            time.time() - self.lawsuit_time >= 15 and
            self.mc.territory_percent < 15):
            
            self.lawsuit_triggered = True
            
            # 计算迷你世界15%的领土数量（基于迷你世界已占领的领土）
            mini_owned_territory = self.mini.territory
            target_cells = int(mini_owned_territory * 0.15)
            
            # 获取所有迷你世界领土（包括防御领土）
            mini_territory = []
            for x in range(MAP_SIZE):
                for y in range(MAP_SIZE):
                    if self.map[x][y] == 2:
                        mini_territory.append((x, y))
            
            # 随机选择15%的迷你世界领土转给我的世界
            if len(mini_territory) > 0:
                cells_to_transfer = min(target_cells, len(mini_territory))
                transfer_cells = random.sample(mini_territory, cells_to_transfer)
                
                for x, y in transfer_cells:
                    self.map[x][y] = 1  # 转给我的世界
                    # 如果这些格子是防御格子，移除防御状态
                    if (x, y) in self.mini.defense_cells:
                        self.mini.defense_cells.remove((x, y))
                
                self.update_territory()
                self.state = GameState.LAWSUIT

    def player_attack(self, x, y):
        """玩家攻占边境格子（仅非观察者阵营）"""
        if self.player_camp not in ["我的世界", "迷你世界"]:
            return False
            
        camp = 1 if self.player_camp == "我的世界" else 2
        target_border = self.mc_border if camp == 1 else self.mini_border
        
        if (x, y) not in target_border:
            return False  # 非边境格子，无法攻占
            
        # 未触发事件前，不能攻击对方已占领的格子
        if not self.event_triggered and self.map[x][y] != 0:
            return False
            
        # 检查士气是否足够
        faction = self.mc if camp == 1 else self.mini
        
        # 根据攻击目标类型决定士气消耗
        morale_cost = 5 if self.map[x][y] == 0 else 10
        
        if faction.morale < morale_cost:
            return False
            
        # 消耗士气
        faction.morale = max(0, faction.morale - morale_cost)
        

        # 攻占成功率（受士气影响）
        success_rate = 0.7 + (faction.morale / 100 * 0.2)
        if random.random() < success_rate:
            # 检查是否被防御
            enemy_faction = self.mini if camp == 1 else self.mc
            if (x, y) in enemy_faction.defense_cells:
                # 防御成功
                enemy_faction.defense_count += 1
                enemy_faction.morale = min(100, enemy_faction.morale + 2)
                if enemy_faction.defense_count % 7 == 0:
                    enemy_faction.morale = min(100, enemy_faction.morale + 10)
                enemy_faction.defense_cells.remove((x, y))  # 防御被消耗
                return True
                
            # 攻占成功
            self.map[x][y] = camp
            self.update_territory()
            faction.morale = min(100, faction.morale + 3)
            # 全屏阶段更新投降值
            if self.full_territory:
                enemy_faction.surrender = min(100, enemy_faction.surrender + 5)
            return True
        return False

    def player_defend(self, x, y):
        """玩家设置防御格子（右键点击己方领土）"""
        if self.player_camp not in ["我的世界", "迷你世界"]:
            return False
            
        camp = 1 if self.player_camp == "我的世界" else 2
        if self.map[x][y] != camp:
            return False  # 非己方格子
            
        faction = self.mc if camp == 1 else self.mini
        
        # 切换防御状态
        if (x, y) in faction.defense_cells:
            faction.defense_cells.remove((x, y))
        else:
            faction.defense_cells.add((x, y))
        return True

    def update_morale(self):
        """每秒恢复5点士气"""
        current_time = time.time()
        if current_time - self.last_morale_regen >= 1.0:  # 每秒恢复
            self.last_morale_regen = current_time
            for faction in self.factions:
                faction.morale = min(100, faction.morale + 5)

    def get_ai_success_rate(self, faction):
        """根据AI难度获取成功率"""
        base_rate = 0.6
        if self.ai_difficulty == "简单":
            base_rate = 0.5
        elif self.ai_difficulty == "困难":
            base_rate = 0.7
            
        # 事件触发后成功率提升
        if self.event_triggered:
            base_rate += 0.1
            
        # 士气影响
        return base_rate + (faction.morale / 100 * 0.2)

    def get_ai_action_interval(self):
        """根据AI难度获取行动间隔"""
        if self.ai_difficulty == "简单":
            return 90  # 1.5秒（60FPS）
        elif self.ai_difficulty == "普通":
            return 60  # 1秒
        elif self.ai_difficulty == "困难":
            return 30  # 0.5秒

    def ai_attack(self, faction, border_cells, enemy_faction):
        """AI攻击逻辑"""
        if not border_cells:
            return
            
        target = random.choice(border_cells)
        x, y = target
        
        # 未触发事件前，不能攻击对方已占领的格子
        if not self.event_triggered and self.map[x][y] != 0:
            return
            
        # 根据攻击目标类型决定士气消耗
        morale_cost = 5 if self.map[x][y] == 0 else 10
            
        if faction.morale < morale_cost:
            return
            
        # 消耗士气
        faction.morale = max(0, faction.morale - morale_cost)
            
        success_rate = self.get_ai_success_rate(faction)
        if random.random() < success_rate:
            # 检查是否被防御
            if (x, y) in enemy_faction.defense_cells:
                # 防御成功
                enemy_faction.defense_count += 1
                enemy_faction.morale = min(100, enemy_faction.morale + 2)
                if enemy_faction.defense_count % 7 == 0:
                    enemy_faction.morale = min(100, enemy_faction.morale + 10)
                enemy_faction.defense_cells.remove((x, y))  # 防御被消耗
                return

            # 攻占成功
            faction_id = 1 if faction.name == "我的世界" else 2
            self.map[x][y] = faction_id
            self.update_territory()
            faction.morale = min(100, faction.morale + 3)
            # 全屏阶段更新投降值
            if self.full_territory:
                enemy_faction.surrender = min(100, enemy_faction.surrender + 5)

    def ai_defend(self, faction):
        """AI防御逻辑"""
        # 获取己方领土
        own_territory = []
        for x in range(MAP_SIZE):
            for y in range(MAP_SIZE):
                if (faction.name == "我的世界" and self.map[x][y] == 1) or \
                   (faction.name == "迷你世界" and self.map[x][y] == 2):
                    own_territory.append((x, y))
        
        # 如果有边境领土，随机选择一些设置防御
        if own_territory:
            # 计算需要防御的格子数量（最多5个）
            defense_count = min(5, len(own_territory))
            defense_cells = random.sample(own_territory, defense_count)
            
            # 设置防御
            for cell in defense_cells:
                faction.defense_cells.add(cell)

    def ai_action(self):
        """AI行动逻辑"""
        # 更新行动间隔
        self.ai_action_interval = self.get_ai_action_interval()
        
        # 我的世界AI行动（当玩家不是我的世界或者观察者模式时）
        if self.player_camp != "我的世界":
            self.ai_timer_mc += 1
            if self.ai_timer_mc >= self.ai_action_interval:
                self.ai_attack(self.mc, self.mc_border, self.mini)
                # 每隔一段时间设置防御
                if random.random() < 0.2:  # 20%的概率设置防御
                    self.ai_defend(self.mc)
                self.ai_timer_mc = 0
                
        # 迷你世界AI行动（当玩家不是迷你世界或者观察者模式时）
        if self.player_camp != "迷你世界":
            self.ai_timer_mini += 1
            if self.ai_timer_mini >= self.ai_action_interval:
                self.ai_attack(self.mini, self.mini_border, self.mc)
                # 每隔一段时间设置防御
                if random.random() < 0.2:  # 20%的概率设置防御
                    self.ai_defend(self.mini)
                self.ai_timer_mini = 0

    def draw_settings(self):
        """绘制设置界面"""
        self.screen.fill((240, 240, 240))
        w, h = self.screen.get_size()

        # 标题
        title = self.title_font.render("游戏设置", True, COLORS["文字"])
        self.screen.blit(title, (w//2 - title.get_width()//2, 50))

        # 开发者信息
        developer_text = self.small_font.render("开发者：LK", True, COLORS["文字"])
        self.screen.blit(developer_text, (w//2 - developer_text.get_width()//2, 120))

        # 分辨率选择
        res_label = self.font.render("选择分辨率:", True, COLORS["文字"])
        self.screen.blit(res_label, (w//2 - 200, 150))
        res_y = 200
        for res in RESOLUTIONS.keys():
            rect = pygame.Rect(w//2 - 150, res_y, 300, 40)
            color = COLORS["我的世界浅"] if res == self.resolution else COLORS["进度条底"]
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, COLORS["文字"], rect, 2)  # 边框
            text = self.font.render(res, True, COLORS["文字"])
            self.screen.blit(text, (rect.x + 10, rect.y + 10))
            res_y += 60

        # 帧率选择
        fps_label = self.font.render("选择帧率(FPS):", True, COLORS["文字"])
        self.screen.blit(fps_label, (w//2 - 200, 400))
        fps_y = 450
        for fps in FRAMES:
            rect = pygame.Rect(w//2 - 100 + (FRAMES.index(fps)*150), fps_y, 120, 40)
            color = COLORS["我的世界浅"] if fps == self.fps else COLORS["进度条底"]
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, COLORS["文字"], rect, 2)
            text = self.font.render(f"{fps}", True, COLORS["文字"])
            self.screen.blit(text, (rect.x + 10, rect.y + 10))

        # 全屏切换
        full_rect = pygame.Rect(w//2 - 150, 520, 300, 40)
        full_text = "全屏模式: 开启" if self.fullscreen else "全屏模式: 关闭"
        pygame.draw.rect(self.screen, COLORS["我的世界浅"] if self.fullscreen else COLORS["进度条底"], full_rect)
        pygame.draw.rect(self.screen, COLORS["文字"], full_rect, 2)
        text = self.font.render(full_text, True, COLORS["文字"])
        self.screen.blit(text, (full_rect.x + 10, full_rect.y + 10))

        # 确认按钮
        confirm_rect = pygame.Rect(w//2 - 100, h - 100, 200, 50)
        pygame.draw.rect(self.screen, COLORS["我的世界"], confirm_rect)
        text = self.font.render("确认设置", True, COLORS["文字白"])
        self.screen.blit(text, (confirm_rect.x + 30, confirm_rect.y + 15))

        pygame.display.flip()

    def draw_camp_select(self):
        """绘制阵营选择界面"""
        self.screen.fill((240, 240, 240))
        w, h = self.screen.get_size()

        title = self.title_font.render("选择阵营", True, COLORS["文字"])
        self.screen.blit(title, (w//2 - title.get_width()//2, 100))

        # 阵营选项
        camps = [
            ("我的世界", COLORS["我的世界"], w//2 - 200, 250),
            ("迷你世界", COLORS["迷你世界"], w//2 - 200, 350),
            ("观察者", COLORS["观察者"], w//2 - 200, 450)
        ]
        
        for name, color, x, y in camps:
            rect = pygame.Rect(x, y, 300, 60)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
            text = self.font.render(name, True, COLORS["文字白"])
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

        # 返回按钮
        back_rect = pygame.Rect(50, h - 100, 150, 50)
        pygame.draw.rect(self.screen, COLORS["返回按钮"], back_rect)
        text = self.font.render("返回", True, COLORS["文字白"])
        self.screen.blit(text, (back_rect.x + 50, back_rect.y + 15))

        pygame.display.flip()

    def draw_difficulty_select(self):
        """绘制AI难度选择界面"""
        self.screen.fill((240, 240, 240))
        w, h = self.screen.get_size()

        title = self.title_font.render("选择AI难度", True, COLORS["文字"])
        self.screen.blit(title, (w//2 - title.get_width()//2, 100))

        # 难度选项
        diff_y = 250
        for difficulty in AI_DIFFICULTIES:
            rect = pygame.Rect(w//2 - 150, diff_y, 300, 60)
            color = COLORS["我的世界浅"] if difficulty == self.ai_difficulty else COLORS["进度条底"]
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
            text = self.font.render(difficulty, True, COLORS["文字"])
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)
            diff_y += 100

        # 确认按钮
        confirm_rect = pygame.Rect(w//2 - 100, h - 100, 200, 50)
        pygame.draw.rect(self.screen, COLORS["我的世界"], confirm_rect)
        text = self.font.render("确认", True, COLORS["文字白"])
        self.screen.blit(text, (confirm_rect.x + 80, confirm_rect.y + 15))

        # 返回按钮
        back_rect = pygame.Rect(50, h - 100, 150, 50)
        pygame.draw.rect(self.screen, COLORS["返回按钮"], back_rect)
        text = self.font.render("返回", True, COLORS["文字白"])
        self.screen.blit(text, (back_rect.x + 50, back_rect.y + 15))

        pygame.display.flip()

    def draw_battle(self):
        """绘制战斗界面"""
        self.screen.fill((240, 240, 240))
        w, h = self.screen.get_size()
        map_width = MAP_SIZE * CELL_SIZE
        map_height = MAP_SIZE * CELL_SIZE
        map_x = (w - map_width) // 2
        map_y = 50

        # 更新边境数据
        self.update_border()

        # 绘制地图网格
        for x in range(MAP_SIZE):
            for y in range(MAP_SIZE):
                cell_rect = pygame.Rect(
                    map_x + y * CELL_SIZE,
                    map_y + x * CELL_SIZE,
                    CELL_SIZE - 1,
                    CELL_SIZE - 1
                )
                # 格子颜色逻辑
                if self.map[x][y] == 1:
                    if (x, y) in self.mc.defense_cells:
                        color = COLORS["我的世界防御"]  # 紫色防御
                    else:
                        color = COLORS["我的世界"]
                elif self.map[x][y] == 2:
                    if (x, y) in self.mini.defense_cells:
                        color = COLORS["迷你世界防御"]  # 橙色防御
                    else:
                        color = COLORS["迷你世界"]
                else:
                    color = COLORS["中立"]
                pygame.draw.rect(self.screen, color, cell_rect)
                
                # 绘制边境格子（覆盖在原有格子上）
                if (x, y) in self.common_border:
                    # 共同边境 - 浅绿色
                    border_color = COLORS["共同边境"]
                    pygame.draw.rect(self.screen, border_color, 
                                    (cell_rect.x + 5, cell_rect.y + 5, 
                                     CELL_SIZE - 11, CELL_SIZE - 11))
                elif (x, y) in self.mc_border:
                    # 我的世界边境 - 浅蓝色
                    border_color = COLORS["我的世界浅"]
                    pygame.draw.rect(self.screen, border_color, 
                                    (cell_rect.x + 5, cell_rect.y + 5, 
                                     CELL_SIZE - 11, CELL_SIZE - 11))
                elif (x, y) in self.mini_border:
                    # 迷你世界边境 - 浅红色
                    border_color = COLORS["迷你世界浅"]
                    pygame.draw.rect(self.screen, border_color, 
                                    (cell_rect.x + 5, cell_rect.y + 5, 
                                     CELL_SIZE - 11, CELL_SIZE - 11))

        # 关键调整：迷你方玩家显示事件触发按钮（未触发时）
        if self.player_camp == "迷你世界" and not self.event_triggered:
            trigger_btn = pygame.Rect(w - 200, 50, 150, 40)
            pygame.draw.rect(self.screen, (255, 150, 0), trigger_btn)
            pygame.draw.rect(self.screen, (0, 0, 0), trigger_btn, 2)
            btn_text = self.small_font.render("触发萨拉热窝事件", True, COLORS["文字白"])
            self.screen.blit(btn_text, (trigger_btn.x + 10, trigger_btn.y + 10))

        # 绘制数据面板
        panel_y = map_y + map_height + 30

        # 我的世界数据
        mc_label = self.font.render(f"{self.mc.name}", True, self.mc.color)
        self.screen.blit(mc_label, (50, panel_y))
        pygame.draw.rect(self.screen, COLORS["进度条底"], (50, panel_y + 30, 300, 25))
        pygame.draw.rect(self.screen, self.mc.color, (50, panel_y + 30, self.mc.morale * 3, 25))
        morale_text = self.small_font.render(f"士气: {int(self.mc.morale)}", True, COLORS["文字"])
        self.screen.blit(morale_text, (50 + 310, panel_y + 30))
        territory_text = self.small_font.render(f"领土占比: {self.mc.territory_percent}%", True, COLORS["文字"])
        self.screen.blit(territory_text, (50, panel_y + 60))

        # 迷你世界数据（往左移动）
        mini_label = self.font.render(f"{self.mini.name}", True, self.mini.color)
        self.screen.blit(mini_label, (w - 400, panel_y))  # 向左移动50像素
        pygame.draw.rect(self.screen, COLORS["进度条底"], (w - 400, panel_y + 30, 300, 25))
        pygame.draw.rect(self.screen, self.mini.color, (w - 400, panel_y + 30, self.mini.morale * 3, 25))
        morale_text = self.small_font.render(f"士气: {int(self.mini.morale)}", True, COLORS["文字"])
        self.screen.blit(morale_text, (w - 400 + 310, panel_y + 30))
        territory_text = self.small_font.render(f"领土占比: {self.mini.territory_percent}%", True, COLORS["文字"])
        self.screen.blit(territory_text, (w - 400, panel_y + 60))

        # 显示当前AI难度（观察者模式）
        if self.player_camp == "观察者":
            diff_text = self.small_font.render(f"AI难度: {self.ai_difficulty}", True, COLORS["文字"])
            self.screen.blit(diff_text, (w//2 - diff_text.get_width()//2, panel_y + 90))

        # 添加重来和返回按钮
        restart_rect = pygame.Rect(w - 250, h - 60, 100, 40)
        pygame.draw.rect(self.screen, COLORS["重来按钮"], restart_rect)
        restart_text = self.small_font.render("重来", True, COLORS["文字"])
        self.screen.blit(restart_text, (restart_rect.x + 30, restart_rect.y + 12))

        back_rect = pygame.Rect(w - 130, h - 60, 100, 40)
        pygame.draw.rect(self.screen, COLORS["返回按钮"], back_rect)
        back_text = self.small_font.render("返回", True, COLORS["文字"])
        self.screen.blit(back_text, (back_rect.x + 30, back_rect.y + 12))

        pygame.display.flip()

    def draw_event(self):
        """绘制事件界面"""
        self.screen.fill((240, 240, 240))
        w, h = self.screen.get_size()
        
        # 显示事件信息
        title = self.title_font.render("萨拉热窝事件已触发！", True, COLORS["文字"])
        self.screen.blit(title, (w//2 - title.get_width()//2, h//2 - 50))
        
        # 显示倒计时
        elapsed = time.time() - self.event_start_time
        countdown = max(0, 5 - int(elapsed))
        countdown_text = self.font.render(f"战斗将在 {countdown} 秒后恢复", True, COLORS["文字"])
        self.screen.blit(countdown_text, (w//2 - countdown_text.get_width()//2, h//2 + 20))
        
        pygame.display.flip()
        
        # 5秒后返回战斗状态
        if elapsed >= 5:
            self.state = GameState.BATTLE

    def draw_victory(self):
        """绘制胜利界面"""
        self.screen.fill(COLORS["胜利背景"])
        w, h = self.screen.get_size()
        
        # 显示胜利信息
        if self.victor:
            title = self.big_font.render(f"{self.victor.name} 获得胜利！", True, self.victor.color)
            self.screen.blit(title, (w//2 - title.get_width()//2, h//2 - 50))
        
        # 返回主界面按钮
        back_rect = pygame.Rect(w//2 - 100, h//2 + 50, 200, 50)
        pygame.draw.rect(self.screen, COLORS["我的世界"], back_rect)
        text = self.font.render("返回主界面", True, COLORS["文字白"])
        self.screen.blit(text, (back_rect.x + 40, back_rect.y + 15))
        
        pygame.display.flip()

    def draw_lawsuit(self):
        """绘制官司胜利界面"""
        self.screen.fill(COLORS["胜利背景"])
        w, h = self.screen.get_size()
        
        # 显示官司胜利信息
        title = self.big_font.render("官司胜利！", True, COLORS["我的世界"])
        self.screen.blit(title, (w//2 - title.get_width()//2, h//2 - 50))
        
        info = self.font.render("我的世界获得迷你世界15%的领土", True, COLORS["文字"])
        self.screen.blit(info, (w//2 - info.get_width()//2, h//2))
        
        # 继续游戏按钮
        continue_rect = pygame.Rect(w//2 - 100, h//2 + 50, 200, 50)
        pygame.draw.rect(self.screen, COLORS["我的世界"], continue_rect)
        text = self.font.render("继续游戏", True, COLORS["文字白"])
        self.screen.blit(text, (continue_rect.x + 50, continue_rect.y + 15))
        
        pygame.display.flip()

    def handle_click(self, pos):
        """处理鼠标点击事件"""
        x, y = pos
        w, h = self.screen.get_size()

        if self.state == GameState.SETTINGS:
            # 分辨率选择
            res_y = 200
            for res in RESOLUTIONS.keys():
                rect = pygame.Rect(w//2 - 150, res_y, 300, 40)
                if rect.collidepoint(x, y):
                    self.resolution = res
                res_y += 60

            # 帧率选择
            fps_y = 450
            for fps in FRAMES:
                rect = pygame.Rect(w//2 - 100 + (FRAMES.index(fps)*150), fps_y, 120, 40)
                if rect.collidepoint(x, y):
                    self.fps = fps
            
            # 全屏切换
            full_rect = pygame.Rect(w//2 - 150, 520, 300, 40)
            if full_rect.collidepoint(x, y):
                self.toggle_fullscreen()
            
            # 确认按钮
            confirm_rect = pygame.Rect(w//2 - 100, h - 100, 200, 50)
            if confirm_rect.collidepoint(x, y):
                self.apply_settings()
                self.state = GameState.CAMP_SELECT

        elif self.state == GameState.CAMP_SELECT:
            # 阵营选择
            camps = [
                ("我的世界", w//2 - 200, 250, 300, 60),
                ("迷你世界", w//2 - 200, 350, 300, 60),
                ("观察者", w//2 - 200, 450, 300, 60)
            ]
            for name, x_pos, y_pos, width, height in camps:
                rect = pygame.Rect(x_pos, y_pos, width, height)
                if rect.collidepoint(x, y):
                    self.player_camp = name
                    self.reset_game()
                    # 如果选择了观察者模式，直接进入战斗
                    if name == "观察者":
                        self.state = GameState.BATTLE
                    else:
                        self.state = GameState.DIFFICULTY_SELECT
            
            # 返回按钮
            back_rect = pygame.Rect(50, h - 100, 150, 50)
            if back_rect.collidepoint(x, y):
                self.state = GameState.SETTINGS

        elif self.state == GameState.DIFFICULTY_SELECT:
            # AI难度选择
            diff_y = 250
            for difficulty in AI_DIFFICULTIES:
                rect = pygame.Rect(w//2 - 150, diff_y, 300, 60)
                if rect.collidepoint(x, y):
                    self.ai_difficulty = difficulty
                diff_y += 100
            
            # 确认按钮
            confirm_rect = pygame.Rect(w//2 - 100, h - 100, 200, 50)
            if confirm_rect.collidepoint(x, y):
                self.state = GameState.BATTLE
            
            # 返回按钮
            back_rect = pygame.Rect(50, h - 100, 150, 50)
            if back_rect.collidepoint(x, y):
                self.state = GameState.CAMP_SELECT

        elif self.state in [GameState.BATTLE, GameState.FULL_BATTLE]:
            # 迷你世界事件触发按钮
            if self.player_camp == "迷你世界" and not self.event_triggered:
                trigger_btn = pygame.Rect(w - 200, 50, 150, 40)
                if trigger_btn.collidepoint(x, y):
                    self.event_triggered = True
                    self.state = GameState.EVENT
                    self.event_start_time = time.time()
                    self.lawsuit_time = time.time()
                    return

            # 地图点击处理
            map_width = MAP_SIZE * CELL_SIZE
            map_height = MAP_SIZE * CELL_SIZE
            map_x = (w - map_width) // 2
            map_y = 50
            
            if map_x <= x <= map_x + map_width and map_y <= y <= map_y + map_height:
                grid_x = (y - map_y) // CELL_SIZE
                grid_y = (x - map_x) // CELL_SIZE
                if 0 <= grid_x < MAP_SIZE and 0 <= grid_y < MAP_SIZE:
                    # 获取鼠标按钮
                    mouse_buttons = pygame.mouse.get_pressed()
                    if mouse_buttons[2]:  # 右键点击设置防御
                        self.player_defend(grid_x, grid_y)
                    else:  # 左键点击攻击
                        self.player_attack(grid_x, grid_y)

            # 重来按钮
            restart_rect = pygame.Rect(w - 250, h - 60, 100, 40)
            if restart_rect.collidepoint(x, y):
                self.reset_game()
                if self.player_camp == "观察者":
                    self.state = GameState.BATTLE
                else:
                    self.state = GameState.DIFFICULTY_SELECT

            # 返回按钮
            back_rect = pygame.Rect(w - 130, h - 60, 100, 40)
            if back_rect.collidepoint(x, y):
                if self.player_camp == "观察者":
                    self.state = GameState.CAMP_SELECT
                else:
                    self.state = GameState.DIFFICULTY_SELECT

        elif self.state == GameState.VICTORY:
            # 返回主界面按钮
            back_rect = pygame.Rect(w//2 - 100, h//2 + 50, 200, 50)
            if back_rect.collidepoint(x, y):
                self.state = GameState.SETTINGS
                self.reset_game()

        elif self.state == GameState.LAWSUIT:
            # 继续游戏按钮
            continue_rect = pygame.Rect(w//2 - 100, h//2 + 50, 200, 50)
            if continue_rect.collidepoint(x, y):
                self.state = GameState.BATTLE

    def run(self):
        """游戏主循环"""
        running = True
        
        while running:
            self.clock.tick(self.fps)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:  # 按F键切换全屏
                        self.toggle_fullscreen()

            # 更新士气
            self.update_morale()

            # AI自动行动
            if self.state in [GameState.BATTLE, GameState.FULL_BATTLE]:
                self.ai_action()
                
                # 检查官司条件
                if self.event_triggered and not self.lawsuit_triggered:
                    self.check_lawsuit()

            # 绘制对应界面
            if self.state == GameState.SETTINGS:
                self.draw_settings()
            elif self.state == GameState.CAMP_SELECT:
                self.draw_camp_select()
            elif self.state == GameState.DIFFICULTY_SELECT:
                self.draw_difficulty_select()
            elif self.state in [GameState.BATTLE, GameState.FULL_BATTLE]:
                self.draw_battle()
            elif self.state == GameState.EVENT:
                self.draw_event()
            elif self.state == GameState.VICTORY:
                self.draw_victory()
            elif self.state == GameState.LAWSUIT:
                self.draw_lawsuit()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()

