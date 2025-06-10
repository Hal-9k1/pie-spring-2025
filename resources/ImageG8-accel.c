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
  Vec2i size;
  uint8_t *pData;
} ImageG8;

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
  pInvoc->func(pInvoc->start, pInvoc->end, pInvoc->id, pInvoc->pArg);
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
  ImageG8 image;
  ImageG8 template;
  ImageG8 *pMask;
  Vec2i resultSize;
  double errScalingFac;
  uint32_t *pBuf;
} TemplateMatchInfo;

static void templateMatchChunk(int start, int end, int id, void *pArg)
{
  TemplateMatchInfo *pInfo = pArg;
  for (int i = start; i < end; ++i)
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
    pInfo->pBuf[i - start] = ceil(err * pInfo->errScalingFac);
  }
}

typedef struct
{
  uint32_t *pResults;
  uint32_t *pData;
} NumberAggregateInfo;

static void minChunk(int start, int end, int id, void *pArg)
{
  NumberAggregateInfo *pInfo = pArg;
  uint32_t result = 0;
  for (int i = start; i < end; ++i)
  {
    result = result < pInfo->pData[i] ? result : pInfo->pData[i];
  }
  pInfo->pResults[id] = result;
}

static void maxChunk(int start, int end, int id, void *pArg)
{
  NumberAggregateInfo *pInfo = pArg;
  uint32_t result = 0;
  for (int i = start; i < end; ++i)
  {
    result = result > pInfo->pData[i] ? result : pInfo->pData[i];
  }
  pInfo->pResults[id] = result;
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

static void normalizeErrorChunk(int start, int end, int id, void *pArg)
{
  NormalizeInfo *pInfo = pArg;
  for (int i = start; i < end; ++i)
  {
    pInfo->pResults[i] = (pInfo->pData[i] - pInfo->low) * pInfo->scale;
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
  double scale = high != low ? 255 / (high - low) : 1;
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
