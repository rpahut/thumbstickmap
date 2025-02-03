# Скрипт отслеживает движение аналогового стика и прочерчивает карту движения. Карта при завершении приложения записывается в файл.
# Цветом обозначается скорость перемещения между соседними положениями стика, что позволяет визуализировать равномерность рабочего диапазона.

import math
import pygame

which_gamepad = 0
which_axis_x = 2
which_axis_y = 3
smoothness_range = 20.0

color_blank = (255, 255, 255)
color_smooth = (0, 127, 0)
color_abrupt = (255, 127, 127)
map_resolution = 256

pygame.init()
screen = pygame.display.set_mode((512, 512))
screen.fill(color_blank)

map_img = pygame.Surface((map_resolution, map_resolution))
map_img.fill(color_blank)

pygame.joystick.init()
gamepads = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

gamepad = gamepads[which_gamepad]
gamepad.init()
gamepad_name = gamepad.get_name()

map_sprite = pygame.sprite.Sprite()
map_sprite.image = map_img

pointer_img = pygame.image.load('pointer.png')
pointer_sprite = pygame.sprite.Sprite()
pointer_sprite.image = pointer_img

def _get_line_points(x1, y1, x2, y2):
    points = []
    issteep = abs(y2-y1) > abs(x2-x1)
    if issteep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    rev = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        rev = True
    deltax = x2 - x1
    deltay = abs(y2-y1)
    error = int(deltax / 2)
    y = y1
    ystep = None
    if y1 < y2:
        ystep = 1
    else:
        ystep = -1
    for x in range(x1, x2 + 1):
        if issteep:
            points.append((y, x))
        else:
            points.append((x, y))
        error -= deltay
        if error < 0:
            y += ystep
            error += deltax
    # Reverse the list if the coordinates were reversed
    if rev:
        points.reverse()
    return points

def _mix_colors(color1, color2, ratio):
    return tuple(int(a * ratio + b * (1 - ratio)) for a, b in zip(color1, color2))

def _pick_closest_of_colors(ref_color, color1, color2):
    vec1 = tuple(a - b for a, b in zip(color1, ref_color))
    vec2 = tuple(a - b for a, b in zip(color2, ref_color))
    dist1 = math.hypot(*vec1)
    dist2 = math.hypot(*vec2)
    if dist1 < dist2:
        return color1
    return color2

def _draw_line_special(x1, y1, x2, y2, smoothness):
    '''
    Нарисовать в карту отрезок прямой между указанными точками, цветом, соответствующим заданной "плавности".
    При этом сохраняются пиксели с бОльшей плавностью уже помещённые на карту.
    '''
    color = _mix_colors(color_smooth, color_abrupt, smoothness)
    pp = _get_line_points(x1, y1, x2, y2)
    for p in pp:
        xy = (int(p[0]), int(p[1]))
        pix = map_img.get_at(xy)
        map_img.get_at(xy)
        if pix == color_blank or _pick_closest_of_colors(pix, color_smooth, color_abrupt) == color_abrupt:
            map_img.set_at(xy, color)

lastX = None
lastY = None
def _visualize_step_to(x: int, y: int):
    global lastX, lastY
    if lastX and lastY:
        if x == lastX and y == lastY:
            return
        distX = x - lastX
        distY = y - lastY
        distMax = max(abs(distX), abs(distY))
        smoothness = 1 - min(1, distMax / smoothness_range)
        _draw_line_special(lastX, lastY, x, y, smoothness)
    lastX = x
    lastY = y

def _remap_to_map_range(stick_x: float, stick_y: float):
    map_x = (stick_x + 1.0) / 2 * map_resolution
    map_y = (stick_y + 1.0) / 2 * map_resolution
    map_x = max(min(map_x, map_resolution - 1), 0)
    map_y = max(min(map_y, map_resolution - 1), 0)
    return map_x, map_y

def _process_stick():
    jx = gamepad.get_axis(which_axis_x)
    jy = gamepad.get_axis(which_axis_y)
    #print(f"{a},{b}")
    px, py = _remap_to_map_range(jx, jy)
    print(f"{px},{py}")
    _visualize_step_to(int(px), int(py))

def on_draw():
    map_sprite.update()
    screen.blit(map_sprite.image, (127, 127))
    if lastX and lastY:
        screen.blit(pointer_sprite.image, (lastX + 127, lastY + 127))

clock = pygame.time.Clock()
running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.JOYAXISMOTION:
            _process_stick()
        if ev.type == pygame.QUIT:
            running = False
            break
    on_draw()

    pygame.display.flip()
    clock.tick(60)

pygame.image.save(map_img, f'{gamepad_name}-{which_axis_x}-{which_axis_y}.png')
pygame.quit()