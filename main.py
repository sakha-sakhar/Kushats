import pygame
import sys
import os
from math import ceil, floor
from random import randint

directions = {0: ((1, 0), 'right'),  # вправо
              1: ((-1, 0), 'left'),  # влево
              2: ((0, 1), 'down'),  # вниз
              3: ((0, -1), 'up'),  # вверх
              -1: ((0, 0), 'stop')}   # стоп


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


class Entity:  # сущность - думаю, можно или объединить в этом классе игрока и призраков, либо какие-то из них унаследовать от этого класса.
    def __init__(self, pos, board, name):
        self.board = board
        self.pos = pos
        self.name = name
        self.speed = 0.5  # от 0.1 до 1
        self.dir1 = (1, 0)  # освновное направление
        self.dir2 = (1, 0)  # если игрок изменил направление тогда, когда в том направлении была стена, записывается сюда
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


class Ghost:
    def __init__(self, pos, board, trajectory, color, name=None):
        self.color = color
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

    def get_image(self):
        return Entity.get_image(self)

    def check_kush(self):
        # если кушац пересекается с призраком, то оба входят в режим таймаута - меняют спрайт
        # при этом кушац не может есть точки, а призраки не двигаются
        pos1 = self.board.kush.pos
        if abs(self.pos[0] - pos1[0]) < 0.5 and abs(self.pos[1] - pos1[1]) < 0.5 \
                and self.check_state() and \
                self.board.kush.check_state():
            self.timer = pygame.time.get_ticks()
            self.board.kush.timer = pygame.time.get_ticks()
            survive = False
            for s in self.board.sweets:
                if s.collected and not s.eaten:
                    s.eaten = True
                    self.board.score -= 1000
                    survive = True
                    break
            if not survive:
                self.board.gameend = 1


    def check_state(self):
        return pygame.time.get_ticks() - self.timer > 5000


class Chaser(Entity, Ghost):
    def __init__(self, board, pos):
        super().__init__(board, pos, 'chaser')
        self.color = (225, 0, 255)
        self.speed = 0.1
        self.timer = -5000

    def change_dir(self, dir_x, dir_y):
        if self.can_move(dir_x) and dir_x != (0, 0):
            self.dir2 = dir_x
        elif self.can_move(dir_y) and dir_y != (0, 0):
            self.dir2 = dir_y
        else:
            self.dir2 = (0, 0)

    def change_coords(self):
        if not self.check_state():
            return
            # чейзер, как и остальные призраки, не двигается в таймауте
        deltax = self.board.kush.pos[0] - self.pos[0]
        deltay = self.board.kush.pos[1] - self.pos[1]
        dir_x = (abs(deltax) / deltax if deltax != 0 else 0, 0)
        dir_y = (0, abs(deltay) / deltay if deltay != 0 else 0)
        self.change_dir(dir_x, dir_y)
        super().change_coords()

    def check_kush(self):
        Ghost.check_kush(self)


