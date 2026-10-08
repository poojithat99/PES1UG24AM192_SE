import random
import pygame
from game.maze import generate_maze, CELL
from game.entities import Player, Enemy

COLS, ROWS = 13, 11
WIDTH = COLS * CELL
HUD_H = 72
HEIGHT = ROWS * CELL + HUD_H
FPS = 60

RAMP_MS = 15000        # Task 2: every 15 seconds...
RAMP_STEP = 2          # ...move_interval decreases by 2...
MIN_INTERVAL = 5       # ...but never below 5
FREEZE_FRAMES = 300    # Task 3: 5 seconds at 60 FPS
PELLET_RADIUS = 9

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Chase")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.hud_font = pygame.font.SysFont("monospace", 16)
        self.big_font = pygame.font.SysFont("monospace", 38, bold=True)
        self.reset()

    def reset(self):
        self.walls = generate_maze(COLS, ROWS)
        self.player = Player(0, 0)
        # three enemies, one in each corner the player does not start in
        self.enemies = [
            Enemy(ROWS-1, COLS-1),  # bottom-right
            Enemy(0, COLS-1),       # top-right
            Enemy(ROWS-1, 0),       # bottom-left
        ]
        self.exit_rect = pygame.Rect((COLS//2)*CELL+5, (ROWS//2)*CELL+5, CELL-10, CELL-10)
        self.caught = False
        self.won = False
        self.score = 0  # Task 4: frames survived
        # Task 2: difficulty ramp
        self.start_ticks = pygame.time.get_ticks()
        self.speed_tier = 0
        # Task 3: power pellet
        self.freeze_timer = 0
        self.pellet = self._place_pellet()

    def _place_pellet(self):
        # any cell except the four corners (spawns) and the exit cell
        corners = {(0, 0), (0, COLS-1), (ROWS-1, 0), (ROWS-1, COLS-1)}
        exit_cell = (ROWS//2, COLS//2)
        cells = [(r, c) for r in range(ROWS) for c in range(COLS)
                 if (r, c) not in corners and (r, c) != exit_cell]
        r, c = random.choice(cells)
        cx, cy = c*CELL + CELL//2, r*CELL + CELL//2
        return pygame.Rect(cx-PELLET_RADIUS, cy-PELLET_RADIUS, PELLET_RADIUS*2, PELLET_RADIUS*2)

    def _elapsed_ms(self):
        return pygame.time.get_ticks() - self.start_ticks

    def _update_speed(self):
        target = self._elapsed_ms() // RAMP_MS
        while self.speed_tier < target and self.enemies[0].move_interval > MIN_INTERVAL:
            self.speed_tier += 1
            for enemy in self.enemies:
                enemy.move_interval = max(MIN_INTERVAL, enemy.move_interval - RAMP_STEP)

    def _update_freeze(self):
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            if self.freeze_timer == 0:
                for enemy in self.enemies:
                    enemy.frozen = False
        if self.pellet and self.player.rect.colliderect(self.pellet):
            self.pellet = None
            self.freeze_timer = FREEZE_FRAMES
            for enemy in self.enemies:
                enemy.frozen = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
        return True

    def update(self):
        if self.caught or self.won: return
        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, ROWS, COLS)
        self._update_speed()
        self._update_freeze()
        for enemy in self.enemies:
            enemy.update(self.walls, self.player, ROWS, COLS)
        if any(self.player.rect.colliderect(e.rect) for e in self.enemies):
            self.caught = True
        if self.player.rect.colliderect(self.exit_rect):
            self.won = True
        if not self.caught:
            self.score += 1  # player is still alive this frame

    def draw(self):
        self.screen.fill((230, 220, 210))
        wc=(50,40,60)
        for r in range(ROWS):
            for c in range(COLS):
                x,y=c*CELL,r*CELL
                w=self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen,wc,(x,y),(x+CELL,y),3)
                if w[1]: pygame.draw.line(self.screen,wc,(x,y+CELL),(x+CELL,y+CELL),3)
                if w[2]: pygame.draw.line(self.screen,wc,(x+CELL,y),(x+CELL,y+CELL),3)
                if w[3]: pygame.draw.line(self.screen,wc,(x,y),(x,y+CELL),3)
        pygame.draw.rect(self.screen,(80,200,80),self.exit_rect,border_radius=4)
        lbl=self.font.render("EXIT",True,(20,80,20))
        self.screen.blit(lbl,(self.exit_rect.x+2,self.exit_rect.y+6))
        if self.pellet:
            pygame.draw.circle(self.screen,(255,215,0),self.pellet.center,PELLET_RADIUS)
            pygame.draw.circle(self.screen,(180,140,0),self.pellet.center,PELLET_RADIUS,2)
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        hud=pygame.Rect(0,ROWS*CELL,WIDTH,HUD_H)
        pygame.draw.rect(self.screen,(30,30,50),hud)
        info=self.hud_font.render("Reach EXIT before the enemies catch you!  R=Restart",True,(200,200,200))
        self.screen.blit(info,(8,ROWS*CELL+5))
        interval=self.enemies[0].move_interval
        tier="Speed Tier: %d%s (moves every %d frames)"%(self.speed_tier," MAX" if interval<=MIN_INTERVAL else "",interval)
        if self.freeze_timer>0:
            status=self.hud_font.render("%s   FROZEN %.1fs"%(tier,self.freeze_timer/FPS),True,(120,200,255))
        else:
            status=self.hud_font.render(tier,True,(255,215,0))
        self.screen.blit(status,(8,ROWS*CELL+27))
        surv=self.hud_font.render("Survived: %ds"%(self.score//FPS),True,(255,255,255))
        self.screen.blit(surv,(8,ROWS*CELL+49))
        if self.caught:
            self._overlay("CAUGHT!", (220,60,60))
        if self.won:
            self._overlay("ESCAPED!", (80,220,80))
        pygame.display.flip()

    def _overlay(self, text, color):
        surf=pygame.Surface((WIDTH,ROWS*CELL),pygame.SRCALPHA)
        surf.fill((0,0,0,140))
        self.screen.blit(surf,(0,0))
        msg=self.big_font.render(text,True,color)
        final=self.font.render("Survived: %ds  (score %d)"%(self.score//FPS,self.score),True,(255,255,255))
        sub=self.font.render("Press R to Restart",True,(200,200,200))
        self.screen.blit(msg,(WIDTH//2-msg.get_width()//2,ROWS*CELL//2-50))
        self.screen.blit(final,(WIDTH//2-final.get_width()//2,ROWS*CELL//2))
        self.screen.blit(sub,(WIDTH//2-sub.get_width()//2,ROWS*CELL//2+35))

    def run(self):
        running=True
        while running:
            running=self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
