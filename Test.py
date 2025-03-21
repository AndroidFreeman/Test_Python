import pygame
import random
import time
import copy

# 游戏参数
BLOCK_SIZE = 35
BORDER = 2
WIDTH = 10
HEIGHT = 20
FPS = 60
PREVIEW_SIZE = BLOCK_SIZE * 4

# 颜色定义
COLORS = [
    (40, 40, 40), (255, 85, 85), (100, 200, 115),
    (120, 108, 245), (255, 140, 50), (50, 160, 255),
    (255, 220, 55), (160, 50, 190)
]

# 方块形状
SHAPES = [
    {"shape": [[1,1,1,1]], "preview_offset": (1, 2)},
    {"shape": [[1,1],[1,1]], "preview_offset": (1, 1)},
    {"shape": [[1,1,1],[0,1,0]], "preview_offset": (1, 1)},
    {"shape": [[1,1,1],[1,0,0]], "preview_offset": (1, 1)},
    {"shape": [[1,1,1],[0,0,1]], "preview_offset": (1, 1)},
    {"shape": [[1,1,0],[0,1,1]], "preview_offset": (1, 1)},
    {"shape": [[0,1,1],[1,1,0]], "preview_offset": (1, 1)}
]

class Tetris:
    def __init__(self, ai_mode=True):
        pygame.init()
        self.screen = pygame.display.set_mode((BLOCK_SIZE*(WIDTH+7), BLOCK_SIZE*HEIGHT))
        pygame.display.set_caption("AI Tetris Pro")
        self.clock = pygame.time.Clock()
        self.ai_mode = ai_mode
        self.move_sequence = []
        self.reset_game()

    def reset_game(self):
        self.game_board = [[0]*WIDTH for _ in range(HEIGHT)]
        self.score = 0
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.last_drop = time.time()

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

    def evaluate_position(self, piece):
        temp = [row.copy() for row in self.game_board]
        max_height = 0
        wells = 0
        holes = 0
        bumpiness = 0
        
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    ty = y + piece['y']
                    tx = x + piece['x']
                    if 0 <= tx < WIDTH and 0 <= ty < HEIGHT:
                        temp[ty][tx] = piece['color']
        
        heights = []
        for x in range(WIDTH):
            height = 0
            for y in range(HEIGHT):
                if temp[y][x]:
                    height = HEIGHT - y
                    break
            heights.append(height)
            max_height = max(max_height, height)
            
            has_block = False
            for y in range(HEIGHT):
                if temp[y][x]:
                    has_block = True
                elif has_block:
                    holes += 1
        
        for x in range(WIDTH):
            left = heights[x-1] if x > 0 else 100
            right = heights[x+1] if x < WIDTH-1 else 100
            wells += max(0, min(left, right) - heights[x])
        
        bumpiness = sum(abs(heights[i] - heights[i+1]) for i in range(WIDTH-1))
        full_lines = sum(1 for row in temp if 0 not in row)
        
        return (
            full_lines ** 2.5 * 1000
            - holes * 300
            - wells * 50
            - bumpiness * 10
            - max_height * 5
        )

    def ai_think(self):
        best = {'score': -float('inf'), 'moves': []}
        original = copy.deepcopy(self.current_piece)

        for rotate in range(4):
            piece = copy.deepcopy(original)
            for _ in range(rotate):
                piece['shape'] = [list(row) for row in zip(*reversed(piece['shape']))]
            
            min_x = -len(piece['shape'][0]) + 1
            max_x = WIDTH - 1
            
            for x in range(min_x, max_x):
                test = copy.deepcopy(piece)
                test['x'] = x
                
                while not self.check_collision(test, dy=1):
                    test['y'] += 1
                
                if not self.check_collision(test):
                    score = self.evaluate_position(test)
                    if score > best['score']:
                        moves = self.generate_moves(original, test, rotate)
                        best = {'score': score, 'moves': moves}
        return best['moves']

    def generate_moves(self, original, target, rotations):
        moves = []
        if rotations in (1, 3):
            moves += ['rotate'] * rotations
        elif rotations == 2:
            moves += ['rotate', 'rotate']
        
        dx = target['x'] - original['x']
        if dx != 0:
            direction = 'right' if dx > 0 else 'left'
            moves += [direction] * abs(dx)
        
        moves.append('drop')
        return moves

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()

            if self.ai_mode and not self.game_over:
                if not self.move_sequence:
                    self.move_sequence = self.ai_think()
                if self.move_sequence:
                    action = self.move_sequence.pop(0)
                    if action == 'rotate':
                        self.rotate_piece()
                    elif action == 'left' and not self.check_collision(self.current_piece, dx=-1):
                        self.current_piece['x'] -= 1
                    elif action == 'right' and not self.check_collision(self.current_piece, dx=1):
                        self.current_piece['x'] += 1
                    elif action == 'drop':
                        while not self.check_collision(self.current_piece, dy=1):
                            self.current_piece['y'] += 1
                        self.lock_piece()
                        self.current_piece = self.next_piece
                        self.next_piece = self.new_piece()
                        if self.check_collision(self.current_piece):
                            self.game_over = True

            self.screen.fill(COLORS[0])
            
            # 绘制游戏区域边框
            pygame.draw.rect(self.screen, (100,100,100), 
                           (0, 0, BLOCK_SIZE*WIDTH, BLOCK_SIZE*HEIGHT), 3)
            
            # 绘制下一个方块预览
            preview_x = WIDTH + 2
            preview_y = 6
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
            font = pygame.font.SysFont('consolas', 24)
            score_text = font.render(f'Score: {self.score}', True, (255,255,255))
            self.screen.blit(score_text, (BLOCK_SIZE*(WIDTH+1), 20))
            
            # 游戏结束提示
            if self.game_over:
                over_text = font.render('Game Over - Press R to Restart', True, (255,255,255))
                self.screen.blit(over_text, (BLOCK_SIZE, BLOCK_SIZE*HEIGHT//2))
            
            pygame.display.update()
            self.clock.tick(FPS)

if __name__ == '__main__':
    game = Tetris(ai_mode=True)
    game.run()