class Sweet:
    def __init__(self, board, name):
        self.board = board
        self.pos = self.board.generate_pos()
        self.name = name
        self.im = load_image(self.name + '.png')
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
        self.font = load_font('18534.TTF', 32)
        self.portal_im = load_image('portal.png')
        self.kush = Entity([1, 12], self, 'kush')  # игрок
        self.sweets = []
        for name in ['donut', 'cherry', 'candycane']:
            sweet = Sweet(self, name)
            self.sweets.append(sweet)
        self.chaser = Chaser([12, 3], self)  # привидение которое движется к игроку
        self.cloudy = Ghost((1, 0), self, [(3, 0), (3, 9), (4, 9), (4, 11),
                                           (5, 11), (5, 13), (3, 13), (3, 11),
                                           (6, 11), (6, 12), (7, 12), (7, 13),
                                           (9, 13), (9, 9), (13, 9),
                                           (13, 12), (12, 12), (12, 13), (10, 13),
                                           (10, 12), (9, 12), (9, 10), (6, 10),
                                           (6, 11), (4, 11), (4, 9), (3, 9),
                                           (3, 2), (1, 2), (1, 0)], (205, 92, 92), name='cloudy')
        self.mandarin = Ghost((10, 2), self, [(10, 0), (12, 0), (12, 1), (13, 1),
                                            (13, 3), (6, 3), (9, 3), (9, 0),
                                            (7, 0), (7, 1), (5, 1), (5, 2),
                                            (0, 2), (0, 1), (1, 1), (1, 0), (3, 0),
                                            (3, 3), (4, 3), (4, 2), (5, 2),
                                            (5, 0), (9, 0), (9, 2), (10, 2)], (255, 140, 0), name='mandarin')
        self.score = 0

    def check_collision(self):
        for s in self.sweets:
            if self.kush.pos == s.pos and self.kush.check_state() and not s.collected:
                s.collected = True
                self.score += 464
        if self.portal == self.kush.pos and self.kush.check_state():
            self.gameend = 2

    def generate_pos(self):
        w = self.width
        h = self.height
        n = randint(0, w * h - 1)
        pos = n % h, n // h
        poses = [s.pos for s in self.sweets]
        poses.append(self.kush.pos)
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
            self.board[y][x] = 2
        for i in range(self.width):
            for j in range(self.height):
                cell = self.board[j][i]
                rct = (*self.get_coords([i, j]), self.cell_size, self.cell_size)
                if cell == 0:  # точки
                    screen.fill((255, 255, 0), rect=(rct[0] + self.cell_size // 2 - 5,
                                                     rct[1] + self.cell_size // 2 - 5, 10, 10))
        for character in (self.kush, self.cloudy, self.chaser, self.mandarin):
            screen.blit(character.get_image(), (self.get_coords(character.pos)))
            character.check_kush()
        screen.blit(self.kush.get_image(), (self.get_coords(self.kush.pos)))
        for i, s in enumerate(self.sweets):
            if not s.eaten:
                y = 755
                if s.collected:
                    x = 335 + 46 * i
                else:
                    x, y = self.get_coords(s.pos)
                screen.blit(s.im, (x, y))
        if self.portal:
            screen.blit(self.portal_im, self.get_coords(self.portal))
        else:
            self.portal_necessity()
        score_text = self.font.render(f'Score: {self.score}', True, (255, 217, 82))
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


pygame.init()
pygame.display.set_caption("Kushats")
size = width, height = 800, 800
screen = pygame.display.set_mode(size)
screen.blit(load_image('background0.png'), (0, 0))
clock = pygame.time.Clock()
mainrunning = True
while mainrunning:
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
        screen.blit(load_image('background' + str(pygame.time.get_ticks() // 500 % 2) + '.png'), (0, 0))
        board.kush.change_coords()
        board.chaser.change_coords()
        board.cloudy.move()
        board.mandarin.move()
        board.check_collision()
        board.render(screen)
        pygame.display.flip()
    pygame.time.wait(1000)
    running = True
    while running:
        x, y = pygame.mouse.get_pos()
        if 250 < x < 550 and 400 < y < 500:
            btnstate = 'selected'
        else:
            btnstate = 'base'
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mainrunning = False
                running = False
            elif event.type == pygame.KEYUP and event.key == 32:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and 250 < event.pos[0] < 550 and 400 < event.pos[1] < 500:
                btnstate = 'pressed'
            elif event.type == pygame.MOUSEBUTTONUP and 250 < event.pos[0] < 550 and 400 < event.pos[1] < 500:
                running = False
                btnstate = 'base'
        screen.blit(load_image('background' + str(pygame.time.get_ticks() // 500 % 2) + '.png'), (0, 0))
        if board.gameend == 1:
            screen.blit(load_image('gameover.png'), (0, 0))
        elif board.gameend == 2:
            screen.blit(load_image('youwon.png'), (0, 0))
        score_text = load_font('18534.TTF', 64).render(f'Score: {board.score}', True, (255, 217, 82))
        screen.blit(score_text, (400 - score_text.get_width() // 2, 333))
        screen.blit(load_image('newgame' + btnstate + '.png'), (0, 0))
        pygame.display.flip()
pygame.quit()