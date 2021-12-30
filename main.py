import pygame
import sys
import os
from math import ceil, floor


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


class Entity:  # сущность - думаю, можно или объединить в этом классе игрока и призраков, либо какие-то из них унаследовать от этого класса.
    def __init__(self, pos, board, name):
        self.board = board
        self.pos = pos
        self.name = name
        self.speed = 0.1 # от 0.1 до 1
        self.dir1 = 0  # освновное направление
        self.dir2 = 0  # если игрок изменил направление тогда, когда в том направлении была стена, записывается сюда
        self.directions = {0: ((1, 0), 'right'),    # вправо
                           1: ((-1, 0), 'left'),   # влево
                           2: ((0, 1), 'down'),    # вниз
                           3: ((0, -1), 'up')}   # вверх
        
    def change_dir(self, dr):
        self.dir2 = dr
    
    def change_coords(self):
        for direction in [self.dir2, self.dir1]:  # сначала обрабатывает dir2, если не сработало - dir1
            x, y = self.directions[direction][0]
            x1 = round(self.pos[0] + x * self.speed, 1)   # изменяет координаты в соответствии с направлением
            y1 = round(self.pos[1] + y * self.speed, 1)
            try:
                # assertы обрабатывают, можно ли пойти в этом направлении
                assert 0 <= x1 <= 13 and 0 <= y1 <= 13
                assert board.board[floor(y1)][floor(x1)] != 1
                assert board.board[ceil(y1)][ceil(x1)] != 1
                assert board.board[floor(y1)][ceil(x1)] != 1
                assert board.board[ceil(y1)][floor(x1)] != 1
                self.pos[0] = x1
                self.pos[1] = y1
                self.dir1 = direction
                # если можно, то координаты меняются, и, если это был dir2, то он становится основным направлением
                # и dir1 не обрабатывается
                return
            except IndexError:
                # если в какой-то момент Кушац у стены, то выползает IndexError
                self.pos[0] = x1
                self.pos[1] = y1
                self.dir1 = direction
                return
            except:
                pass

    def get_image(self):
        im = self.name + self.directions[self.dir1][1] + str(pygame.time.get_ticks() // 200 % 2) + '.png'
        return load_image(im)
            

class Board:
    # поле
    def __init__(self, width, height):
        self.width = width
        self.height = height
#         self.board = [[0] * width for _ in range(height)]      # лля тестирования
#         self.board[7] = [1] * 13 + [0] 
        self.board = [[1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],     # собственно поле
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
        self.kush = Entity([1, 12], self, 'kush')   # игрок

    def render(self, screen):
        x, y = self.kush.pos
        x = int(int(x) + (x - int(x)) // 0.5)
        y = int(int(y) + (y - int(y)) // 0.5)
        self.board[y][x] = 2
        for i in range(self.width):
            for j in range(self.height):
                a = self.board[j][i]
                rct = (*self.get_coords([i, j]), self.cell_size, self.cell_size)
                # pygame.draw.rect(screen, (255, 255, 255), rect=rct, width=1)
                # if a == 1:  # стены
                #     screen.fill((255, 0, 0), rect=rct)
                if a == 0:  # точки
                    screen.fill((255, 255, 0), rect=(rct[0] + self.cell_size // 2 - 5, rct[1] + self.cell_size // 2 - 5, 10, 10))
        screen.blit(self.kush.get_image(), (self.get_coords(self.kush.pos)))
        
            
    def get_coords(self, pos):   # преобразует позицию клетки в кординаты её левого верхнего угла
        x = pos[0] * self.cell_size + self.left
        y = pos[1] * self.cell_size + self.top
        return [x, y]
        

if True:
    pygame.init()
    pygame.display.set_caption("Kushats")
    size = width, height = 800, 800
    screen = pygame.display.set_mode(size)
    screen.blit(load_image('background.png'), (0, 0))
    board = Board(14, 14)
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYUP:  # стрелки
                if 1073741903 <= event.key <= 1073741906:
                    board.kush.change_dir(event.key - 1073741903)
                else:
                    print(event.key)
        clock.tick(120)
        screen.blit(load_image('background.png'), (0, 0))
        board.kush.change_coords()
        board.render(screen)
        pygame.display.flip()
    pygame.quit()