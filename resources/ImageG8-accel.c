#include <math.h>
#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>

typedef struct
{
  int x;
  int y;
} Vec2i;

typedef struct
{
  double x;
  double y;
} Vec2d;

typedef struct
{
  Vec2i size;
  uint8_t *pData;
} ImageG8;

typedef struct
{
  double data[6];
} Mat3;

static Vec2d mulMat3Vec2d(Mat3 *pMat, Vec2d vec)
{
  Vec2d result = {
    pMat->data[0] * vec.x + pMat->data[1] * vec.y + pMat->data[2],
    pMat->data[3] * vec.x + pMat->data[4] * vec.y + pMat->data[5]
  };
  return result;
}

static double implicitRow[3] = { 0, 0, 1 };

static double rowColDot(
  Mat3 *pMatA,
  int row,
  Mat3 *pMatB,
  int col
) {
  int aStart = row * 3;
  return pMatA->data[aStart] * pMatB->data[col]
    + pMatA->data[aStart + 1] * pMatB->data[col + 3]
    + pMatA->data[aStart + 2] * implicitRow[col];
}

static void mulMat3Mat3(Mat3 *pMatA, Mat3 *pMatB, Mat3 *pResult)
{
  for (int i = 0; i < sizeof(pMatA->data) / sizeof(pMatA->data[0]); ++i)
  {
    div_t d = div(i, 3);
    pResult->data[i] = rowColDot(pMatA, d.quot, pMatB, d.rem);
  }
}

static double clampd(double value, double min, double max)
{
  double temp = value > max ? max : value;
  return temp < min ? min : temp;
}

static int clampi(int value, int min, int max)
{
  int temp = value > max ? max : value;
  return temp < min ? min : temp;
}

static uint8_t getImageG8(ImageG8 img, int x, int y)
{
  return img.pData[img.size.x * y + x];
}

static double getInterpolatedImageG8(ImageG8 img, double x, double y)
{
  double modfDummy;
  double xClamped = clampd(x, 0, 1) * (img.size.x - 1);
  double xFrac = modf(xClamped, &modfDummy);
  double xComp = 1 - xFrac;
  int xHighUnclamped = xClamped + 1;
  int xHigh = xHighUnclamped > img.size.x ? img.size.x : xHighUnclamped;
  int xLow = xClamped;

  double yClamped = clampd(y, 0, 1) * (img.size.y - 1);
  double yFrac = modf(yClamped, &modfDummy);
  double yComp = 1 - yFrac;
  int yHighUnclamped = yClamped + 1;
  int yHigh = yHighUnclamped > img.size.y ? img.size.y : yHighUnclamped;
  int yLow = yClamped;

  return (
    xComp * yComp * getImageG8(img, xLow, yLow) +
    xFrac * yComp * getImageG8(img, xHigh, yLow) +
    xComp * yFrac * getImageG8(img, xLow, yHigh) +
    xFrac * yFrac * getImageG8(img, xHigh, yHigh)
  );
}

typedef struct MultiprocessInvocation_t MultiprocessInvocation;

typedef void (*Multiprocessable)(MultiprocessInvocation *pInvoc);

struct MultiprocessInvocation_t
{
  Multiprocessable func;
  int start;
  int end;
  int id;
  void *pUserdata;
};

static void *multiprocessThread(void *pArg)
{
  MultiprocessInvocation *pInvoc = pArg;
  pInvoc->func(pInvoc);
  free(pInvoc);
  return NULL;
}

static int multiprocess(Multiprocessable func, int range, int threads, void *pArg)
{
  if (threads == 1)
  {
    MultiprocessInvocation invoc = { func, 0, range, 0, pArg };
    func(&invoc);
    return 0;
  }
  int itemsPerChunk = range / threads;
  int lastItemsPerChunk = range - (threads - 1) * itemsPerChunk;
  pthread_t *pThreads = malloc(threads * sizeof(pthread_t));
  pthread_attr_t attributes;
  if (!pThreads || pthread_attr_init(&attributes))
  {
    return 1;
  }
  for (int i = 0; i < threads; ++i)
  {
    MultiprocessInvocation *pInvoc = malloc(sizeof(MultiprocessInvocation));
    if (!pInvoc)
    {
      return 1;
    }
    pInvoc->func = func;
    pInvoc->start = itemsPerChunk * i;
    pInvoc->end = (i == threads - 1) ? range : pInvoc->start + itemsPerChunk;
    pInvoc->id = i;
    pInvoc->pUserdata = pArg;
    if (pthread_create(pThreads + i, &attributes, multiprocessThread, pInvoc))
    {
      return 2;
    }
  }
  pthread_attr_destroy(&attributes);
  for (int i = 0; i < threads; ++i)
  {
    if (pthread_join(pThreads[i], NULL))
    {
      return 3;
    }
  }
  free(pThreads);
  return 0;
}

