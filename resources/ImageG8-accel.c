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

static void mulMat3Vec2d(double mat[9], Vec2d vec, Vec2d *pResult)
{
  pResult->x = mat[0] * vec.x + mat[1] * vec.y + mat[2];
  pResult->y = mat[3] * vec.x + mat[4] * vec.y + mat[3];
}

static double rowColDot(
  double a[9],
  int row,
  double b[9],
  int col,
) {
  int aStart = row * 3;
  return a[aStart] * b[col]
    + a[aStart + 1] * b[col + 3]
    + a[aStart + 2] * b[col + 6];
}

static void mulMat3Mat3(double a[9], double b[9], double result[9])
{
  for (int i = 0; i < 9; ++i)
  {
    div_t d = div(i, 3);
    result[i] = rowColDot(a, d.quot, b, d.rem);
  }
}

typedef void (*Multiprocessable)(int start, int end, int id, void *pArg);

typedef struct
{
  Multiprocessable func;
  int start;
  int end;
  int id;
  void *pArg;
} MultiprocessInvocation;

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
    func(0, range, 0, pArg);
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
    pInvoc->pArg = pArg;
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
  NumberAggregateInfo *pInfo = pInvoc->pArg;
  uint32_t result = 0;
  for (int i = pInvoc->start; i < pInvoc->end; ++i)
  {
    result = result < pInfo->pData[i] ? result : pInfo->pData[i];
  }
  pInfo->pResults[pInvoc->id] = result;
}

static void maxChunk(MultiprocessInvocation *pInvoc)
{
  NumberAggregateInfo *pInfo = pInvoc->pArg;
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
  func(0, threads, 0, &aggInfo);
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
  NormalizeInfo *pInfo = pInvoc->pArg;
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
  TemplateMatchInfo *pInfo = pInvoc->pArg;
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
        int a = pInfo->image.pData[pInfo->image.size.x * (ay + by) + ax + bx];
        int b = pInfo->template.pData[pInfo->template.size.x * by + bx];
        int maskFac = pInfo->pMask ? pInfo->pMask->pData[pInfo->pMask->size.x * by + bx] : 255;
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

const char *templateMatch(
  ImageG8 image,
  ImageG8 template,
  ImageG8 *pMask,
  ImageG8 out,
  int threads
) {
  switch (templateMatchImpl(image, template, pMask, out, threads))
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

typedef struct
{
  Vec2i pos;
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
  Vec2i size = pInfo->img.size:
  ShaderInvocation shaderInvoc = {{0, 0}, size, pInfo->pUniforms, pInfo->img.data};
  for (int i = pArg->start; i < pArg->end; ++i)
  {
    div_t d = div(i, size.x);
    shaderInvoc.pos.y = d.quot;
    shaderInvoc.pos.x = d.rem;
    ++shaderInvoc.pOut;
    pInfo->shader(&shaderInvoc);
  }
}

static void shadeImage(ImageG8 img, Shader shader, void *pUniforms, int threads)
{
  ShadeInfo info = { img, shader, pUniforms };
  multiprocess(shadeImageChunk, img.size.x * img.size.y, threads, &info);
}

typedef struct
{
  ImageG8 img;
  double invTfm[9];
  Vec2i offset;
  Vec2i resultSize;
  uint8_t fill;
  bool interpolate;
} TransformUniform;

static void transformShader(ShaderInvocation *pInvoc)
{
  TransformUniform *pUniform = pInvoc->pUniform;
  Vec2d tfmedPos = { pInvoc->pos.x + pUniform->offset.x, pInvoc->pos.y + pUniform->offset.y };
  Vec2d pos = mulMat3Vec2d(pUniform->invTfm, tfmedPos);
  Vec2i imgSize = pUniform->img.size;
  if (pos.x < 0 || pox.x > imgSize.x || pos.y < 0 || pos.y > imgSize.y)
  {
    *pInvoc->pOut = pUniform->fill;
  }
  if (pUniform->interpolate)
  {
    *pInvoc->pOut = getInterpolatedImageG8(pos.x / imgSize.x, pos.y / imgSize.y);
  }
  else
  {
    *pInvoc->pOut = pUniform->img.data[imgSize.x * pos.y + pos.x];
  }
}
