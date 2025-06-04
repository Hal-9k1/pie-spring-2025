import tkinter as tk
from localization.source import _ImageG8
import field
from localization.source import TemplateMatchingLocalizationSource
from math import pi
from matrix import Vec2


_hold = set()

def show(img: _ImageG8):
    root = tk.Tk()
    data = f'P5\n{img._width}\n{img._height}\n255\n'.encode('ascii') + img._data.tobytes()
    #with open('out.pgm', 'w') as f:
    #    f.write(data)
    img = tk.PhotoImage(data=data)
    _hold.add(img)
    tk.Label(root, image=img).pack(side='bottom', fill='both', expand='yes')
    try:
        root.mainloop()
        pass
    except KeyboardInterrupt:
        _hold.discard(img)

def demo1():
    i = _ImageG8(400, 200)
    div = 0.1
    i.draw(lambda x, y: int((x // div + y // div) % 2 * 255))
    i = i.convolve(_ImageG8(10, 10, [int(128 / 100 + 128)] * 100))
    show(i)

def demo2():
    src = TemplateMatchingLocalizationSource(field.spring_2025)
    show(src._field_img)

def demo3():
    src = TemplateMatchingLocalizationSource(field.spring_2025)
    show(src._field_img.rotate(pi / 4, Vec2(0, 0), 0))

if __name__ == '__main__':
    demo3()
