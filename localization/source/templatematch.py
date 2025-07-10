from array import array
from contextlib import nullcontext
from localization.source import AbstractStaticObstacleLocalizationSource
from matrix import Mat2
from matrix import Mat3
from matrix import Vec2
from resources.ImageG8_accel_c_build import ImageG8_accel_c
from units import convert
import ctypes
import math
import multiprocessing
import os
import os.path
import subprocess


class _Vec2iStruct(ctypes.Structure):
    _fields_ = [('x', ctypes.c_int), ('y', ctypes.c_int)]


class _Mat3Struct(ctypes.Structure):
    _fields_ = [('data', ctypes.c_double * 6)]


class _ImageG8Struct(ctypes.Structure):
    _fields_ = [('size', _Vec2iStruct), ('pData', ctypes.POINTER(ctypes.c_uint8))]


class ImageG8:
    GAUSSIAN_KERNELS = {}
    ACCEL_LIB = None
    ACCEL_LIB_FILENAME = 'encinal-2025-data/ImageG8-accel.so'
    #ACCEL_LIB_BUILD_ARGS = ('gcc', '-shared', '-O0', '-ggdb')
    ACCEL_LIB_BUILD_ARGS = ('gcc', '-shared', '-O3')

    def __init__(self, width, height, data=None):
        self.size = Vec2(width, height)
        self._data = array('B', data or [0] * width * height)
        self._pins = []

    def _test_accelerator(filename, should_build):
        lib = ctypes.CDLL(filename)
        try:
            lib.getSourceHash
        except AttributeError:
            should_build.value = 1
        else:
            lib.getSourceHash.restype = ctypes.c_uint64
            should_build.value = int(lib.getSourceHash() != hash(ImageG8_accel_c))

    @classmethod
    def load_accelerator(cls):
        try:
            build_lib = False
            if not os.path.isfile(cls.ACCEL_LIB_FILENAME):
                # Accelerator doesn't exist
                build_lib = True
            else:
                test_output = multiprocessing.Value(ctypes.c_int, lock=False)
                test_process = multiprocessing.Process(
                    target=cls._test_accelerator,
                    args=(cls.ACCEL_LIB_FILENAME, test_output)
                )
                test_process.start()
                test_process.join()
                build_lib = bool(test_output.value)

            if build_lib:
                src_fn = cls.ACCEL_LIB_FILENAME[:-2] + 'c'
                os.makedirs(os.path.dirname(src_fn), exist_ok=True)
                with open(src_fn, 'w') as f:
                    f.write(ImageG8_accel_c)
                subprocess.run([
                    *cls.ACCEL_LIB_BUILD_ARGS,
                    f'-DSOURCE_HASH={hash((ImageG8_accel_c, cls.ACCEL_LIB_BUILD_ARGS))}',
                    '-o', cls.ACCEL_LIB_FILENAME,
                    src_fn
                ], check=True)

            cls.ACCEL_LIB = ctypes.CDLL(cls.ACCEL_LIB_FILENAME)
            cls.ACCEL_LIB.templateMatch.restype = ctypes.c_char_p
            cls.ACCEL_LIB.templateMatch.argtypes = [
                _ImageG8Struct, # image
                _ImageG8Struct, # template
                ctypes.POINTER(_ImageG8Struct), # pMask
                _Vec2iStruct, # offset
                _ImageG8Struct, # out
                ctypes.c_int # threads
            ]
            cls.ACCEL_LIB.transform.restype = ctypes.c_char_p
            cls.ACCEL_LIB.transform.argtypes = [
                _ImageG8Struct, # image
                _Mat3Struct, # invTfm
                _Vec2iStruct, # offset
                ctypes.c_uint8, # fill
                ctypes.c_int, # shouldInterpolate
                _ImageG8Struct, # result
                ctypes.c_int # threads
            ]
            cls.ACCEL_LIB.convolve.restype = ctypes.c_char_p
            cls.ACCEL_LIB.convolve.argtypes = [
                _ImageG8Struct, # image
                _ImageG8Struct, # kernel
                _ImageG8Struct, # result
                ctypes.c_int, # threads
            ]
        except Exception as e:
            raise RuntimeError('Failed to compile or load ImageG8 accelerator.') from e

    @property
    def _as_parameter_(self):
        return _ImageG8Struct(
            _Vec2iStruct(self.size.x, self.size.y),
            ctypes.pointer(ctypes.c_uint8.from_buffer(self._data))
        )

    def get_norm(self, x, y):
        x_norm = max(0, min(self.size.x - 1, x * (self.size.x - 1)))
        y_norm = max(0, min(self.size.y - 1, y * (self.size.y - 1)))
        x_frac = x_norm % 1
        x_comp = 1 - x_frac
        y_frac = y_norm % 1
        y_comp = 1 - y_frac
        x_high = min(self.size.x, int(math.floor(x_norm + 1)))
        x_low = int(x_norm)
        y_high = min(self.size.y, int(math.floor(y_norm + 1)))
        y_low = int(y_norm)
        p00 = self._data[self.size.x * y_low + x_low]
        p10 = self._data[self.size.x * y_low + x_high]
        p01 = self._data[self.size.x * y_high + x_low]
        p11 = self._data[self.size.x * y_high + x_high]
        return (
            p00 * x_comp * y_comp +
            p10 * x_frac * y_comp +
            p01 * x_comp * y_frac +
            p11 * x_frac * y_frac
        )

    def get_norm_nearest(self, x, y):
        return self._data[self.size.x * int(y * self.size.y) + int(x * self.size.x)]

    def _draw_chunk(self, kernel, userdata, result, start, end):
        for i in range(start, end):
            yf = i // self.size.x / self.size.y
            xf = (i % self.size.x) / self.size.x
            res = kernel(xf, yf, userdata) if userdata else kernel(xf, yf)
            result[i - start] = int(res)
        return result

    def draw(self, kernel, num_threads=1, process_pool=None, userdata=None):
        total_px = self.size.x * self.size.y
        if num_threads == 1:
            self._draw_chunk(kernel, userdata, self._data, 0, total_px)
        else:
            self._data = array('B')
            px_per_chunk = total_px // num_threads
            last_px_per_chunk = total_px - (num_threads - 1) * px_per_chunk
            def to_args(i):
                is_last_chunk = i == num_threads - 1
                num_px = last_px_per_chunk if is_last_chunk else px_per_chunk
                buf = array('B', [0] * num_px)
                start = px_per_chunk * i
                end = total_px if is_last_chunk else start + px_per_chunk
                return (self, kernel, userdata, buf, start, end)
            args = [to_args(i) for i in range(num_threads)]
            try:
                pool = process_pool or multiprocessing.Pool(num_threads)
                for chunk in pool.starmap(type(self)._draw_chunk, args):
                    self._data.extend(chunk)
            finally:
                if not process_pool:
                    pool.terminate()

    def _paste_chunk(self, location, image, result, start, end):
        for i in range(start, end):
            y = i // image.size.x
            x = i % image.size.x
            ay = y + location.y
            ax = x + location.x
            if ax >= 0 and ax < self.size.x and ay >= 0 and ay < self.size.y:
                result[i - start] = min(
                    255,
                    image._data[image.size.x * y + x] + self._data[self.size.x * ay + ax]
                )
        return result

    def paste(self, location, image, *, num_threads=1, process_pool=None):
        total_px = image.size.x * image.size.y
        if num_threads == 1:
            result = array('B', [0] * total_px)
            self._paste_chunk(location, image, result, 0, total_px)
        else:
            result = array('B')
            px_per_chunk = total_px // num_threads
            last_px_per_chunk = total_px - (num_threads - 1) * px_per_chunk
            def to_args(i):
                is_last_chunk = i == num_threads - 1
                num_px = last_px_per_chunk if is_last_chunk else px_per_chunk
                buf = array('B', [0] * num_px)
                start = px_per_chunk * i
                end = total_px if is_last_chunk else start + px_per_chunk
                return (self, location, image, buf, start, end)
            args = [to_args(i) for i in range(num_threads)]
            try:
                pool = process_pool or multiprocessing.Pool(num_threads)
                for chunk in pool.starmap(type(self)._paste_chunk, args):
                    result.extend(chunk)
            finally:
                if not process_pool:
                    pool.terminate()
        for row in range(image.size.y):
            s = self.size.x * (location.y + row) + location.x
            e = s + image.size.x
            self._data[s:e] = result[row * image.size.x:(row + 1) * image.size.x]

    def _template_match_chunk(self, template, mask, result, start, end):
        result_width = self.size.x - template.size.x
        result_height = self.size.y - template.size.y
        template_px = template.size.x * template.size.y
        err_scaling_fac = 1 / template_px / 2 / 255 / 255 * 2**32
        for i in range(start, end):
            ay = i // result_width
            ax = i % result_width
            err = 0
            for by in range(template.size.y):
                for bx in range(template.size.x):
                    a = self._data[self.size.x * (ay + by) + ax + bx]
                    b = template._data[template.size.x * by + bx]
                    mask_fac = mask._data[mask.size.x * by + bx] if mask else 255
                    err += abs(a - b) * mask_fac
            # Use ceil so 0 error always means exact match
            result[i - start] = math.ceil(err * err_scaling_fac)
        return result

    def _template_match_rescale(arg):
        x, l, r = arg
        return int((x - l) * r)

    def template_match(
            self,
            template,
            offset,
            *,
            num_threads=1,
            process_pool=None,
            mask=None,
            accelerate=True):
        result_width = self.size.x + template.size.x - offset.x
        result_height = self.size.y + template.size.y - offset.y
        result = ImageG8(result_width, result_height)
        if accelerate:
            if not self.ACCEL_LIB:
                type(self).load_accelerator()
            msg = self.ACCEL_LIB.templateMatch(
                self,
                template,
                mask and ctypes.pointer(mask._as_parameter_),
                _Vec2iStruct(offset.x, offset.y),
                result,
                num_threads
            )
            if msg:
                raise RuntimeError(
                    'Encountered error in accelerated template_match: ' + msg.decode('ascii')
                )
            return result
        total_px = result_width * result_height
        if num_threads == 1:
            intermediate = array('L', [0] * total_px)
            self._template_match_chunk(template, mask, intermediate, 0, total_px)
            l = min(intermediate)
            r = 255 / (max(intermediate) - l)
            result._data = array('B', [int((x - l) * r) for x in intermediate])
        else:
            intermediate = array('L')
            px_per_chunk = total_px // num_threads
            last_px_per_chunk = total_px - (num_threads - 1) * px_per_chunk
            def to_args(i):
                is_last_chunk = i == num_threads - 1
                num_px = last_px_per_chunk if is_last_chunk else px_per_chunk
                buf = array('L', [0] * num_px)
                start = px_per_chunk * i
                end = total_px if is_last_chunk else start + px_per_chunk
                return (self, template, mask, buf, start, end)
            args = [to_args(i) for i in range(num_threads)]
            try:
                pool = process_pool or multiprocessing.Pool(num_threads)
                chunks = pool.starmap(type(self)._template_match_chunk, args)
                l = min(pool.map(min, chunks))
                r = 255 / max(1, max(pool.map(max, chunks)) - l)
                def normalize(arg):
                    x, l, r = arg
                    return int((x - l) * r)
                result._data = array(
                    'B',
                    pool.imap(
                        type(self)._template_match_rescale,
                        ((x, l, r) for chunk in chunks for x in chunk),
                        chunksize=px_per_chunk
                    )
                )
            finally:
                if not process_pool:
                    pool.terminate()
        return result

    def _convolve_chunk(self, kernel, result, start, end):
        cxl = kernel.size.x // 2
        cyl = kernel.size.y // 2
        for i in range(start, end):
            ay = i // self.size.x
            ax = i % self.size.x
            v = 0
            for by in range(kernel.size.y):
                ayi = min(self.size.y - 1, max(0, ay - cyl + by))
                for bx in range(kernel.size.x):
                    axi = min(self.size.x - 1, max(0, ax - cxl + bx))
                    d = self._data[self.size.x * ayi + axi]
                    w = kernel._data[kernel.size.x * by + bx] / 128 - 1
                    v += d * w
            result[i - start] = int(max(0, min(255, v)))
        return result

    def convolve(self, kernel, *, num_threads=1, process_pool=None, accelerate=True):
        result = type(self)(self.size.x, self.size.y)
        result._pins = list(self._pins)
        total_px = self.size.x * self.size.y
        if accelerate:
            if not self.ACCEL_LIB:
                type(self).load_accelerator()
            msg = self.ACCEL_LIB.convolve(self, kernel, result, num_threads)
            if msg:
                raise RuntimeError(
                    'Encountered error in accelerated convolve: ' + msg.decode('ascii')
                )
            return result
        if num_threads == 1:
            self._convolve_chunk(kernel, result._data, 0, total_px)
        else:
            result._data = array('B')
            px_per_chunk = total_px // num_threads
            last_px_per_chunk = total_px - (num_threads - 1) * px_per_chunk
            def to_args(i):
                is_last_chunk = i == num_threads - 1
                num_px = last_px_per_chunk if is_last_chunk else px_per_chunk
                buf = array('B', [0] * num_px)
                start = px_per_chunk * i
                end = total_px if is_last_chunk else start + px_per_chunk
                return (self, kernel, buf, start, end)
            args = [to_args(i) for i in range(num_threads)]
            try:
                pool = process_pool or multiprocessing.Pool(num_threads)
                for chunk in process_pool.starmap(type(self)._convolve_chunk, args):
                    result._data.extend(chunk)
            finally:
                if not process_pool:
                    pool.terminate()
        return result

    def square_blur(self, size, *, num_threads=1, process_pool=None, accelerate=True):
        return self.convolve(
            type(self)(size, size, [int(128 / size**2 + 128)] * size**2),
            num_threads=num_threads,
            process_pool=process_pool,
            accelerate=accelerate
        )

    def gaussian_blur(
            self,
            size,
            *,
            num_threads=1,
            process_pool=None,
            cache_kernel=True,
            accelerate=True):
        if size in self.GAUSSIAN_KERNELS:
            kernel = self.GAUSSIAN_KERNELS[size]
        else:
            kernel = type(self)(size, size)
            kernel.draw(
                type(self)._gaussian_kernel_draw_kernel,
                num_threads=num_threads,
                userdata=(size, (size / 4) ** 2)
            )
            if cache_kernel:
                self.GAUSSIAN_KERNELS[size] = kernel
        return self.convolve(
            kernel,
            num_threads=num_threads,
            process_pool=process_pool,
            accelerate=accelerate,
        )

    def _gaussian_kernel_draw_kernel(x, y, userdata):
        size, s2 = userdata
        x = size * (x - 0.5)
        y = size * (y - 0.5)
        return 128 * (1 + math.exp(-(x*x + y*y) / (2 * s2)) / (2 * math.pi * s2))

    def add_pin(self, pos):
        self._pins.append(pos)
        return len(self._pins) - 1

    def get_pin(self, idx):
        return self._pins[idx]

    def rotate(
            self,
            angle,
            fill,
            *,
            anchor=Vec2.zero(),
            num_threads=1,
            process_pool=None,
            accelerate=True):
        tfm = (
            Mat3.from_transform(Mat2.from_angle(angle), anchor)
            * Mat3.from_transform(Mat2.identity(), -anchor)
        )
        return self._transform(
            tfm,
            fill,
            num_threads=num_threads,
            process_pool=process_pool,
            accelerate=accelerate
        )

    def scale(
            self,
            factor,
            *,
            interpolate=True,
            num_threads=1,
            process_pool=None,
            accelerate=True):
        tfm = Mat3.from_transform(Mat2.identity() * factor, Vec2.zero())
        return self._transform(
            tfm,
            0, # Won't be used anyway
            interpolate=interpolate,
            num_threads=num_threads,
            process_pool=process_pool,
            accelerate=accelerate
        )

    def translate(
            self,
            offset,
            fill,
            *,
            interpolate=True,
            num_threads=1,
            process_pool=None,
            accelerate=True):
        tfm = Mat3.from_transform(Mat2.identity(), offset)
        return self._transform(
            tfm,
            fill,
            fit_all=False,
            interpolate=interpolate,
            num_threads=num_threads,
            process_pool=process_pool,
            accelerate=accelerate
        )

    def _transform(
            self,
            tfm,
            fill,
            *,
            interpolate=True,
            fit_all=True,
            num_threads=1,
            process_pool=None,
            accelerate=True):
        corners = [
            tfm * (Vec2(x, y) * self.size)
            for x, y in [(0, 0), (1, 0), (0, 1), (1, 1)]
        ]
        xs = [corner.x for corner in corners]
        ys = [corner.y for corner in corners]
        offset = Vec2(min(xs), min(ys)) if fit_all else Vec2.zero()
        result_width = max(xs) - min(xs)
        result_height = max(ys) - min(ys)
        result = type(self)(int(result_width), int(result_height))
        result._pins = [tfm * pin - offset for pin in self._pins]
        if accelerate:
            if not self.ACCEL_LIB:
                type(self).load_accelerator()
            msg = self.ACCEL_LIB.transform(
                self,
                _Mat3Struct((ctypes.c_double * 6)(*tfm.inv()._mat[:6])),
                _Vec2iStruct(int(offset.x), int(offset.y)),
                fill,
                int(interpolate),
                result,
                num_threads
            )
            if msg:
                raise RuntimeError(
                    'Encountered error in accelerated template_match. ' + msg.decode('ascii')
                )
            return result
        offset_norm = Vec2(offset.x / result_width, offset.y / result_height)
        result.draw(
            type(self)._draw_transformed_kernel,
            userdata=(
                self,
                tfm.inv(),
                offset_norm,
                result.size,
                fill,
                interpolate
            ),
            num_threads=num_threads,
            process_pool=process_pool
        )
        return result

    def _draw_transformed_kernel(x, y, userdata):
        self, tfm, offset_norm, result_size, fill, interpolate = userdata
        pos = tfm * ((Vec2(x, y) + offset_norm) * result_size)
        rx = pos.x
        ry = pos.y
        if rx < 0 or rx >= self.size.x or ry < 0 or ry >= self.size.y:
            return fill
        get_func = self.get_norm if interpolate else self.get_norm_nearest
        return get_func(rx / self.size.x, ry / self.size.y)

    def border(self, width_norm, color, num_threads=1, process_pool=None):
        result = type(self)(self.size.x, self.size.y)
        result._pins = list(self._pins)
        result.draw(
            type(self)._draw_border_kernel,
            userdata=(0.5 - width_norm, color, self),
            num_threads=num_threads,
            process_pool=process_pool
        )
        return result

    def _draw_border_kernel(x, y, userdata):
        min_c_dist_norm, color, img = userdata
        is_border = int(max(abs(0.5 - y), abs(0.5 - x)) > min_c_dist_norm)
        return is_border * color + (1 - is_border) * img.get_norm(x, y)


