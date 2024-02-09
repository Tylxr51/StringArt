import numpy as np
import random
import pyglet
from pyglet.window import Window
from pyglet import app
from pyglet import clock
from pyglet import shapes
from pyglet import image
from pyglet.graphics import Batch
from datetime import datetime
from PIL import Image


##  key of useful variable names:
####    w = window width
####    h = window height
####    r = circle radius
####    circle1 and circle2 create the hollow circle
####    bg = background
####    cx = x coord for centre of window
####    cy = y coord for centre of window
####    p1 = peg the line is coming from
####    p2 = peg the line is going to
    

t = 0
w = 900
h = 900
r = w/3
pegcount = 720
window = Window(w, h, 'String art')
circle1 = shapes.Circle(w/2, h/2, r, color = (0,0,0))
circle2 = shapes.Circle(w/2, h/2, r-1, color = (255, 255, 255))
bg = image.create(w, h, image.SolidColorImagePattern((255,255,255,255)))
pixel_array = np.array(Image.open("lecture.jpg").convert('L'), dtype = 'i')
#pixel_array_2 = np.array(Image.open("red_woman_lips.jpg").convert('L'), dtype = 'i')
batch = Batch()
lines = []
calculated_lines = {}



#### Set peg coords
cx = w/2
cy = h/2
pegxs = [cx+r*np.cos(2*np.pi*(i)/pegcount) for i in range(pegcount)]
pegys = [cx+r*np.sin(2*np.pi*(i)/pegcount) for i in range(pegcount)]




@window.event
def on_draw():
    window.clear()
    #bg.blit(0,0)
    #circle1.draw()
    circle2.draw()
    #draw_pegs()
    batch.draw()
    


def draw_pegs():
    for i in range(pegcount):
        shapes.Circle(pegxs[i], pegys[i], 1.3, color = (255, 0, 0)).draw()

def draw_line(p1, p2, color):
    p1 = p1%pegcount
    p2 = p2%pegcount
    lines.append(shapes.Line(pegxs[p1], pegys[p1], pegxs[p2], pegys[p2], 1, color = color, batch=batch))
    lines[-1].opacity = 15


def alter_image(line):
    coord1, coord2 = (line[0], line[1])
    if line[0] > line[1]: coord1, coord2 = (line[1], line[0])
    for coords in calculated_lines[str(str(coord1)+'-'+str(coord2))]:
        pixel_array[coords[0], coords[1]] += 10
        if pegxs[coord2] - pegxs[coord1] == 0:
            pixel_array[coords[0], coords[1]+1] += 4
            pixel_array[coords[0], coords[1]+1] += 4
        elif abs((pegys[coord2]-pegys[coord1]) / (pegxs[coord2] - pegxs[coord1])) > 1:
            pixel_array[coords[0]+1, coords[1]] += 4
            pixel_array[coords[0]-1, coords[1]] += 4
        else:
            pixel_array[coords[0], coords[1]+1] += 4
            pixel_array[coords[0], coords[1]+1] += 4

def calculate_line_total(lineID):
    total = 0
    for coords in calculated_lines[str(lineID)]:
        total += 255 - pixel_array[coords[0], coords[1]]
    return total

def calculate_pixels(p1, p2):
    pixels_hit = []
    x1 = int(pegxs[p1%pegcount])
    x2 = int(pegxs[p2%pegcount])
    y1 = int(pegys[p1%pegcount])
    y2 = int(pegys[p2%pegcount])
    if x1-x2 == 0: grad = 999999999
    elif y1-y2 == 0: grad = 0
    else: grad = (y2-y1)/(x2-x1)
    adjust = 1 if grad >= 0 else -1
    offset = 0
    threshold = 0.5
    if abs(grad) <= 1:
        y = y1
        if x2 < x1:
            x1, x2 = (x2, x1)
            y = y2
        for x in range(x1, x2+1):
            pixels_hit.append([-1-y, x])
            offset += abs(grad)
            if offset >= threshold:
                y += adjust
                threshold += 1

    else:
        x =  x1
        if y2 < y1:
            y1, y2 = (y2, y1)
            x = x2
        for y in range(y1, y2+1):
            pixels_hit.append([-1-y, x])
            offset += abs(1/grad)
            if offset >= threshold:
                x += adjust
                threshold += 1

    return pixels_hit

