import pygame
from game.maze import CELL

SPEED = 2

class Player:
    def __init__(self, r, c):
        self.r, self.c = r, c
        cx, cy = c*CELL+CELL//2, r*CELL+CELL//2
        self.rect = pygame.Rect(cx-10, cy-10, 20, 20)
        self.color = (60, 120, 220)

    def move(self, keys, walls, rows, cols):
        dx=dy=0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx=-SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx=SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy=-SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy=SPEED
        nr = self.rect.move(dx,0)
        if self._valid(nr, walls, rows, cols): self.rect=nr
        nr = self.rect.move(0,dy)
        if self._valid(nr, walls, rows, cols): self.rect=nr

    def _valid(self, rect, walls, rows, cols):
        # stay inside the maze bounds
        for px,py in [(rect.left,rect.top),(rect.right-1,rect.top),(rect.left,rect.bottom-1),(rect.right-1,rect.bottom-1)]:
            cr,cc=py//CELL,px//CELL
            if not(0<=cr<rows and 0<=cc<cols): return False
        # do not cross any wall (walls are drawn as thin lines on cell edges)
        t = 2  # half of the wall thickness
        r0, r1 = max(rect.top//CELL, 0), min((rect.bottom-1)//CELL, rows-1)
        c0, c1 = max(rect.left//CELL, 0), min((rect.right-1)//CELL, cols-1)
        for r in range(r0, r1+1):
            for c in range(c0, c1+1):
                x, y = c*CELL, r*CELL
                w = walls[r][c]
                if w[0] and rect.colliderect(pygame.Rect(x-t, y-t, CELL+2*t, 2*t)): return False
                if w[1] and rect.colliderect(pygame.Rect(x-t, y+CELL-t, CELL+2*t, 2*t)): return False
                if w[2] and rect.colliderect(pygame.Rect(x+CELL-t, y-t, 2*t, CELL+2*t)): return False
                if w[3] and rect.colliderect(pygame.Rect(x-t, y-t, 2*t, CELL+2*t)): return False
        return True

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)

class Enemy:
    def __init__(self, r, c):
        self.r, self.c = r, c
        cx, cy = c*CELL+CELL//2, r*CELL+CELL//2
        self.rect = pygame.Rect(cx-12, cy-12, 24, 24)
        self.color = (220, 60, 60)
        self.timer = 0
        self.move_interval = 20  # frames between cell moves
        self.frozen = False      # set by the power pellet

    def update(self, walls, player, rows, cols):
        from game.maze import bfs
        if self.frozen:
            return  # frozen: no timer tick, no BFS, no movement
        self.timer += 1
        if self.timer >= self.move_interval:
            self.timer = 0
            pr, pc = player.rect.centery//CELL, player.rect.centerx//CELL
            step = bfs(walls, (self.r, self.c), (pr, pc), rows, cols)
            if step:
                dr, dc = step
                self.r += dr; self.c += dc
                cx, cy = self.c*CELL+CELL//2, self.r*CELL+CELL//2
                self.rect.center = (cx, cy)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        # eyes
        for ex in [self.rect.x+4, self.rect.x+14]:
            pygame.draw.circle(screen, (255,255,255), (ex, self.rect.y+8), 4)
            pygame.draw.circle(screen, (0,0,0), (ex+1, self.rect.y+8), 2)
        if self.frozen:
            # icy tint + white border + snowflake so a frozen enemy is obvious
            tint = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            tint.fill((120, 200, 255, 170))
            screen.blit(tint, self.rect.topleft)
            pygame.draw.rect(screen, (230, 245, 255), self.rect, 2, border_radius=5)
            cx, cy = self.rect.center
            for dx, dy in [(8, 0), (0, 8), (6, 6), (6, -6)]:
                pygame.draw.line(screen, (255, 255, 255), (cx-dx, cy-dy), (cx+dx, cy+dy), 2)
