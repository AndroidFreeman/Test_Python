import pygame
import random
import time

# 游戏参数
BLOCK_SIZE = 40
BORDER = 3
WIDTH = 10
HEIGHT = 20
FPS = 60
PREVIEW_SIZE = BLOCK_SIZE * 4
BUTTON_RADIUS = BLOCK_SIZE  # 按钮半径

# 颜色定义
COLORS = [
    (30, 30, 30),      # 背景
    (255, 85, 85),     # 红
    (100, 200, 115),   # 绿
    (120, 108, 245),   # 蓝
    (255, 140, 50),    # 橙
    (50, 160, 255),    # 浅蓝
    (255, 220, 55),    # 黄
    (160, 50, 190)     # 紫
]

# 触控按钮布局（右侧独立区域）
BUTTONS = {
    'left': (WIDTH*BLOCK_SIZE + BLOCK_SIZE*3, HEIGHT*BLOCK_SIZE - BLOCK_SIZE*5),
    'right': (WIDTH*BLOCK_SIZE + BLOCK_SIZE*5, HEIGHT*BLOCK_SIZE - BLOCK_SIZE*5),
    'rotate': (WIDTH*BLOCK_SIZE + BLOCK_SIZE*4, HEIGHT*BLOCK_SIZE - BLOCK_SIZE*7),
    'down': (WIDTH*BLOCK_SIZE + BLOCK_SIZE*4, HEIGHT*BLOCK_SIZE - BLOCK_SIZE*3)
}

# 方块形状
SHAPES = [
    {"shape": [[1,1,1,1]], "preview_offset": (1, 2)},   # I
    {"shape": [[1,1],[1,1]], "preview_offset": (1, 1)},  # O
    {"shape": [[1,1,1],[0,1,0]], "preview_offset": (1, 1)},  # T
    {"shape": [[1,1,1],[1,0,0]], "preview_offset": (1, 1)},  # L
    {"shape": [[1,1,1],[0,0,1]], "preview_offset": (1, 1)},  # J
    {"shape": [[1,1,0],[0,1,1]], "preview_offset": (1, 1)},  # S
    {"shape": [[0,1,1],[1,1,0]], "preview_offset": (1, 1)}   # Z
]

