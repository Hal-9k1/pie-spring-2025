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
    root.bind('<Key>', lambda e: root.destroy())
    try:
        root.mainloop()
    except KeyboardInterrupt:
        _hold.discard(img)

def demo1():
    i = _ImageG8(400, 200)
    div = 0.1
    i.draw(lambda x, y: int((x // div + y // div) % 2 * 255))
    i = i.square_blur(10)
    show(i)

def demo2():
    src = TemplateMatchingLocalizationSource(field.spring_2025)
    show(src._field_img)

def demo3():
    src = TemplateMatchingLocalizationSource(field.spring_2025)
    show(src._field_img.rotate(pi / 4, Vec2(0, 0), 0, 8))

def demo4():
    src = TemplateMatchingLocalizationSource(field.spring_2025)
    fac = 0.1
    xoff = 0.7
    yoff = 0
    tpl = _ImageG8(int(src._field_img._width * fac), int(src._field_img._height * fac))
    show(src._field_img)
    tpl.draw(lambda x, y: src._field_img.get_interp(x * fac + xoff, y * fac + yoff))
    show(tpl)
    match = src._field_img.template_match(tpl, 8)
    show(match)

if __name__ == '__main__':
    demo4()
