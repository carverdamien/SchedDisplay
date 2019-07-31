#define _GNU_SOURCE
#include <dlfcn.h>
#include <sys/time.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>

typedef int (*original_gettimeofday_f_type)(struct timeval *tv, struct timezone *tz);

#ifdef __i386
extern __inline__ uint64_t rdtsc(void) {
  uint64_t x;
  __asm__ volatile ("rdtsc" : "=A" (x));
  return x;
}
#elif defined __amd64
extern __inline__ uint64_t rdtsc(void) {
  uint64_t a, d;
  __asm__ volatile ("rdtsc" : "=a" (a), "=d" (d));
  return (d<<32) | a;
}
#endif

int gettimeofday(struct timeval *tv, struct timezone *tz) {
  struct timespec tp;
  int ret;
  original_gettimeofday_f_type original_gettimeofday = (original_gettimeofday_f_type) dlsym(RTLD_NEXT,"gettimeofday");
  ret = original_gettimeofday(tv, tz);
  // printf("Time: %lu.%03lu\n", tv->tv_sec, tv->tv_usec / 1000);
  // printf("gettimeofday: tv_sec=%lu tv_usec=%lu\n", tv->tv_sec, tv->tv_usec);
  if (!clock_gettime(CLOCK_MONOTONIC_RAW, &tp)) {
    // printf("clock_gettime(CLOCK_MONOTONIC_RAW): tv_sec=%lu tv_nsec=%lu\n", tp.tv_sec, tp.tv_nsec);
  }
  // if (!clock_gettime(CLOCK_BOOTTIME, &tp)) {
    // printf("clock_gettime(CLOCK_BOOTTIME): tv_sec=%lu tv_nsec=%lu\n", tp.tv_sec, tp.tv_nsec);
  // }
  // printf("%llu\n",__builtin_ia32_rdtsc());
  // printf("%llu\n",rdtsc());
  return ret;
}