class Tetris:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((
            BLOCK_SIZE*(WIDTH+7), 
            BLOCK_SIZE*HEIGHT
        ))
        pygame.display.set_caption("触控俄罗斯方块")
        self.clock = pygame.time.Clock()
        self.reset_game()
        self.touch_down = False

    def reset_game(self):
        self.game_board = [[0]*WIDTH for _ in range(HEIGHT)]
        self.score = 0
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.last_drop = time.time()

    # 新增缺失的方法
    def new_piece(self):
        shape_data = random.choice(SHAPES)
        return {
            "shape": shape_data["shape"],
            "preview_offset": shape_data["preview_offset"],
            "color": random.randint(1, len(COLORS)-1),
            "x": WIDTH//2 - len(shape_data["shape"][0])//2,
            "y": 0
        }

    def check_collision(self, piece, dx=0, dy=0):
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece['x'] + x + dx
                    new_y = piece['y'] + y + dy
                    if new_x < 0 or new_x >= WIDTH or new_y >= HEIGHT:
                        return True
                    if new_y >= 0 and self.game_board[new_y][new_x]:
                        return True
        return False

    def rotate_piece(self):
        rotated = [list(row) for row in zip(*reversed(self.current_piece['shape']))]
        old_shape = self.current_piece['shape']
        self.current_piece['shape'] = rotated
        if self.check_collision(self.current_piece):
            self.current_piece['shape'] = old_shape

    def lock_piece(self):
        for y, row in enumerate(self.current_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    self.game_board[y + self.current_piece['y']][x + self.current_piece['x']] = self.current_piece['color']
        
        lines_cleared = 0
        for y in range(HEIGHT):
            if 0 not in self.game_board[y]:
                del self.game_board[y]
                self.game_board.insert(0, [0]*WIDTH)
                lines_cleared += 1
        
        if lines_cleared > 0:
            self.score += 100 * (2 ** lines_cleared)

    def draw_block(self, x, y, color, is_preview=False):
        border = BORDER * 2 if is_preview else BORDER
        pygame.draw.rect(self.screen, COLORS[color],
                        (x*BLOCK_SIZE + border, y*BLOCK_SIZE + border,
                         BLOCK_SIZE - 2*border, BLOCK_SIZE - 2*border))
        if color != 0:
            pygame.draw.line(self.screen, (255,255,255), 
                            (x*BLOCK_SIZE, y*BLOCK_SIZE),
                            (x*BLOCK_SIZE + BLOCK_SIZE, y*BLOCK_SIZE), 2)
            pygame.draw.line(self.screen, (255,255,255),
                            (x*BLOCK_SIZE, y*BLOCK_SIZE),
                            (x*BLOCK_SIZE, y*BLOCK_SIZE + BLOCK_SIZE), 2)

    def draw_button(self, name, pos):
        x, y = pos
        center = (x, y)
        color = (200, 200, 200) if not self.touch_down else (150, 150, 150)
        
        pygame.draw.circle(self.screen, (50,50,50), center, BUTTON_RADIUS+2)
        pygame.draw.circle(self.screen, color, center, BUTTON_RADIUS)
        
        arrow_color = (40, 40, 40)
        line_width = 4
        
        if name == 'left':
            points = [
                (center[0] - 10, center[1]),
                (center[0] + 5, center[1] - 12),
                (center[0] + 5, center[1] + 12)
            ]
        elif name == 'right':
            points = [
                (center[0] + 10, center[1]),
                (center[0] - 5, center[1] - 12),
                (center[0] - 5, center[1] + 12)
            ]
        elif name == 'rotate':
            pygame.draw.arc(self.screen, arrow_color, 
                           (center[0]-15, center[1]-15, 30, 30),
                           0.5, 5.5, line_width)
            pygame.draw.polygon(self.screen, arrow_color, [
                (center[0]+10, center[1]-10),
                (center[0]+15, center[1]-15),
                (center[0]+5, center[1]-20)
            ])
        elif name == 'down':
            points = [
                (center[0], center[1] + 10),
                (center[0] - 12, center[1] - 5),
                (center[0] + 12, center[1] - 5)
            ]
        
        if name in ['left', 'right', 'down']:
            pygame.draw.polygon(self.screen, arrow_color, points)
        
        return pygame.Rect(x-BUTTON_RADIUS, y-BUTTON_RADIUS, BUTTON_RADIUS*2, BUTTON_RADIUS*2)

    def handle_touch(self, pos):
        for name, btn_pos in BUTTONS.items():
            btn_rect = pygame.Rect(
                btn_pos[0]-BUTTON_RADIUS, 
                btn_pos[1]-BUTTON_RADIUS,
                BUTTON_RADIUS*2, 
                BUTTON_RADIUS*2
            )
            if btn_rect.collidepoint(pos):
                if name == 'left' and not self.check_collision(self.current_piece, dx=-1):
                    self.current_piece['x'] -= 1
                elif name == 'right' and not self.check_collision(self.current_piece, dx=1):
                    self.current_piece['x'] += 1
                elif name == 'rotate':
                    self.rotate_piece()
                elif name == 'down':
                    self.current_piece['y'] += 1
                return True
        return False

    def run(self):
        while True:
            delta_time = self.clock.tick(FPS)/1000.0
            self.touch_down = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.touch_down = True
                    self.handle_touch(pygame.mouse.get_pos())
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.touch_down = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:
                        self.reset_game()

            # 自动下落逻辑
            if not self.game_over and time.time() - self.last_drop > 0.5:
                if not self.check_collision(self.current_piece, dy=1):
                    self.current_piece['y'] += 1
                    self.last_drop = time.time()
                else:
                    self.lock_piece()
                    self.current_piece = self.next_piece
                    self.next_piece = self.new_piece()
                    self.last_drop = time.time()
                    if self.check_collision(self.current_piece):
                        self.game_over = True

            # 绘制界面
            self.screen.fill(COLORS[0])
            
            # 绘制游戏区域边框
            pygame.draw.rect(self.screen, (100,100,100), 
                           (0, 0, BLOCK_SIZE*WIDTH, BLOCK_SIZE*HEIGHT), 3)
            
            # 绘制预览区域
            preview_x = WIDTH + 1
            preview_y = 2
            pygame.draw.rect(self.screen, (80,80,80), 
                           (preview_x*BLOCK_SIZE-10, preview_y*BLOCK_SIZE-10, 
                            PREVIEW_SIZE+20, PREVIEW_SIZE+20), 0)
            ox, oy = self.next_piece['preview_offset']
            for y, row in enumerate(self.next_piece['shape']):
                for x, cell in enumerate(row):
                    if cell:
                        self.draw_block(
                            preview_x + x + ox, 
                            preview_y + y + oy, 
                            self.next_piece['color'], 
                            is_preview=True
                        )
            
            # 绘制游戏板
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    if self.game_board[y][x]:
                        self.draw_block(x, y, self.game_board[y][x])
            
            # 绘制当前方块
            if not self.game_over:
                for y, row in enumerate(self.current_piece['shape']):
                    for x, cell in enumerate(row):
                        if cell:
                            self.draw_block(x + self.current_piece['x'], 
                                         y + self.current_piece['y'], 
                                         self.current_piece['color'])
            
            # 绘制分数
            font = pygame.font.SysFont('notosanssc', 24, bold=True)
            score_text = font.render(f'分数: {self.score}', True, (255,255,255))
            self.screen.blit(score_text, (BLOCK_SIZE*(WIDTH+1), 20))
            
            # 绘制控制按钮
            for name, pos in BUTTONS.items():
                self.draw_button(name, pos)
            
            # 游戏结束提示
            if self.game_over:
                over_font = pygame.font.SysFont('notosanssc', 32, bold=True)
                over_text = over_font.render('游戏结束 - 点击重开', True, (255,255,255))
                self.screen.blit(over_text, (BLOCK_SIZE, BLOCK_SIZE*HEIGHT//2 - 20))
            
            pygame.display.update()

if __name__ == '__main__':
    game = Tetris()
    game.run()
