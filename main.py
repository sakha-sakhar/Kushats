import pygame
import sys
import os
import sqlite3
from math import ceil, floor
from random import randint

directions = {0: ((1, 0), 'right'),  # вправо
              1: ((-1, 0), 'left'),  # влево
              2: ((0, 1), 'down'),  # вниз
              3: ((0, -1), 'up'),  # вверх
              -1: ((0, 0), 'stop')}   # стоп

volume = 1  # громкость музыки


def load_image(name, colorkey=None):
    fullname = os.path.join('images', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def load_font(name, size):
    found = True
    fullname = os.path.join('fonts', name)
    if not os.path.isfile(fullname):
        found = False
        print(f'Файл со шрифтом {fullname} не найден')
        fonts = ['18534.TTF', '18963.TTF', '18949.TTF', '18536.TTF']
        for font in fonts:
            fullname = os.path.join('fonts', font)
            if os.path.isfile(fullname):
                found = True
                break
    if found:
        return pygame.font.Font(fullname, size)
    else:
        sys.exit()


class Animated:
    def __init__(self, images, delay):
        self.images = [load_image(image) for image in images]
        self.delay = delay

    def get_image(self):
        return self.images[pygame.time.get_ticks() // self.delay % len(self.images)]


class Entity:  # сущность - игрок и призраки
    def __init__(self, pos, board, name):
        self.board = board
        self.pos = pos
        self.name = name
        self.speed = 0.5  # от 0.1 до 1
        self.dir1 = (1, 0)  # освновное направление
        self.dir2 = (1, 0)  # если игрок изменил направление, когда в том направлении была стена, записывается сюда
        self.timer = -5000

    def change_dir(self, dr):
        self.dir2 = directions[dr][0]

    def can_move(self, direction):
        x, y = direction
        x1 = round(self.pos[0] + x * self.speed, 1)  # изменяет координаты в соответствии с направлением
        y1 = round(self.pos[1] + y * self.speed, 1)
        try:
            # assertы обрабатывают, можно ли пойти в этом направлении
            assert 0 <= x1 <= 13 and 0 <= y1 <= 13
            assert board.board[floor(y1)][floor(x1)] != 1
            assert board.board[ceil(y1)][ceil(x1)] != 1
            assert board.board[floor(y1)][ceil(x1)] != 1
            assert board.board[ceil(y1)][floor(x1)] != 1
            return (x1, y1)
        except IndexError:
            # если в какой-то момент Кушац у стены, то выползает IndexError
            return (x1, y1)
        except:
            return False

    def change_coords(self):
        for direction in [self.dir2, self.dir1]:  # сначала обрабатывает dir2, если не сработало - dir1
            a = self.can_move(direction)
            if a:
                self.pos = a
                self.dir1 = direction
                return True
        return False

    def get_image(self):
        # для картинок из таймаута
        if not self.check_state():
            im = self.name + 'angry' + str(pygame.time.get_ticks() // 200 % 2) + '.png'
            return load_image(im)
        # находит название направления
        for dr in directions:
            if directions[dr][0] == self.dir1:
                direction = directions[dr][1]
                break
        im = self.name + direction + str(pygame.time.get_ticks() // 200 % 2) + '.png'
        return load_image(im)

    def check_kush(self):
        return

    def check_state(self):
        return pygame.time.get_ticks() - self.timer > 5000


class Ghost(Entity):
    def __init__(self, pos, board, trajectory, name=None):
        self.name = name
        self.trajectory = trajectory
        self.board = board
        self.pos = pos
        self.point = 0  # к которой точке траектории направляется
        self.speed = 0.1
        self.dir1 = (0, 1)
        self.timer = -5000 # время последнего столкновения

    def move(self):
        if not self.check_state():
            # призраки не двигаются в режиме таймаута
            return
        if self.trajectory[self.point] == self.pos:
            self.point = (self.point + 1) % len(self.trajectory)
        x = self.trajectory[self.point][0] - self.pos[0]
        y = self.trajectory[self.point][1] - self.pos[1]
        if x != 0:
            x = abs(x) / x
        if y != 0:
            y = abs(y) / y
        self.dir1 = (x, y)
        x1 = round(self.pos[0] + x * self.speed, 1)
        y1 = round(self.pos[1] + y * self.speed, 1)
        self.pos = x1, y1

    def check_kush(self):
        # если кушац пересекается с призраком, то оба входят в режим таймаута - меняют спрайт
        # при этом кушац не может есть точки, а призраки не двигаются
        pos1 = self.board.kush.pos
        if abs(self.pos[0] - pos1[0]) < 0.5 and abs(self.pos[1] - pos1[1]) < 0.5 \
                and self.check_state() and \
                self.board.kush.check_state():
            self.timer = pygame.time.get_ticks()
            self.board.kush.timer = pygame.time.get_ticks()
            self.board.ghost_sound.play()
            survive = False
            for s in self.board.sweets:
                if s.collected and not s.eaten:
                    s.eaten = True
                    self.board.score -= 1000
                    survive = True
                    break
            if not survive:
                self.board.gameend = 1


class Chaser(Ghost):
    def change_dir(self, dir_x, dir_y):
        if self.can_move(dir_x) and dir_x != (0, 0):
            self.dir2 = dir_x
        elif self.can_move(dir_y) and dir_y != (0, 0):
            self.dir2 = dir_y
        else:
            self.dir2 = (0, 0)

    def move(self):
        if not self.check_state():
            return
            # чейзер, как и остальные призраки, не двигается в таймауте
        deltax = self.board.kush.pos[0] - self.pos[0]
        deltay = self.board.kush.pos[1] - self.pos[1]
        dir_x = (abs(deltax) / deltax if deltax != 0 else 0, 0)
        dir_y = (0, abs(deltay) / deltay if deltay != 0 else 0)
        self.change_dir(dir_x, dir_y)
        super().change_coords()


class Sweet:
    def __init__(self, board, name):
        self.board = board
        self.pos = self.board.generate_pos()
        self.name = name
        self.imsmall = load_image(self.name + '.png')
        self.imbig = load_image(self.name + '_big.png')
        self.collected = False  # собрано
        self.eaten = False  # съедено привидением


class Board:
    # поле
    def __init__(self, width, height):
        self.gameend = 0
        self.width = width
        self.height = height
        #         self.board = [[0] * width for _ in range(height)]      # для тестирования
        #         self.board[7] = [1] * 13 + [0]
        self.board = [[1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # собственно поле
                      [0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0],
                      [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0],
                      [0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1],
                      [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0],
                      [1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
                      [0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0],
                      [0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0],
                      [0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0],
                      [0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0],
                      [0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0],
                      [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1]]
        self.left = 50
        self.top = 50
        self.cell_size = 50
        self.portal = False    # портала нет, пока не собраны все точки
        self.portal_im = load_image('portal.png')
        self.kush = Entity([1, 12], self, 'kush')  # игрок
        self.sweets = []
        for name in ['donut', 'cherry', 'candycane']:
            sweet = Sweet(self, name)
            self.sweets.append(sweet)
        chaser = Chaser([12, 3], self, None, name='chaser')  # привидение которое движется к игроку
        cloudy = Ghost((1, 0), self, [(3, 0), (3, 9), (4, 9), (4, 11),
                                        (5, 11), (5, 13), (3, 13), (3, 11),
                                        (6, 11), (6, 12), (7, 12), (7, 13),
                                        (9, 13), (9, 9), (13, 9),
                                        (13, 12), (12, 12), (12, 13), (10, 13),
                                        (10, 12), (9, 12), (9, 10), (6, 10),
                                        (6, 11), (4, 11), (4, 9), (3, 9),
                                        (3, 2), (1, 2), (1, 0)], name='cloudy')
        mandarin = Ghost((10, 2), self, [(10, 0), (12, 0), (12, 1), (13, 1),
                                        (13, 3), (6, 3), (9, 3), (9, 0),
                                        (7, 0), (7, 1), (5, 1), (5, 2),
                                        (0, 2), (0, 1), (1, 1), (1, 0), (3, 0),
                                        (3, 3), (4, 3), (4, 2), (5, 2),
                                        (5, 0), (9, 0), (9, 2), (10, 2)], name='mandarin')
        self.ghosts = [chaser, cloudy, mandarin]
        self.score = 0
        self.ghost_sound = pygame.mixer.Sound('sounds/ghost attack.mp3')
        self.sweet_sound = pygame.mixer.Sound('sounds/sweet collected.mp3')
        self.won_sound = pygame.mixer.Sound('sounds/won.mp3')
        self.points_sound = pygame.mixer.Sound('sounds/eating points.mp3')
        self.points_sound_timer = -1000
        self.points_sound.set_volume(0.5 * volume)
        for sound in [self.ghost_sound, self.sweet_sound, self.won_sound]:
            sound.set_volume(volume)

    def check_collision(self):
        for s in self.sweets:
            if self.kush.pos == s.pos and self.kush.check_state() and not s.collected:
                s.collected = True
                self.score += 464
                self.sweet_sound.play()
        if self.portal == self.kush.pos and self.kush.check_state():
            self.gameend = 2
            self.won_sound.play()

    def generate_pos(self):
        w = self.width
        h = self.height
        n = randint(0, w * h - 1)
        pos = n % h, n // h
        poses = [s.pos for s in self.sweets]
        poses.append(tuple(self.kush.pos))
        while pos in poses or self.board[pos[1]][pos[0]] == 1:
            n = randint(0, w * h)
            pos = n % h, n // h
        return pos

    def render(self, screen):
        if self.kush.check_state():
            x, y = self.kush.pos
            x = int(int(x) + (x - int(x)) // 0.5)
            y = int(int(y) + (y - int(y)) // 0.5)
            if self.board[y][x] == 0:
                self.score += 12
                if pygame.time.get_ticks() - self.points_sound_timer > 50:
                    self.points_sound.play(0, 1000)
                    self.points_sound_timer = pygame.time.get_ticks()
            self.board[y][x] = 2
        for i in range(self.width):
            for j in range(self.height):
                cell = self.board[j][i]
                rct = (*self.get_coords([i, j]), self.cell_size, self.cell_size)
                if cell == 0:  # точки
                    screen.fill((255, 255, 0), rect=(rct[0] + self.cell_size // 2 - 5,
                                                     rct[1] + self.cell_size // 2 - 5, 10, 10))
        #for character in (self.kush, self.cloudy, self.chaser, self.mandarin):
        for character in (self.kush, *self.ghosts):
            screen.blit(character.get_image(), (self.get_coords(character.pos)))
            character.check_kush()
        for i, s in enumerate(self.sweets):
            if not s.eaten:
                if s.collected:
                    screen.blit(s.imsmall, (335 + 46 * i, 755))
                else:
                    screen.blit(s.imbig, self.get_coords(s.pos))
        if self.portal:
            screen.blit(self.portal_im, self.get_coords(self.portal))
        else:
            self.portal_necessity()
        score_text = font32.render(f'Score: {self.score}', True, (255, 217, 82))
        screen.blit(score_text, (530, 5))

    def get_coords(self, pos):  # преобразует позицию клетки в кординаты её левого верхнего угла
        x = pos[0] * self.cell_size + self.left
        y = pos[1] * self.cell_size + self.top
        return [x, y]

    def portal_necessity(self):
        for line in self.board:
            if not all([cell != 0 for cell in line]):
                return False    # не все точки собраны
        self.portal = self.generate_pos()   # все точки собраны, портал открылся


class Button:
    def __init__(self, coords, name):
        self.coords = coords
        self.name = name
        self.base = load_image(name + 'base.png')
        self.selected = load_image(name + 'selected.png')
        self.pressed = load_image(name + 'pressed.png')
        self.current = self.base
        self.size = self.base.get_size()

    def check_mouse(self, mouse):
        if self.coords[0] < mouse[0] < self.coords[0] + self.size[0] and \
                self.coords[1] < mouse[1] < self.coords[1] + self.size[1]:
            return True
        return False

    def check_selected(self, mouse):
        if self.check_mouse(mouse):
            self.current = self.selected
        else:
            self.current = self.base

    def check_pressed(self, mouse):
        if self.check_mouse(mouse):
            self.current = self.pressed
        else:
            self.current = self.base

    def change_coords(self, x, y):
        self.coords = x, y


class SoundWidget(Button):
    def __init__(self):
        self.coords = (0, 530)
        self.size = (70, 270)
        self.mainpics = [load_image(image) for image in ['sound0.png', 'sound1.png',
                                                         'sound2.png', 'sound3.png', 'soundoff.png']]
        self.slider0 = load_image('slider.png')
        self.slider1 = load_image('slider1.png')

    def get_main_image(self):
        if volume == 0:
            return self.mainpics[4]
        return self.mainpics[int(volume // 0.26)]

    def slider_coords(self):
        return (16, int(547 + (1 - volume) * 171))

    def slider_check(self, mouse):
        coords = self.slider_coords()
        if coords[0] < mouse[0] < coords[0] + self.slider1.get_width() and \
                coords[1] < mouse[1] < coords[1] + self.slider1.get_height():
            return True
        return False


def get_results():
    res = cur.execute("""SELECT * FROM results""").fetchall()
    if len(res) > 28:
        for i in range(len(res))[:-28]:
            cur.execute("""DELETE FROM results WHERE id = ?""", (res[i][2],))
            con.commit()
        res = res[28:]
    return res


def select_gameend_picture(score, total):
    scores = cur.execute("""SELECT score FROM results""").fetchall()
    if len(scores) != 0:
        maxs = max(scores, key=lambda x: x[0])[0]
        mins = min(scores, key=lambda x: x[0])[0]
    else:
        maxs = 0
        mins = 0
    if score > maxs or score < mins:
        newgame.change_coords(256, 468)
        if total == 1:
            table = load_image('gameover_hscore.png')
        elif board.gameend == 2:
            table = load_image('youwon_hscore.png')
    else:
        newgame.change_coords(256, 401)
        if total == 1:
            table = load_image('gameover.png')
        elif board.gameend == 2:
            table = load_image('youwon.png')
    return table

# основа
pygame.init()
pygame.display.set_caption("Kushats")
size = width, height = 800, 800
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()

# оформление
pygame.display.set_icon(load_image('icon.png'))
bg = Animated(['background0.png', 'background2.png', 'background1.png', 'background2.png'], 250)
res_bg = Animated(['res_background0.png', 'res_background2.png',
                   'res_background1.png', 'res_background2.png'], 250)
mainmenu = load_image('mainmenu.png')
pygame.mixer.music.load('sounds/menu.mp3')
pygame.mixer.music.play(-1, 5000, 1000)
newgame = Button((256, 401), 'newgame')
quit = Button((256, 613), 'quit')
results = Button((256, 507), 'results')
sound = SoundWidget()
font32 = load_font('18534.TTF', 32)
font38 = load_font('18534.TTF', 38)
font48 = load_font('18534.TTF', 48)

# для правильной работы программы
slider_grabbed = False
not_results = False
running = True
mainrunning = True

# база данных о результатах
con = sqlite3.connect('results.db')
cur = con.cursor()

while not not_results:
    while running:
        pygame.mixer.music.set_volume(volume)
        mouse = pygame.mouse.get_pos()
        newgame.check_selected(mouse)
        quit.check_selected(mouse)
        results.check_selected(mouse)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mainrunning = False
                running = False
                not_results = True
            elif event.type == pygame.KEYUP and event.key == 32:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                newgame.check_pressed(mouse)
                quit.check_pressed(mouse)
                results.check_pressed(mouse)
                if sound.slider_check(mouse):
                    slider_grabbed = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if newgame.check_mouse(mouse):
                    running = False
                    not_results = True
                elif quit.check_mouse(mouse):
                    running = False
                    mainrunning = False
                    not_results = True
                elif results.check_mouse(mouse):
                    running = False
                slider_grabbed = False
        screen.blit(mainmenu, (0, 0))
        screen.blit(newgame.current, newgame.coords)
        screen.blit(quit.current, quit.coords)
        screen.blit(results.current, results.coords)
        screen.blit(sound.get_main_image(), (0, 700))
        if sound.check_mouse(mouse) or slider_grabbed:
            screen.blit(sound.slider0, (27, 547))
            screen.blit(sound.slider1, sound.slider_coords())
        if slider_grabbed:
            volume = 1 - (mouse[1] - 547) / 171
            if volume > 1:
                volume = 1
            elif volume < 0:
                volume = 0
        pygame.display.flip()
    if not_results:
        break
    back = False
    res = get_results()
    if len(res) != 0:
        positive = max(res, key=lambda x: x[1])[1]
        if positive <= 0:
            positive = '-'
        negative = min(res, key=lambda x: x[1])[1]
        if negative >= 0:
            negative = '-'
    else:
        positive = '-'
        negative = '-'
    all_results_text = []
    for i, r in enumerate(res):
        status = 'fail' if r[0] == 1 else 'win'
        text0 = font38.render(f'{i + 1}', True, (255, 217, 82))
        text1 = font38.render(str(r[1]), True, (255, 217, 82))
        text2 = font38.render(status, True, (255, 217, 82))
        all_results_text.append((text0, text1, text2))
    positive_text = font48.render(str(positive), True, (255, 217, 82))
    negative_text = font48.render(str(negative), True, (255, 217, 82))
    score_txt = font38.render('Score', True, (255, 217, 82))
    total_txt = font38.render('Total', True, (255, 217, 82))
    back_btn = Button((63, 63), 'back')
    del_btn = Button((624, 63), 'del')
    while not back:
        pygame.mixer.music.set_volume(volume)
        mouse = pygame.mouse.get_pos()
        back_btn.check_selected(mouse)
        del_btn.check_selected(mouse)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mainrunning = False
                not_results = True
                back = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                back_btn.check_pressed(mouse)
                del_btn.check_pressed(mouse)
            elif event.type == pygame.MOUSEBUTTONUP:
                if back_btn.check_mouse(mouse):
                    back = True
                    running = True
                elif del_btn.check_mouse(mouse):
                    cur.execute("""DELETE FROM results""")
                    con.commit()
                    all_results_text = []
                    positive_text = font48.render('-', True, (255, 217, 82))
                    negative_text = font48.render('-', True, (255, 217, 82))
        screen.blit(res_bg.get_image(), (0, 0))
        for i in range(len(all_results_text)):
            x = i // ceil(len(all_results_text) / 2) * 390
            y = 345 + i % ceil(len(all_results_text) / 2) * 27
            w_num = all_results_text[i][0].get_width()
            w_score = all_results_text[i][1].get_width()
            screen.blit(all_results_text[i][0], (x + 90 - w_num, y))
            screen.blit(all_results_text[i][1], (x + 220 - w_score, y))
            screen.blit(all_results_text[i][2], (x + 270, y))
        screen.blit(back_btn.current, back_btn.coords)
        screen.blit(del_btn.current, del_btn.coords)
        screen.blit(total_txt, (260, 305))
        screen.blit(total_txt, (650, 305))
        screen.blit(score_txt, (120, 305))
        screen.blit(score_txt, (510, 305))
        screen.blit(positive_text, (454, 157))
        screen.blit(negative_text, (454, 215))
        pygame.display.flip()

while mainrunning:
    pygame.mixer.music.unload()
    pygame.mixer.music.load('sounds/start.mp3')
    pygame.mixer.music.play(fade_ms=100)
    board = Board(14, 14)
    while not board.gameend:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYUP:  # стрелки
                if 1073741903 <= event.key <= 1073741906:
                    board.kush.change_dir(event.key - 1073741903)
                else:
                    print(event.key)
        clock.tick(50)
        screen.blit(bg.get_image(), (0, 0))
        board.kush.change_coords()
        for ghost in board.ghosts:
            ghost.move()
        board.check_collision()
        board.render(screen)
        pygame.display.flip()
    pygame.time.wait(1850)
    running = True
    pygame.mixer.music.load('sounds/menu.mp3')
    pygame.mixer.music.play(-1, 5000, 1000)
    table = select_gameend_picture(board.score, board.gameend)
    cur.execute("""INSERT INTO results(total, score) VALUES(?, ?)""",
                (board.gameend, board.score))
    con.commit()
    get_results()

    while running:
        mouse = pygame.mouse.get_pos()
        newgame.check_selected(mouse)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mainrunning = False
                running = False
            elif event.type == pygame.KEYUP and event.key == 32:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                newgame.check_pressed(mouse)
            elif event.type == pygame.MOUSEBUTTONUP:
                if newgame.check_mouse(mouse):
                    running = False
        screen.blit(bg.get_image(), (0, 0))
        screen.blit(table, (0, 0))
        score_text = load_font('18534.TTF', 64).render(f'Score: {board.score}', True, (255, 217, 82))
        screen.blit(score_text, (400 - score_text.get_width() // 2, 333))
        screen.blit(newgame.current, newgame.coords)
        pygame.display.flip()
pygame.quit()
con.close()
