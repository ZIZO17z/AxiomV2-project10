import pygame
import sympy
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import numpy as np
import random
import sys
import math


WIDTH = 600
HEIGHT = 800
BG_COLOR = (30, 30, 40)
SCREEN_TITLE = "CALC Calculator"

NEON_GREEN = (57, 255, 20)
HOT_PINK = (255, 20, 147)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0,0,0)
RED = (255, 100, 100)

LCD_GREEN = (160, 180, 160)
GRID_COLOR = (50, 70, 50)

MODE_CALC = "CALCULATOR"
MODE_3D = "3D GRAPH"


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(SCREEN_TITLE)
clock = pygame.time.Clock()


try:
    FONT_DISPLAY = pygame.font.SysFont("Consolas", 32, bold=True)
    FONT_BTN = pygame.font.SysFont("Comic Sans MS", 20, bold=True)
    FONT_TINY = pygame.font.SysFont("Comic Sans MS", 14)

except:
    FONT_DISPLAY = pygame.font.SysFont("Courier New", 30, bold=True)
    FONT_BTN = pygame.font.SysFont("Arial", 20, bold=True)
    FONT_TINY = pygame.font.SysFont("Arial", 14)


x, y ,z = sympy.symbols("x y z")
transformations = (standard_transformations + (implicit_multiplication_application,))

class MathBrain:
    def __init__(self):
        self.result_str = "Ready"
        self.current_func_3d = None
        self.current_func_2d = None
    

    def safe_parse(self, text):
        try:
            clean_str = text.replace("^", "**")
            return parse_expr(clean_str, transformations=transformations)
        except:
            return None
        
    def solve(self, text):
        expr = self.safe_parse(text)
        if expr:
            try:
                if isinstance(expr, list) or "Matrix" in str(type(expr)):
                    mat = sympy.Matrix(expr)
                    self.result_str = str(mat)
                else: 
                    res = expr.evalf()
                    self.result_str = f"= {res:.4f}"
            except Exception as e:
                self.result_str = "Error"
        else:
            self.result_str = "Syntax Error"

    
    def prepare_3d(self, text):
        expr = self.safe_parse(text)
        if expr:
            try:
                self.current_func_3d = sympy.lambdify((x, y), expr, modules=['numpy'])
                self.result_str = "3D Mode Active"
                return True
            
            except:
                self.result_str = "3D Parse Error"
        return False
    

class AdvancedInput:
    def __init__(self):
        self.text = ""
        self.cursor_pos = 0
        self.blink_timer = 0

    def add_char(self, char):
        self.text = self.text[:self.cursor_pos] + char + self.text[self.cursor_pos:]
        self.cursor_pos +=1

    def delete(self):
        if self.cursor_pos > 0:
            self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
            self.cursor_pos -=1
    
    def move_cursor(self, direction):
        if direction == "LEFT" and self.cursor_pos > 0:
            self.cursor_pos -= 1
        elif direction == "RIGHT" and self.cursor_pos < len(self.text):
            self.cursor_pos += 1

    def clear(self):
        self.text = ""
        self.cursor_pos = 0

    def draw(self, surface, x,y):
        txt_surf = FONT_DISPLAY.render(self.text, True, BLACK)
        surface.blit(txt_surf, (x, y))

        self.blink_timer += 1
        if self.blink_timer % 60 < 30:
            prefix = self.text[:self.cursor_pos]
            width_to_cursor = FONT_DISPLAY.size(prefix)[0]
            cursor_h = FONT_DISPLAY.get_height()
            pygame.draw.line(surface, RED, (x + width_to_cursor, y), (x + width_to_cursor, y + cursor_h), 2)


class Grapher3D:
    def __init__(self):
        self.angle_x = 0.5
        self.angle_y = 0.5
        self.zoom = 20
        self.mesh_res = 15

    def project(self, x, y, z, width, height):
        rx = x * math.cos(self.angle_y) - z * math.sin(self.angle_y)
        rz = x * math.sin(self.angle_y) + z * math.cos(self.angle_y)

        ry = y * math.cos(self.angle_x) - rz * math.sin(self.angle_x)

        screen_x = width/2 + rx * self.zoom
        screen_y = height/2 - ry * self.zoom

        return (screen_x, screen_y)
    
    def draw(self, surface, rect, func):
        surface.set_clip(rect)
        if not func:
            hint = FONT_TINY.render("Type func(x,y) -> CLICK 3D", True, (100, 100, 100))
            surface.blit(hint, (rect.centerx - 80, rect.centery))
            surface.set_clip(None)
            return
        
        limit = 5
        step = limit * 2 / self.mesh_res

        points = []
        for i in range(self.mesh_res + 1):
            row = []
            x_val = -limit + i * step

            for j in range(self.mesh_res + 1):
                try:
                    y_val = -limit + j * step
                    z_val = func(x_val, y_val)
                    z_val = max(min(z_val, 10), -10)
                except:
                    z_val = 0

                px, py = self.project(x_val, z_val, y_val, rect.width, rect.height)
                row.append((rect.x + px - rect.width/2, rect.y + py + rect.height/2))
            points.append(row)

        for i in range(len(points)):
            for j in range(len(points[i])):
                if j< len(points[i]) - 1:
                    pygame.draw.line(surface, HOT_PINK, points[i][j], points[i][j+1], 2)
                if i < len(points) - 1:
                    pygame.draw.line(surface, CYAN, points[i][j], points[i+1][j], 2)

        surface.set_clip(None)