typedef struct
{
  uint32_t *pResults;
  uint32_t *pData;
} NumberAggregateInfo;

static void minChunk(MultiprocessInvocation *pInvoc)
{
  NumberAggregateInfo *pInfo = pInvoc->pUserdata;
  uint32_t result = 0;
  for (int i = pInvoc->start; i < pInvoc->end; ++i)
  {
    result = result < pInfo->pData[i] ? result : pInfo->pData[i];
  }
  pInfo->pResults[pInvoc->id] = result;
}

static void maxChunk(MultiprocessInvocation *pInvoc)
{
  NumberAggregateInfo *pInfo = pInvoc->pUserdata;
  uint32_t result = 0;
  for (int i = pInvoc->start; i < pInvoc->end; ++i)
  {
    result = result > pInfo->pData[i] ? result : pInfo->pData[i];
  }
  pInfo->pResults[pInvoc->id] = result;
}

static int parallelAggregate(
  Multiprocessable func,
  int count,
  uint32_t *pData,
  uint32_t *pResult,
  int threads
) {
  uint32_t *pAggResults = malloc(threads * sizeof(uint32_t));
  if (!pAggResults)
  {
    return 1;
  }
  NumberAggregateInfo aggInfo = { pAggResults, pData };
  int err = multiprocess(func, count, threads, &aggInfo);
  if (err)
  {
    return err;
  }
  aggInfo.pResults = pResult;
  aggInfo.pData = pAggResults;
  MultiprocessInvocation invoc = { func, 0, threads, 0, &aggInfo };
  func(&invoc);
  free(pAggResults);
  return 0;
}

typedef struct
{
  uint8_t *pResults;
  uint32_t *pData;
  uint32_t low;
  double scale;
} NormalizeInfo;

static void normalizeErrorChunk(MultiprocessInvocation *pInvoc)
{
  NormalizeInfo *pInfo = pInvoc->pUserdata;
  for (int i = pInvoc->start; i < pInvoc->end; ++i)
  {
    pInfo->pResults[i] = (pInfo->pData[i] - pInfo->low) * pInfo->scale;
  }
}

typedef struct
{
  ImageG8 image;
  ImageG8 template;
  ImageG8 *pMask;
  Vec2i resultSize;
  double errScalingFac;
  uint32_t *pBuf;
} TemplateMatchInfo;

static void templateMatchChunk(MultiprocessInvocation *pInvoc)
{
  TemplateMatchInfo *pInfo = pInvoc->pUserdata;
  for (int i = pInvoc->start; i < pInvoc->end; ++i)
  {
    div_t imageCoords = div(i, pInfo->resultSize.x);
    int ay = imageCoords.quot;
    int ax = imageCoords.rem;
    long err = 0;
    for (int by = 0; by < pInfo->template.size.y; ++by)
    {
      for (int bx = 0; bx < pInfo->template.size.x; ++bx)
      {
        int a = getImageG8(pInfo->image, ax + bx, ay + by);
        int b = getImageG8(pInfo->template, bx, by);
        int maskFac = pInfo->pMask ? getImageG8(*pInfo->pMask, bx, by) : 255;
        err += abs(a - b) * maskFac;
      }
    }
    pInfo->pBuf[i] = ceil(err * pInfo->errScalingFac);
  }
}

static int templateMatchImpl(
  ImageG8 image,
  ImageG8 template,
  ImageG8 *pMask,
  ImageG8 out,
  int threads
) {
  int totalPx = out.size.x * out.size.y;
  uint32_t *pBuf = malloc(totalPx * sizeof(uint32_t));
  if (!pBuf)
  {
    return 1;
  }
  TemplateMatchInfo templateInfo = {
    image,
    template,
    pMask,
    out.size,
    // Divide by template area to get average error across template
    // Divide by 2 because difference could be from -255 to 255, brings range to 0-255
    // Divide by 255 from mask
    // Divide by 255 to scale 0-255 difference to 1
    // Multiply by 2**32 to bring range into uint32_t range
    1.0 / (template.size.x * template.size.y) / 2 / 255 / 255 * (1L << 32),
    pBuf
  };
  int err = multiprocess(templateMatchChunk, totalPx, threads, &templateInfo);
  if (err)
  {
    return err;
  }

  uint32_t low;
  err = parallelAggregate(minChunk, totalPx, pBuf, &low, threads);
  if (err)
  {
    return err;
  }
  uint32_t high;
  err = parallelAggregate(maxChunk, totalPx, pBuf, &high, threads);
  if (err)
  {
    return err;
  }
  double scale = high != low ? 255.0 / (high - low) : 1;
  NormalizeInfo normInfo = {
    out.pData,
    pBuf,
    low,
    scale
  };
  err = multiprocess(normalizeErrorChunk, totalPx, threads, &normInfo);
  if (err)
  {
    return err;
  }
  free(pBuf);
  return 0;
}