class TemplateMatchingLocalizationSource(AbstractStaticObstacleLocalizationSource):
    DETECTION_LIFETIME = 1
    PX_PER_M = 100
    FIELD_OUTLINE_RADIUS_PX = 6
    FIELD_BORDER_PX = 6
    MAX_DETECTION_DIST_M = 0.3
    DETECTION_RADIUS_PX = 2
    FIELD_DRAW_THREADS = 16
    DETECTION_DRAW_THREADS = 16
    TEMPLATE_MATCH_THREADS = 1
    ROTATION_VARIANTS = 16

    def __init__(self, field, field_img=None, detection_img=None):
        super().__init__(self.DETECTION_LIFETIME)
        self._size_m = field.get_size()
        border_rr = Vec2(self.FIELD_BORDER_PX, self.FIELD_BORDER_PX)
        self._size_px = math.floor(self._size_m * self.PX_PER_M) + border_rr * 2
        self._field_border_norm = (
            border_rr / self._size_px
        )
        if (field_img
                and field_img[0] == self.PX_PER_M
                and field_img[1] == self.FIELD_OUTLINE_RADIUS_PX
                and field_img[2] == self.FIELD_BORDER_PX):
            self._field_img = field_img[3]
        else:
            self._field_img = ImageG8(self._size_px.x, self._size_px.y)
            obstacles = field.get_pathfinding_obstacles()
            discard_border_fac = 1 / (1 - self._field_border_norm * 2)
            self._field_img.draw(
                type(self)._draw_field_kernel,
                num_threads=self.FIELD_DRAW_THREADS,
                userdata=(
                    self,
                    obstacles,
                    self.FIELD_OUTLINE_RADIUS_PX / self.PX_PER_M,
                    len(obstacles) - 1,
                    discard_border_fac
                )
            )
        if detection_img and detection_img[0] == self.DETECTION_RADIUS_PX:
            self._detection_img = detection_img[1]
        else:
            detection_diameter = self.DETECTION_RADIUS_PX * 2
            self._detection_img = ImageG8(detection_diameter, detection_diameter)
            self._detection_img.draw(
                type(self)._draw_detection_kernel,
                num_threads=self.DETECTION_DRAW_THREADS
            )

    def get_field_image(self):
        return (self.PX_PER_M, self.FIELD_OUTLINE_RADIUS_PX, self.FIELD_BORDER_PX, self._field_img)

    def get_detection_image(self):
        return (self.DETECTION_RADIUS_PX, self._detection_img)

    def _localize_from_detections(self, dets):
        detection_dist_px = int(self.MAX_DETECTION_DIST_M * self.PX_PER_M)
        template = ImageG8(2 * detection_dist_px, detection_dist_px)
        points = [
            Vec2(
                det.get_distance() * math.cos(det.get_angle()) + self.MAX_DETECTION_DIST_M,
                self.MAX_DETECTION_DIST_M - det.get_distance() * math.sin(det.get_angle())
            )
            for det in dets if det.get_distance() < self.MAX_DETECTION_DIST_M
        ]
        detection_rr = Vec2(self.DETECTION_RADIUS_PX, self.DETECTION_RADIUS_PX)
        match_results = []
        with (multiprocessing.Pool(self.TEMPLATE_MATCH_THREADS)
                if self.TEMPLATE_MATCH_THREADS != 1
                else nullcontext()) as pool:
            for point in points:
                template.paste(
                    math.floor(point * self.PX_PER_M) - detection_rr,
                    self._detection_img,
                    num_threads=self.TEMPLATE_MATCH_THREADS,
                    process_pool=pool
                )
            bordered = template.border(0.05, 255, num_threads=16)
            anchor = Vec2(detection_dist_px, detection_dist_px)
            pin = template.add_pin(anchor)
            for i in range(self.ROTATION_VARIANTS):
                angle = 2 * math.pi * i / self.ROTATION_VARIANTS
                print(i)
                rotated = template.rotate(
                    angle,
                    0,
                    anchor=anchor,
                    num_threads=1,
                    process_pool=pool
                )
                match_results.append(bordered.rotate(
                    angle,
                    0,
                    anchor=anchor
                ).scale(
                    16,
                    interpolate=False
                ))
                pin_pos = math.floor(rotated.get_pin(pin))
                match = self._field_img.template_match(
                    rotated,
                    pin_pos,
                    mask=rotated,
                    num_threads=self.TEMPLATE_MATCH_THREADS,
                    process_pool=pool
                )
                match_results.append(match)
                match_results.append(match.translate(
                    pin_pos,
                    255,
                    num_threads=self.TEMPLATE_MATCH_THREADS,
                    process_pool=pool
                ))
        # get localization data from match_results
        return match_results

    def _draw_field_kernel(x, y, userdata):
        self, obstacles, radius_m, obstacles_len_minus_one, discard_border_fac = userdata
        point = (Vec2(x, y) - self._field_border_norm) * discard_border_fac * self._size_m
        #point = Vec2(x, y) * self._size_m
        sum_abs_dist = sum([
            min(radius_m, abs(o.get_distance_to(point)))
            for o in obstacles
        ])
        norm_dist = max(0, min(1, sum_abs_dist / radius_m - obstacles_len_minus_one))
        return (1 - norm_dist) * 255

    def _draw_detection_kernel(x, y):
        dist = math.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2)
        norm = min(0.5, dist) / 0.5
        return (1 - norm) * 255
