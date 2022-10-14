import pygame
import sys
import os
import sqlite3
from math import ceil, floor
from random import randint, choice

directions = {0: ((1, 0), 'right'),  # вправо
              1: ((-1, 0), 'left'),  # влево
              2: ((0, 1), 'down'),  # вниз
              3: ((0, -1), 'up'),  # вверх
              -1: ((0, 0), 'stop')}   # стоп

volume = 0.3  # громкость музыки

difficulty = 2

# скорость кушаца, призраков, модель поведения мандарина и клауди
diffs = {0: (0.25, 0.0625, 0),
         1: (0.5, 0.1, 1),
         2: (0.5, 0.25, 1)}


def load_image(name, colorkey=None):
    fullname = os.path.join('images', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        fullname = os.path.join('images', 'noimage.png')
        # sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def load_font(name, font_size):
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
        return pygame.font.Font(fullname, font_size)
    else:
        sys.exit()


class Animated:
    def __init__(self, images, delay):
        self.images = [load_image(image) for image in images]
        self.delay = delay

    def get_image(self):
        return self.images[pygame.time.get_ticks() // self.delay % len(self.images)]


class Entity:  # сущность - игрок и призраки
    def __init__(self, pos, brd, name, speed=0.5):
        self.board = brd
        self.pos = pos
        self.name = name
        self.speed = speed  # от 0.1 до 1
        self.dir1 = (1, 0)  # освновное направление
        self.dir2 = (1, 0)  # если игрок изменил направление, когда в том направлении была стена, записывается сюда
        self.timer = -5000

    def change_dir(self, dr):
        self.dir2 = directions[dr][0]

    def can_move(self, direction):
        x0, y0 = direction
        x1 = round(self.pos[0] + x0 * self.speed, 4)  # изменяет координаты в соответствии с направлением
        y1 = round(self.pos[1] + y0 * self.speed, 4)
        tf = True
        try:
            # assertы обрабатывают, можно ли пойти в этом направлении
            assert 0 <= x1 <= 13 and 0 <= y1 <= 13
            assert board.board[floor(y1)][floor(x1)] != 1
            assert board.board[ceil(y1)][ceil(x1)] != 1
            assert board.board[floor(y1)][ceil(x1)] != 1
            assert board.board[ceil(y1)][floor(x1)] != 1
        except IndexError:
            pass
        except Exception:   # наверное, следует как-то переписать
            x1 = self.pos[0]
            y1 = self.pos[1]
            if x0 == 1:
                x1 = ceil(x1)
            elif x0 == -1:
                x1 = floor(x1)
            if y0 == 1:
                y1 = ceil(y1)
            elif y0 == -1:
                y1 = floor(y1)
            if self.pos[0] == x1 and self.pos[1] == y1:
                tf = False
        return x1, y1, tf

    def change_coords(self):
        # сначала обрабатывает dir2
        # он в приоритете, но если мы не можем двигаться по направлению dir2,
        # мы направление пока не меняем
        a = self.can_move(self.dir2)
        if a[2]:
            self.pos = (a[0], a[1])
            self.dir1 = self.dir2
            return True
        a = self.can_move(self.dir1)
        self.pos = (a[0], a[1])
        return a[2]

    def get_image(self):
        # для картинок из таймаута
        if not self.check_state():
            im = self.name + 'angry' + str(pygame.time.get_ticks() // 200 % 2) + '.png'
            return load_image(im)
        # находит название направления
        direction = ''
        for dr in directions:
            if directions[dr][0] == self.dir1:
                direction = directions[dr][1]
                break
        if direction:
            im = self.name + direction + str(pygame.time.get_ticks() // 200 % 2) + '.png'
        else:
            im = 'ERROR.png'
        return load_image(im)

    def check_kush(self):
        return

    def check_state(self):
        return pygame.time.get_ticks() - self.timer > 5000


class Ghost(Entity):
    def __init__(self, pos, brd, trajectory, name='', speed=0.1):
        super().__init__(pos, brd, name)
        self.trajectory = trajectory
        self.point = 0  # к которой точке траектории направляется
        self.speed = speed

    def move(self):
        if not self.check_state():
            # призраки не двигаются в режиме таймаута
            return
        if self.trajectory:
            if self.trajectory[self.point] == self.pos:
                self.point = (self.point + 1) % len(self.trajectory)
            x = self.trajectory[self.point][0] - self.pos[0]
            y = self.trajectory[self.point][1] - self.pos[1]
            if x != 0:
                x = abs(x) / x
            if y != 0:
                y = abs(y) / y
            self.dir1 = (x, y)
            x1 = round(self.pos[0] + x * self.speed, 4)
            y1 = round(self.pos[1] + y * self.speed, 4)
            self.pos = x1, y1
        else:
            if not self.change_coords():
                d1 = (self.dir2[1], self.dir2[0])
                d2 = (-self.dir2[1], -self.dir2[0])
                if self.can_move(d1)[2]:
                    if self.can_move(d2)[2]:
                        d = choice((d1, d2))
                    else:
                        d = d1
                elif self.can_move(d2)[2]:
                    d = d2
                else:
                    d = (-self.dir2[0], -self.dir2[1])
                self.dir2 = d

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
    def __init__(self, pos, brd, speed=0.1):
        super().__init__(pos, brd, None, 'chaser', speed)

    def change_dir(self, dir_x, dir_y):
        if self.can_move(dir_x)[2] and dir_x != (0, 0):
            self.dir2 = dir_x
        elif self.can_move(dir_y)[2] and dir_y != (0, 0):
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
    def __init__(self, brd, name):
        self.board = brd
        self.pos = self.board.generate_pos()
        self.name = name
        self.imsmall = load_image(self.name + '.png')
        self.imbig = load_image(self.name + '_big.png')
        self.collected = False  # собрано
        self.eaten = False  # съедено привидением


class Board:
    # поле
    def __init__(self, difsets):
        self.gameend = 0
        self.width = self.height = 14
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
        self.portal = -1, -1    # портала нет, пока не собраны все точки
        self.portal_im = load_image('portal.png')
        self.kush = Entity([1, 12], self, 'kush', speed=difsets[0])  # игрок
        self.sweets = []
        for name in ['donut', 'cherry', 'candycane']:
            sweet = Sweet(self, name)
            self.sweets.append(sweet)
        chaser = Chaser([12, 3], self, speed=difsets[1])  # привидение которое движется к игроку
        if not difsets[2]:
            cloudy = Ghost((1, 0), self, [(3, 0), (3, 9), (4, 9), (4, 11),
                                          (5, 11), (5, 13), (3, 13), (3, 11),
                                          (6, 11), (6, 12), (7, 12), (7, 13),
                                          (9, 13), (9, 9), (13, 9),
                                          (13, 12), (12, 12), (12, 13), (10, 13),
                                          (10, 12), (9, 12), (9, 10), (6, 10),
                                          (6, 11), (4, 11), (4, 9), (3, 9),
                                          (3, 2), (1, 2), (1, 0)], name='cloudy', speed=difsets[1])
            mandarin = Ghost((10, 2), self, [(10, 0), (12, 0), (12, 1), (13, 1),
                                             (13, 3), (6, 3), (9, 3), (9, 0),
                                             (7, 0), (7, 1), (5, 1), (5, 2),
                                             (0, 2), (0, 1), (1, 1), (1, 0), (3, 0),
                                             (3, 3), (4, 3), (4, 2), (5, 2),
                                             (5, 0), (9, 0), (9, 2), (10, 2)], name='mandarin', speed=difsets[1])
        else:
            cloudy = Ghost((1, 0), self, None, name='cloudy', speed=difsets[1])
            mandarin = Ghost((10, 2), self, None, name='mandarin', speed=difsets[1])
        self.ghosts = [chaser, cloudy, mandarin]
        self.score = 0
        self.ghost_sound = pygame.mixer.Sound('sounds/ghost attack.mp3')
        self.sweet_sound = pygame.mixer.Sound('sounds/sweet collected.mp3')
        self.won_sound = pygame.mixer.Sound('sounds/won.mp3')
        self.points_sound = pygame.mixer.Sound('sounds/eating points.mp3')
        self.points_sound_timer = -1000
        self.points_sound.set_volume(0.5 * volume)
        for snd in [self.ghost_sound, self.sweet_sound, self.won_sound]:
            snd.set_volume(volume)

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
            n = randint(0, w * h - 1)
            pos = n % h, n // h
        return pos

    def render(self, scrn):
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
        for _i in range(self.width):
            for _j in range(self.height):
                cell = self.board[_j][_i]
                rct = (*self.get_coords([_i, _j]), self.cell_size, self.cell_size)
                if cell == 0:  # точки
                    scrn.fill((255, 255, 0), rect=(rct[0] + self.cell_size // 2 - 5,
                                                   rct[1] + self.cell_size // 2 - 5, 10, 10))
        for char in (self.kush, *self.ghosts):
            scrn.blit(char.get_image(), (self.get_coords(char.pos)))
            char.check_kush()
        for n, swt in enumerate(self.sweets):
            if not swt.eaten:
                if swt.collected:
                    scrn.blit(swt.imsmall, (335 + 46 * n, 755))
                else:
                    scrn.blit(swt.imbig, self.get_coords(swt.pos))
        if self.portal != (-1, -1):
            scrn.blit(self.portal_im, self.get_coords(self.portal))
        else:
            self.portal_necessity()
        scoretxt = font32.render(f'Score: {self.score}', True, (255, 217, 82))
        scrn.blit(scoretxt, (530, 5))

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


class CharacterBtn(Button):
    def __init__(self, coords, name):
        self.coords = coords
        self.name = name
        self.base0 = load_image(name + 'right0.png')
        self.base1 = load_image(name + 'right1.png')
        self.angry0 = load_image(name + 'angry0.png')
        self.angry1 = load_image(name + 'angry1.png')
        self.info = load_image(name + 'info.png')
        self.size = self.base0.get_size()
        self.selected = 0  # 0 - не выбран, 1 - наведён курсор, 2 - выбран, 3 - нажат

    def get_image(self):
        if not self.selected:
            return self.base0
        elif self.selected in (1, 2):
            if pygame.time.get_ticks() // 200 % 2 == 0:
                return self.base0
            return self.base1
        if pygame.time.get_ticks() // 200 % 2 == 0:
            return self.angry0
        return self.angry1

    def check_selected(self, mouse):
        if self.selected in (2, 3):
            self.current = self.get_image()
            return
        if self.check_mouse(mouse):
            self.selected = 1
        else:
            self.selected = 0
        self.current = self.get_image()

    def check_pressed(self, mouse):
        if not self.check_mouse(mouse):
            if self.selected in (1, 2, 3):
                self.selected = 0
            return
        if self.selected == 1:
            self.selected = 2
        elif self.selected == 2:
            self.selected = 3
        else:
            self.selected = 2


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
        return 16, int(547 + (1 - volume) * 171)

    def slider_check(self, mouse_coord):
        coords = self.slider_coords()
        if coords[0] < mouse_coord[0] < coords[0] + self.slider1.get_width() and \
                coords[1] < mouse_coord[1] < coords[1] + self.slider1.get_height():
            return True
        return False


def get_results():
    res_s = cur.execute("""SELECT * FROM results""").fetchall()
    if len(res_s) > 28:
        for i in range(len(res_s))[:-28]:
            cur.execute("""DELETE FROM results WHERE id = ?""", (res_s[i][2],))
            con.commit()
        res_s = res_s[28:]
    return res_s


def select_gameend_picture(score, total):
    scores = cur.execute("""SELECT score FROM results""").fetchall()
    maxs = mins = 0
    if len(scores) != 0:
        maxs = max(scores, key=lambda a: a[0])[0]
        mins = min(scores, key=lambda b: b[0])[0]
    im = 'gameover' if total == 1 else 'youwon'
    print(score, maxs, mins)
    if maxs < score > 0 or mins > score < 0:
        newgame.change_coords(256, 468)
        im += '_hscore'
    else:
        newgame.change_coords(256, 401)
    return load_image(im + '.png')


def buttons_moving():
    for btn in characters:
        if btn.check_mouse(mouse_pos) and newgame.coords[0] == 256:
            for butn in [newgame, quitbtn1, results, *characters]:
                butn.change_coords(butn.coords[0] - 195, butn.coords[1])
            return None
    if newgame.coords[0] != 256 and not any([ch.check_mouse(mouse_pos) for ch in characters]):
        for butn in [newgame, quitbtn1, results, *characters]:
            butn.change_coords(butn.coords[0] + 195, butn.coords[1])


def terminate():
    con.close()
    pygame.quit()
    sys.exit()


def main_menu(sldr_grabbed, menu_run, game_run, result_run, set_run):
    for btn in [newgame, quitbtn1, results, setbtn, *characters]:
        btn.check_selected(mouse_pos)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        elif event.type == pygame.KEYUP and event.key == 32:
            menu_run = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            newgame.check_pressed(mouse_pos)
            quitbtn1.check_pressed(mouse_pos)
            results.check_pressed(mouse_pos)
            setbtn.check_pressed(mouse_pos)
            if sound.slider_check(mouse_pos):
                sldr_grabbed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if newgame.check_mouse(mouse_pos):
                menu_run = False
                game_run = True
            elif quitbtn1.check_mouse(mouse_pos):
                terminate()
            elif results.check_mouse(mouse_pos):
                menu_run = False
                result_run = True
            elif setbtn.check_mouse(mouse_pos):
                menu_run = False
                set_run = True
            for btn in characters:
                btn.check_pressed(mouse_pos)
            buttons_moving()
            sldr_grabbed = False
    screen.blit(mainmenu, (0, 0))
    for btn in [newgame, quitbtn1, results, setbtn, *characters]:
        screen.blit(btn.current, btn.coords)
    for btn in characters:
        if btn.selected in (2, 3):
            screen.blit(btn.info, (0, 0))
    screen.blit(sound.get_main_image(), (0, 700))
    if sound.check_mouse(mouse_pos) or slider_grabbed:
        screen.blit(sound.slider0, (27, 547))
        screen.blit(sound.slider1, sound.slider_coords())
    pygame.display.flip()
    return sldr_grabbed, menu_run, game_run, result_run, set_run


def results_text_render():
    text = []
    for i, r in enumerate(res):
        status = 'fail' if r[0] == 1 else 'win'
        text0 = font38.render(f'{i + 1}', True, (255, 217, 82))
        text1 = font38.render(str(r[1]), True, (255, 217, 82))
        text2 = font38.render(status, True, (255, 217, 82))
        text.append((text0, text1, text2))
    return text


def results_window(rslt_txt, result_run, menu_run):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            back_btn.check_pressed(mouse_pos)
            del_btn.check_pressed(mouse_pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if back_btn.check_mouse(mouse_pos):
                result_run = False
                menu_run = True
            elif del_btn.check_mouse(mouse_pos):
                cur.execute("""DELETE FROM results""")
                con.commit()
                rslt_txt = []
    screen.blit(sbg.get_image(), (0, 0))
    screen.blit(res_bg, (0, 0))
    for i in range(len(rslt_txt)):
        x_coord = i // ceil(len(rslt_txt) / 2) * 390
        y_coord = 345 + i % ceil(len(rslt_txt) / 2) * 27
        w_num = rslt_txt[i][0].get_width()
        w_score = rslt_txt[i][1].get_width()
        screen.blit(rslt_txt[i][0], (x_coord + 90 - w_num, y_coord))
        screen.blit(rslt_txt[i][1], (x_coord + 220 - w_score, y_coord))
        screen.blit(rslt_txt[i][2], (x_coord + 270, y_coord))
    screen.blit(back_btn.current, back_btn.coords)
    screen.blit(del_btn.current, del_btn.coords)
    screen.blit(total_txt, (260, 305))
    screen.blit(total_txt, (650, 305))
    screen.blit(score_txt, (120, 305))
    screen.blit(score_txt, (510, 305))
    return rslt_txt, result_run, menu_run


def settings_window(set_run, menu_run):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            back_btn.check_pressed(mouse_pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if back_btn.check_mouse(mouse_pos):
                set_run = False
                menu_run = True
    screen.blit(sbg.get_image(), (0, 0))
    screen.blit(set_bg, (0, 0))
    screen.blit(back_btn.current, back_btn.coords)
    return set_run, menu_run


def game_window(game_run, start_time):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        if event.type == pygame.KEYUP:  # стрелки
            if 1073741903 <= event.key <= 1073741906:
                board.kush.change_dir(event.key - 1073741903)
            else:
                print(event.key)
    clock.tick(37)
    timer = (pygame.time.get_ticks() - start_time) // 60000
    if timer == 1:
        board.score = round(board.score * 0.9)
        start_time += 60000
    screen.blit(bg.get_image(), (0, 0))
    board.kush.change_coords()
    for ghost in board.ghosts:
        ghost.move()
    board.check_collision()
    board.render(screen)
    pygame.display.flip()
    return game_run, start_time


def game_over_window(game_over_run, game_run, menu_run, results_run):
    for btn in [newgame, menu, results1, quitbtn2]:
        btn.check_selected(mouse_pos)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        elif event.type == pygame.KEYUP and event.key == 32:
            game_over_run = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            newgame.check_pressed(mouse_pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if newgame.check_mouse(mouse_pos):
                game_over_run = False
            if menu.check_mouse(mouse_pos):
                game_over_run = False
                game_run = False
                menu_run = True
            elif results1.check_mouse(mouse_pos):
                game_over_run = False
                game_run = False
                results_run = True
            elif quitbtn2.check_mouse(mouse_pos):
                terminate()
    screen.blit(bg.get_image(), (0, 0))
    screen.blit(table, (0, 0))
    score_text = font64.render(f'Score: {board.score}', True, (255, 217, 82))
    screen.blit(score_text, (400 - score_text.get_width() // 2, 333))
    for btn in [newgame, menu, results1, quitbtn2]:
        screen.blit(btn.current, btn.coords)
    pygame.display.flip()
    return game_over_run, game_run, menu_run, results_run


# основа
pygame.init()
pygame.display.set_caption("Kushats")
size = width, height = 800, 800
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()

# оформление
pygame.display.set_icon(load_image('icon.png'))
bg = Animated(['background0.png', 'background2.png', 'background1.png', 'background2.png'], 250)
res_bg = load_image('resultsbg.png')
set_bg = load_image('settingsbg.png')
sbg = Animated(['sbg0.png', 'sbg2.png',
                'sbg1.png', 'sbg2.png'], 250)
mainmenu = load_image('mainmenu.png')
pygame.mixer.music.load('sounds/menu.mp3')
pygame.mixer.music.play(-1, 5000, 1000)
newgame = Button((256, 401), 'newgame')
quitbtn1 = Button((256, 613), 'quit')
results = Button((256, 507), 'results')
menu = Button((0, 0), 'menu')
results1 = Button((0, 50), 'results1')
quitbtn2 = Button((0, 90), 'quit1')
setbtn = Button((66, 747), 'set')
sound = SoundWidget()
font32 = load_font('18534.TTF', 32)
font38 = load_font('18534.TTF', 38)
font48 = load_font('18534.TTF', 48)
font64 = load_font('18534.TTF', 64)
score_txt = font38.render('Score', True, (255, 217, 82))
total_txt = font38.render('Total', True, (255, 217, 82))
back_btn = Button((63, 63), 'back')
del_btn = Button((624, 63), 'del')
characters = []
for j, character in enumerate(['kush', 'chaser', 'mandarin', 'cloudy']):
    characters.append(CharacterBtn((570, 415 + 70 * j), character))

# для правильной работы программы
slider_grabbed = False
running = True
menurunning = True
gamerunning = False
resultsrunning = False
setrunning = False

# база данных о результатах и настройках
con = sqlite3.connect('data.db')
cur = con.cursor()

while running:
    while menurunning:
        mouse_pos = pygame.mouse.get_pos()
        slider_grabbed, menurunning, gamerunning, resultsrunning, setrunning = main_menu(
            slider_grabbed, menurunning, gamerunning, resultsrunning, setrunning)
        if slider_grabbed:
            volume = 1 - (mouse_pos[1] - 547) / 171
            if volume > 1:
                volume = 1
            elif volume < 0:
                volume = 0
        pygame.mixer.music.set_volume(volume)

    while setrunning:
        mouse_pos = pygame.mouse.get_pos()
        back_btn.check_selected(mouse_pos)
        setrunning, menurunning = settings_window(setrunning, menurunning)
        pygame.display.flip()
    res = get_results()
    positive = '-'
    negative = '-'
    if len(res) != 0:
        temp = max(res, key=lambda n: n[1])[1]
        if temp > 0:
            positive = temp
        temp = min(res, key=lambda m: m[1])[1]
        if temp < 0:
            negative = temp
    all_results_text = results_text_render()
    positive_text = font48.render(str(positive), True, (255, 217, 82))
    negative_text = font48.render(str(negative), True, (255, 217, 82))
    while resultsrunning:
        mouse_pos = pygame.mouse.get_pos()
        back_btn.check_selected(mouse_pos)
        del_btn.check_selected(mouse_pos)
        all_results_text, resultsrunning, menurunning = results_window(
            all_results_text, resultsrunning, menurunning)
        if not all_results_text:
            positive_text = font48.render('-', True, (255, 217, 82))
            negative_text = font48.render('-', True, (255, 217, 82))
        screen.blit(positive_text, (454, 157))
        screen.blit(negative_text, (454, 215))
        pygame.display.flip()

    while gamerunning:
        pygame.mixer.music.unload()
        pygame.mixer.music.load('sounds/start.mp3')
        pygame.mixer.music.play(fade_ms=100)
        board = Board(diffs[difficulty])
        starttime = pygame.time.get_ticks()
        #
        #
        #
        while not board.gameend:
            gamerunning, starttime = game_window(gamerunning, starttime)
        pygame.time.wait(1850)
        pygame.mixer.music.load('sounds/menu.mp3')
        pygame.mixer.music.play(-1, 5000, 1000)
        table = select_gameend_picture(board.score, board.gameend)
        cur.execute("""INSERT INTO results(total, score) VALUES(?, ?)""",
                    (board.gameend, board.score))
        con.commit()
        get_results()
        gameoverrunning = True
        while gameoverrunning:
            mouse_pos = pygame.mouse.get_pos()
            gameoverrunning, gamerunning, menurunning, resultsrunning = game_over_window(
                gameoverrunning, gamerunning, menurunning, resultsrunning)
        newgame.change_coords(256, 401)
terminate()
