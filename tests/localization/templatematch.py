from localization.source.templatematch import ImageG8
from localization.source.templatematch import TemplateMatchingLocalizationSource
from math import pi
from matrix import Vec2
from multiprocessing import Pool
from task.sensory import SensorTurretTask
import field
import os
import os.path
import pickle
import tkinter as tk
import math
import cProfile as profile


_hold = set()

def show(img: ImageG8):
    root = tk.Tk()
    data = f'P5\n{img.size.x}\n{img.size.y}\n255\n'.encode('ascii') + img._data.tobytes()
    #with open('out.pgm', 'w') as f:
    #    f.write(data)
    img = tk.PhotoImage(data=data)
    _hold.add(img)
    tk.Label(root, image=img).pack(side='bottom', fill='both', expand='yes')
    root.bind('<Key>', lambda e: root.destroy())
    try:
        root.mainloop()
    except KeyboardInterrupt:
        _hold.discard(img)

def to_conf_path(name):
    return f'encinal-2025-data/{name}.pickle'

def loadconf(name):
    try:
        with open(to_conf_path(name), 'rb') as f:
            return pickle.load(f)
    except (OSError, pickle.PickleError):
        return None

def saveconf(name, obj):
    path = to_conf_path(name)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(obj, f, protocol=-1)
    except (OSError, pickle.PickleError):
        pass

def saveconfs():
    src = TemplateMatchingLocalizationSource(field.spring_2025)
    with Pool(16) as pool:
        for i in range(4, 16):
            ImageG8(1, 1).gaussian_blur(i, num_threads=16, process_pool=pool)
    saveconf('field_img', src.get_field_image())
    saveconf('detection_img', src.get_detection_image())
    saveconf('gaussian_kernels', ImageG8.GAUSSIAN_KERNELS)

def checker_shader(x, y, div):
    return int((x // div + y // div) % 2 * 255)

def checker():
    i = ImageG8(80, 40)
    div = 0.1
    i.draw(
        checker_shader,
        userdata=div,
        num_threads=16
    )
    return i

def circle_shader(x, y):
    return 255 * (math.sqrt((x - 0.5)**2 + (y - 0.5)**2) < 0.5)

def circle(r):
    i = ImageG8(r * 2, r * 2)
    i.draw(circle_shader, num_threads=16)
    return i

def rect(x, y):
    return ImageG8(x, y, [255] * x * y)

def clip_shader(x, y, userdata):
    img, x0, y0, x1, y1 = userdata
    return img.get_norm(
        (x0 + x * (x1 - x0)) / img.size.x,
        (y0 + y * (y1 - y0)) / img.size.y
    )

def clip(img, x0, y0, x1, y1):
    i = ImageG8(x1 - x0, y1 - y0)
    i.draw(
        clip_shader,
        userdata=(img, x0, y0, x1, y1),
        num_threads=16
    )
    return i


def demo1():
    i = ImageG8(400, 200)
    div = 0.1
    i.draw(lambda x, y: int((x // div + y // div) % 2 * 255))
    i = i.square_blur(10)
    show(i)

def demo2():
    src = TemplateMatchingLocalizationSource(
        field.spring_2025,
        field_img=loadconf('field_img'),
        detection_img=loadconf('detection_img')
    )
    show(src._field_img)

def demo3():
    src = TemplateMatchingLocalizationSource(field.spring_2025)
    show(src._field_img.rotate(3 * pi / 4, 0, 8))

def demo4():
    src = TemplateMatchingLocalizationSource(field.spring_2025)
    fac = 0.1
    xoff = 0.7
    yoff = 0
    size = math.floor(src._field_img._size * fac)
    tpl = ImageG8(size.x, size.y)
    show(src._field_img)
    tpl.draw(lambda x, y: src._field_img.get_interp(x * fac + xoff, y * fac + yoff))
    show(tpl)
    match = src._field_img.template_match(tpl, 8)
    show(match)
    match_blur = match.gaussian_blur(10, 8)
    show(match_blur)

def template_match():
    src = TemplateMatchingLocalizationSource(
        field.spring_2025,
        field_img=loadconf('field_img'),
        detection_img=loadconf('detection_img')
    )
    ImageG8.GAUSSIAN_KERNELS = loadconf('gaussian_kernels')
    return src._localize_from_detections([
        SensorTurretTask(i * pi / 16, dist / 100)
        for i, dist in zip(range(13), [
            16,
            11.67,
            9.47,
            8.23,
            7.54,
            7.21,
            7.17,
            7.41,
            8,
            9.06,
            10.92,
        ])
    ])

def demo5():
    for match in template_match():
        show(match)

def demo6():
    profile.run('template_match()', sort='cumulative')

def demo7():
    template_match()

def demo8(accelerate=True, show_accel=False, i=None):
    if not i:
        i = checker()
    if not accelerate:
        breakpoint()
    r = i.rotate(math.pi / 4, 0, accelerate=accelerate)
    if show_accel or not accelerate:
        show(r.scale(12, interpolate=False))

def demo9():
    i = checker()
    r1 = i.rotate(math.pi / 4, 0, accelerate=False).scale(12, interpolate=False)
    r2 = i.rotate(math.pi / 4, 0, accelerate=True).scale(12, interpolate=False)
    show(r1)
    show(r2)

def demo10():
    scene = ImageG8(400, 400)
    scene.paste(Vec2(100, 100), rect(250, 100))
    r = 20
    scene.paste(Vec2(350 - r, 200 - r), circle(r))
    c = clip(scene, 300, 150, 400, 250)
    scene.paste(Vec2(-50, 150), c)
    match = scene.template_match(c, Vec2(-50, -50))
    while True:
        show(scene)
        show(c)
        show(match)

if __name__ == '__main__':
    #saveconfs()
    demo10()
