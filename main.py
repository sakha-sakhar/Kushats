import pygame
from math import ceil, floor


class Entity:  # сущность - думаю, можно или объединить в этом классе игрока и призраков, либо какие-то из них унаследовать от этого класса.
    def __init__(self, pos, board):
        self.board = board
        self.pos = pos
        self.speed = 0.5  # от 0.1 до 1
        self.dir1 = (1, 0)   # освновное направление
        self.dir2 = (1, 0)  # если игрок изменил направление тогда, когда в том направлении была стена, записывается сюда
        self.directions = {0: (1, 0),   # вправо
                           1: (-1, 0),  # влево
                           2: (0, 1),   # вниз
                           3: (0, -1),  # вверх
                           4: (0, 0)}   # стоп

    def change_dir(self, dr):
        self.dir2 = self.directions[dr]

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


class Ghost:
    def __init__(self, pos, board, trajectory, color):
        self.color = color
        self.trajectory = trajectory
        self.board = board
        self.pos = pos
        self.point = 0  # к которой точке траектории направляется
        self.speed = 0.1

    def move(self):
        if self.trajectory[self.point] == self.pos:
            self.point = (self.point + 1) % len(self.trajectory)
        x = self.trajectory[self.point][0] - self.pos[0]
        y = self.trajectory[self.point][1] - self.pos[1]
        if x != 0:
            x = abs(x) / x
        if y != 0:
            y = abs(y) / y
        x1 = round(self.pos[0] + x * self.speed, 1)
        y1 = round(self.pos[1] + y * self.speed, 1)
        self.pos = x1, y1


class Chaser(Entity, Ghost):
    def __init__(self, board, pos):
        super().__init__(board, pos)
        self.color = (225, 0, 255)
        self.speed = 0.1

    def change_dir(self, dir_x, dir_y):
        if self.can_move(dir_x) and dir_x != (0, 0):
            self.dir2 = dir_x
        elif self.can_move(dir_y) and dir_y != (0, 0):
            self.dir2 = dir_y
        else:
            self.dir2 = (0, 0)

    def change_coords(self):
        deltax = self.board.kush.pos[0] - self.pos[0]
        deltay = self.board.kush.pos[1] - self.pos[1]
        dir_x = (abs(deltax) / deltax if deltax != 0 else 0, 0)
        dir_y = (0, abs(deltay) / deltay if deltay != 0 else 0)
        self.change_dir(dir_x, dir_y)
        super().change_coords()


class Board:
    # поле
    def __init__(self, width, height):
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
        self.kush = Entity([1, 12], self)  # игрок
        self.angriest_ghost = Chaser([12, 3], self)  # привидение которое движется к игроку
        self.ghost0 = Ghost((1, 0), self, [(3, 0), (3, 9), (4, 9), (4, 11),
                                           (5, 11), (5, 13), (3, 13), (3, 11),
                                           (6, 11), (6, 12), (7, 12), (7, 13),
                                           (9, 13), (9, 9), (13, 9),
                                           (13, 12), (12, 12), (12, 13), (10, 13),
                                           (10, 12), (9, 12), (9, 10), (6, 10),
                                           (6, 11), (4, 11), (4, 9), (3, 9),
                                           (3, 2), (1, 2), (1, 0)], (205, 92, 92))
        self.ghost1 = Ghost((10, 2), self, [(10, 0), (12, 0), (12, 1), (13, 1),
                                            (13, 3), (6, 3), (9, 3), (9, 0),
                                            (7, 0), (7, 1), (5, 1), (5, 2),
                                            (0, 2), (0, 1), (1, 1), (1, 0), (3, 0),
                                            (3, 3), (4, 3), (4, 2), (5, 2),
                                            (5, 0), (9, 0), (9, 2), (10, 2)], (255, 140, 0))

    def render(self, screen):
        x, y = self.kush.pos
        x = int(int(x) + (x - int(x)) // 0.5)
        y = int(int(y) + (y - int(y)) // 0.5)
        self.board[y][x] = 2
        for i in range(self.width):
            for j in range(self.height):
                cell = self.board[j][i]
                rct = (*self.get_coords([i, j]), self.cell_size, self.cell_size)
                pygame.draw.rect(screen, (255, 255, 255), rect=rct, width=1)
                if cell == 1:  # стены
                    screen.fill((255, 0, 0), rect=rct)
                elif cell == 0:  # точки
                    screen.fill((255, 255, 0), rect=(rct[0] + self.cell_size // 2 - 5,
                                                     rct[1] + self.cell_size // 2 - 5, 10, 10))
        screen.fill((255, 255, 0), rect=(*self.get_coords(self.kush.pos), self.cell_size, self.cell_size))
        for ghost in [self.ghost0, self.ghost1, self.angriest_ghost]:
            x, y = self.get_coords(ghost.pos)
            x += self.cell_size // 2
            y += self.cell_size // 2
            pygame.draw.circle(screen, ghost.color, (x, y), self.cell_size // 2)

    def get_coords(self, pos):
        # преобразует позицию клетки в кординаты её левого верхнего угла
        x = pos[0] * self.cell_size + self.left
        y = pos[1] * self.cell_size + self.top
        return [x, y]


if True:
    pygame.init()
    pygame.display.set_caption("Kushats")
    size = width, height = 800, 800
    screen = pygame.display.set_mode(size)
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
        clock.tick(50)
        screen.fill((0, 0, 0))
        board.kush.change_coords()
        board.angriest_ghost.change_coords()
        board.ghost0.move()
        board.ghost1.move()
        board.render(screen)
        pygame.display.flip()
    pygame.quit()