class WobblyButton:
    def __init__(self, x, y, w, h, text, action, color=CYAN, text_color = BLACK):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.base_color = color
        self.hover_color = tuple(min(255, c+50) for c in color)
        self.text_color = text_color
        self.wobble_timer = random.randint(0, 100)
    

    def draw(self, surface, mouse_pos):
        self.wobble_timer += 1
        ox = np.sin(self.wobble_timer * 0.1) * 2
        oy = np.cos(self.wobble_timer * 0.1) * 2

        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.base_color

        shadow_rect = pygame.Rect(self.rect.x + ox + 4, self.rect.y + oy + 4, self.rect.width, self.rect.height)
        pygame.draw.rect(surface, (20, 20, 20), shadow_rect, border_radius=15)
        
        draw_rect = pygame.Rect(self.rect.x + ox, self.rect.y + oy, self.rect.width, self.rect.height)
        pygame.draw.rect(surface, color, draw_rect, border_radius=15)
        pygame.draw.rect(surface, BLACK, draw_rect, 3, border_radius=15)

        text_surf = FONT_BTN.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False
    


brain = MathBrain()
inp = AdvancedInput()
engine3d = Grapher3D()
buttons = []
current_mode = MODE_CALC

start_y = 350
rows = [
    ['C', 'DEL', '<', '>', '3D'],
    ['7', '8', '9', '/', 'sin'],
    ['4', '5', '6', '*', 'cos'],
    ['1', '2', '3', '-', '^'],
    ['0', '.', 'x', 'y', '+'],
    ['(', ')', ',', '=', 'PLOT']
]
btn_w = (WIDTH - 70)//5
btn_h = 55
gap = 10

def build_buttons():
    buttons.clear()
    for r_idx, row in enumerate(rows):
        for c_idx, label in enumerate(row):
            x_pos = 15 + c_idx * (btn_w + gap)
            y_pos = start_y + r_idx * (btn_h + gap)

            color =NEON_GREEN
            action = None

            if label == "C":
                action = inp.clear
                color = RED
            elif label == "DEL":
                action = inp.delete
                color = RED
            elif label == "<":
                action = lambda: inp.move_cursor("LEFT")
                color = YELLOW
            elif label == ">":
                action = lambda: inp.move_cursor("RIGHT")
                color = YELLOW
            elif label== "3D":
                def switch_3d():
                    global current_mode
                    current_mode = MODE_3D
                    brain.prepare_3d(inp.text)
                action = switch_3d
                color = HOT_PINK

            elif label == "=":
                def do_solve():
                    global current_mode
                    current_mode = MODE_CALC
                    brain.solve(inp.text)
                action = do_solve
                color = CYAN
            
            elif label == "PLOT":
                action = lambda: brain.prepare_3d(inp.text) if current_mode == MODE_3D else None
                color = CYAN
            else:
                def make_typer(l):
                    return lambda: inp.add_char(l)
                action = make_typer(label)

            buttons.append(WobblyButton(x_pos, y_pos, btn_w, btn_h, label, action, color))

build_buttons()

running = True
mouse_down = False
last_mouse_pos = (0, 0)




while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_down = True
            last_mouse_pos = mouse_pos
        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_down = False

        for btn in buttons:
            if btn.is_clicked(event):
                if callable(btn.action):
                    try:
                        btn.action()
                    except Exception as e:
                        brain.result_str = "Err"


        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                inp.delete()
            elif event.key == pygame.K_LEFT:
                inp.move_cursor("LEFT")

            elif event.key == pygame.K_RIGHT:
                inp.move_cursor("RIGHT")

            elif event.key == pygame.K_RETURN:
                brain.solve(inp.text)
            elif event.unicode.isprintable():
                inp.add_char(event.unicode)

    if current_mode == MODE_3D and mouse_down:
        dx = mouse_pos[0] - last_mouse_pos[0]
        dy = mouse_pos[1] - last_mouse_pos[1]
        engine3d.angle_y += dx * 0.01
        engine3d.angle_x += dy * 0.01 
        last_mouse_pos = mouse_pos

    screen.fill(BG_COLOR)

    body_rect = pygame.Rect(10, 10, WIDTH - 20, HEIGHT - 20)
    pygame.draw.rect(screen, (60, 60, 80), body_rect, border_radius=40)
    pygame.draw.rect(screen, BLACK, body_rect, 6, border_radius=40)

    lcd_rect = pygame.Rect(30, 30, WIDTH-60, 280)
    pygame.draw.rect(screen, LCD_GREEN, lcd_rect, border_radius=15)
    pygame.draw.rect(screen, BLACK, lcd_rect, 4, border_radius=15)

    if current_mode == MODE_3D:
        engine3d.draw(screen, lcd_rect, brain.current_func_3d)
        mode_text = FONT_TINY.render("MODE: 3D(DRAG 2 Rotate)", True, BLACK)
        screen.blit(mode_text, (lcd_rect.x + 10, lcd_rect.y + 10))      
    else:
        mode_text = FONT_TINY.render("MODE: CALC", True, BLACK)
        screen.blit(mode_text, (lcd_rect.x + 10, lcd_rect.y + 10))

        res_surf = FONT_BTN.render(brain.result_str, True, (40, 40, 40))
        screen.blit(res_surf, (lcd_rect.x + 15, lcd_rect.bottom - 40))

    
    inp.draw(screen, lcd_rect.x + 15, lcd_rect.y + 40)

    for btn in buttons:
        btn.draw(screen, mouse_pos)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()