def screenshot():
    pyglet.image.get_buffer_manager().get_color_buffer().save('Screenshots/output'+datetime.now().strftime("%H:%M:%S")+'.png')

def dict_check(peg1, peg2):
    if str(peg1)+'-'+str(peg2) not in calculated_lines:
            pixels_hit = calculate_pixels(peg1, peg2)
            calculated_lines.update({str(peg1)+'-'+str(peg2):pixels_hit})
    line_total = calculate_line_total(str(peg1)+'-'+str(peg2))



def gold_func(peg1, peg2):
    peg2 = (peg2 + peg1) % pegcount
    if peg2 < peg1: peg1, peg2 = (peg2, peg1)
    dict_check(peg1, peg2)
    line_total = calculate_line_total(str(peg1)+'-'+str(peg2))
    return line_total

def golden_search(peg1):
    tol, maxiter = 0.8, 100
    golden = (1 + np.sqrt(5)) / 2
    func = gold_func
    chunks = 3

    nodes = np.linspace(0, pegcount - 1, chunks+1)
    boundaries = [[np.ceil(nodes[n]), np.floor(nodes[n+1])] for n in range(chunks)]
    boundaries = [[nodes[0], np.floor(nodes[1])], 
                  [np.ceil(nodes[1]), np.floor(nodes[2])], 
                  [np.ceil(nodes[2]), nodes[3]]]
    
    x_max = []
    f_max = []

    for j, k in enumerate(boundaries):

        a = k[0]
        b = k[1]

        c = int(round(b - (b - a) / golden,0))
        d = int(round(a + (b - a) / golden,0))
        fc, fd = func(peg1, c), func(peg1, d)

        for i in range(maxiter):
            if fc < fd:
                a, c, fc = c, d, fd
                d = int(round(a + (b - a) / golden,0))
                fd = func(peg1, d)

                if abs(c - d) < tol:
                    f_max.append(fd)
                    x_max.append((d + peg1) % pegcount)
                    break

            else:
                b, d, fd = d, c, fc
                c = int(round(b - (b - a) / golden,0))
                fc = func(peg1, c)

                if abs(c - d) < tol:
                    f_max.append(fc)
                    x_max.append((c + peg1) % pegcount)
                    break

        if len(f_max) <= j:
            f_max.append(func(peg1, c))
            x_max.append((c + peg1) % pegcount)
    
    x = x_max[np.argmax(f_max)]

    return (peg1, x)


def greedy(peg1):
    for i in range(pegcount):
        peg2 = (peg1 + i) % pegcount
        if peg2 < peg1: peg1temp, peg2temp = (peg2, peg1)
        else: peg1temp, peg2temp = (peg1, peg2)
        dict_check(peg1temp, peg2temp)
    
    best_total = 0
    best_line = (0,0)
    for i in range(pegcount):
        peg2 = (peg1 + i) % pegcount
        if peg2 < peg1: peg1temp, peg2temp = (peg2, peg1)
        else: peg1temp, peg2temp = (peg1, peg2)
        line_total = calculate_line_total(str(peg1temp)+'-'+str(peg2temp))
        if line_total >= best_total: 
            best_total = line_total
            best_line = (peg1, peg2)
    return best_line



def update(dt):
    global best_line
    global t

    for _ in range(10):
        try: peg1 = best_line[1]
        except: peg1 = 0
    
        best_line = golden_search(peg1)
        #best_line = greedy(peg1)
        
        draw_line(best_line[0], best_line[1], (0,0,0))
        alter_image(best_line)
        t += 1

    print(t)

clock.schedule_interval(update, 0.01)

app.run()
