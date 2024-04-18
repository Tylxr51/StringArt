import numpy as np
import pyglet
import random
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
pixel_array = np.array(Image.open("tim.jpg").convert('L'), dtype = 'i')
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

def screenshot(t):
    pyglet.image.get_buffer_manager().get_color_buffer().save('Screenshots/output'+datetime.now().strftime("%H:%M:%S")+' t:'+str(t)+'.png')

def dict_check(peg1, peg2):
    if str(peg1)+'-'+str(peg2) not in calculated_lines:
            pixels_hit = calculate_pixels(peg1, peg2)
            calculated_lines.update({str(peg1)+'-'+str(peg2):pixels_hit})
    line_total = calculate_line_total(str(peg1)+'-'+str(peg2))



def algo_func(peg1, peg2):
    peg2 = (peg2 + peg1) % pegcount
    if peg2 < peg1: peg1, peg2 = (peg2, peg1)
    dict_check(peg1, peg2)
    line_total = calculate_line_total(str(peg1)+'-'+str(peg2))
    return line_total


def golden_search(peg1):
    tol, maxiter = 0.9, 20
    golden = (1 + np.sqrt(5)) / 2
    func = algo_func
    chunks = 3

    nodes = np.linspace(0, pegcount - 1, chunks+1)
    boundaries = [[np.ceil(nodes[n]), np.floor(nodes[n+1])] for n in range(chunks)]
    
    x_max = []
    f_max = []

    for j, k in enumerate(boundaries):

        a = k[0]
        b = k[1]

        c = int(round(b - (b - a) / golden,0))
        d = int(round(a + (b - a) / golden,0))
        fc, fd = func(peg1, c), func(peg1, d)

        for _ in range(maxiter):
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

def jarratt(peg1):
    tol, maxiter = 0.9, 20
    chunks = 3
    func = algo_func

    nodes = np.linspace(0, pegcount - 1, chunks+1)
    boundaries = [[np.ceil(nodes[n]), np.floor(nodes[n+1])] for n in range(chunks)]
    
    x_max = []
    f_max = []

    for j, k in enumerate(boundaries):

        optimal = [peg1, 0]

        x0 = int(k[0])
        x1 = int(k[1])
        x2 = int((x0+x1) / 2)

        y0 = func(peg1, x0)
        y1 = func(peg1, x1)
        y2 = func(peg1, x2)


        for _ in range(maxiter):
            if x0 == x1 or x0 == x2  or x1 == x2:
                optimal = [peg1,0]        # Divide by 0 error, skip this line to avoid error
                break
            
            try: x3 = int(x2 + 0.5 * ((((x1 - x2)**2 * (y2 - y0)) + ((x0 - x2)**2 * (y1 - y2))) / (((x1 - x2) * (y2 - y0)) + ((x0 - x2) * (y1 - y2)))))
            except: 
                optimal = [peg1, 0]
                break

            y3 = func(peg1, x3)

            if y3 >= optimal[1]:
                optimal = [x3, y3]

            if abs(x3 - x2) < tol:
                f_max.append(func(peg1, optimal[0]))
                x_max.append((optimal[0] + peg1) % pegcount)
                break

            if x3 < x2:
                x1, x2 = (x2, x3)
                y1, y2 = (y2, y3)

            else:
                x0, x2 = (x2, x3)  
                y0, y2 = (y2, y3)  


        if len(f_max) <= j:
            f_max.append(func(peg1, optimal[0]))
            x_max.append((optimal[0] + peg1) % pegcount)

    x = x_max[np.argmax(f_max)]

    return (peg1, x)

def brent(peg1):
    tol, maxiter = 0.9, 20
    chunks = 3
    func = algo_func

    nodes = np.linspace(0, pegcount - 1, chunks+1)
    boundaries = [[np.ceil(nodes[n]), np.floor(nodes[n+1])] for n in range(chunks)]
    
    x_max = []
    f_max = []

    for j, k in enumerate(boundaries):

        optimal = [peg1, 0]

        a = int(k[0])
        b = int(k[1])
        e = 0
        uprev = 0

        v = w = x = int(a + ((3 - np.sqrt(5)) / 2) * (b - a))
        fv = fw = fx = func(peg1, x)


        for _ in range(maxiter):

            m = (1/2) * (a + b)

            # Jarratt or Golden
            if not(v == w or v == x or w == x):
                r = (x - w) * (fx - fv)
                q = (x - v) * (fx - fw)
                p = (x - v) * q - (x - w) * r
                q = 2 * (q - r)
                if q > 0: p = -p
                else: q = -q

                inferr = False
                try: u = int(x + (p / q))
                except: inferr = True

                if u > int(k[1]) or u < int(k[0]) or inferr == True:
                    e = b - x if x < m else a - x
                    u = int(x + (((3 - np.sqrt(5)) / 2) * e))
                
                fu = func(peg1, u)

            else:
                e = b - x if x < m else a - x
                u = int(x + (((3 - np.sqrt(5)) / 2) * e))
                fu = func(peg1, u)
                

            if fx >= optimal[1]:
                optimal = [x, fx]


            # Update variables      
            if fu >= fx:
                if u < x: b = x
                else: a = x
                v, fv, w, fw, x, fx = w, fw, x, fx, u, fu
            else:
                if u < x: a = u
                else: b = u

                if fu >= fw or w == x:
                    v, fv, w, fw = w, fw, u, fu
                elif fu >= fv or v == x or v == w:
                    v, fv = u, fu


            if abs(u - uprev) < tol:
                f_max.append(func(peg1, optimal[0]))
                x_max.append((optimal[0] + peg1) % pegcount)
                break

            uprev = u


        if len(f_max) <= j:
            f_max.append(func(peg1, optimal[0]))
            x_max.append((optimal[0] + peg1) % pegcount)

    x_out = x_max[np.argmax(f_max)]

    return (peg1, x_out)

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
    
        #best_line =  brent(peg1)
        best_line = jarratt(peg1)
        #best_line = golden_search(peg1)
        #best_line = greedy(peg1)
        
        draw_line(best_line[0], best_line[1], (0,0,0))
        alter_image(best_line)
        t += 1

    print(t)

clock.schedule_interval(update, 0.01)

app.run()