const char *errCodeToCStr(int code)
{
  switch (code)
  {
    case 0:
      return NULL;
    case 1:
      return "Out of memory";
    case 2:
      return "pthread_create failed";
    case 3:
      return "pthread_join deadlock detected";
    default:
      return "Unknown error";
  }

}

const char *templateMatch(
  ImageG8 image,
  ImageG8 template,
  ImageG8 *pMask,
  ImageG8 out,
  int threads
) {
  return errCodeToCStr(templateMatchImpl(image, template, pMask, out, threads));
}

typedef struct
{
  int x;
  int y;
  Vec2i imgSize;
  void *pUniforms;
  uint8_t *pOut;
} ShaderInvocation;

typedef void (*Shader)(ShaderInvocation *pInvoc);

typedef struct
{
  ImageG8 img;
  Shader shader;
  void *pUniforms;
} ShadeInfo;

static void shadeImageChunk(MultiprocessInvocation *pInvoc)
{
  ShadeInfo *pInfo = pInvoc->pUserdata;
  Vec2i size = pInfo->img.size;
  ShaderInvocation shaderInvoc = {0, 0, size, pInfo->pUniforms, pInfo->img.pData};
  for (int i = pInvoc->start; i < pInvoc->end; ++i)
  {
    div_t d = div(i, size.x);
    shaderInvoc.y = d.quot;
    shaderInvoc.x = d.rem;
    ++shaderInvoc.pOut;
    pInfo->shader(&shaderInvoc);
  }
}

static int shadeImage(ImageG8 img, Shader shader, void *pUniforms, int threads)
{
  ShadeInfo info = { img, shader, pUniforms };
  return multiprocess(shadeImageChunk, img.size.x * img.size.y, threads, &info);
}

typedef struct
{
  ImageG8 img;
  Mat3 invTfm;
  Vec2i offset;
  uint8_t fill;
  int shouldInterpolate;
} TransformUniform;

static void transformShader(ShaderInvocation *pInvoc)
{
  TransformUniform *pUniform = pInvoc->pUniforms;
  Vec2d tfmedPos = { pInvoc->x + pUniform->offset.x, pInvoc->y + pUniform->offset.y };
  Vec2d pos = mulMat3Vec2d(&pUniform->invTfm, tfmedPos);
  Vec2i imgSize = pUniform->img.size;
  if (pos.x < 0 || pos.x > imgSize.x || pos.y < 0 || pos.y > imgSize.y)
  {
    *pInvoc->pOut = pUniform->fill;
  }
  if (pUniform->shouldInterpolate)
  {
    *pInvoc->pOut = getInterpolatedImageG8(pUniform->img, pos.x / imgSize.x, pos.y / imgSize.y);
  }
  else
  {
    *pInvoc->pOut = getImageG8(pUniform->img, pos.x, pos.y);
  }
}

const char *transform(
  ImageG8 img,
  Mat3 invTfm,
  Vec2i offset,
  uint8_t fill,
  int shouldInterpolate,
  ImageG8 result,
  int threads
) {
  TransformUniform uniform = {
    img,
    invTfm,
    offset,
    fill,
    shouldInterpolate
  };
  return errCodeToCStr(shadeImage(result, transformShader, &uniform, threads));
}

typedef struct
{
  ImageG8 img;
  ImageG8 kernel;
  Vec2i kernelCenter;
} ConvolutionUniform;

static void convolutionShader(ShaderInvocation *pInvoc)
{
  ConvolutionUniform *pUniform = pInvoc->pUniforms;
  double value = 0;
  for (int ky = 0; ky < pUniform->kernel.size.y; ++ky)
  {
    int sy = clampi(pInvoc->y - pUniform->kernelCenter.y + ky, pInvoc->imgSize.y - 1, 0);
    for (int kx = 0; kx < pUniform->kernel.size.x; ++kx)
    {
      int sx = clampi(pInvoc->x - pUniform->kernelCenter.x + kx, pInvoc->imgSize.x - 1, 0);
      int sample = getImageG8(pUniform->img, sx, sy);
      double weight = (double)getImageG8(pUniform->kernel, kx, ky) / 128 - 1;
      value += sample * weight;
    }
  }
  *pInvoc->pOut = clampi(value, 0, 255);
}

const char *convolve(
  ImageG8 img,
  ImageG8 kernel,
  ImageG8 result,
  int threads
) {
  ConvolutionUniform uniform = {
    img,
    kernel,
    { kernel.size.x / 2, kernel.size.y / 2 }
  };
  return errCodeToCStr(shadeImage(result, convolutionShader, &uniform, threads));
}
