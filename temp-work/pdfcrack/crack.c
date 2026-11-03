/*
 * Sharded search for a PDF "Standard security handler" user password
 * (revision 3 / V 2, RC4 128-bit, EncryptMetadata true).
 *
 * Safety rule for this repository: the candidate password is NEVER printed.
 * On a hit the program prints only the candidate index inside the space
 * [0, base^length); the password is regenerated locally from that index.
 *
 * Usage:
 *   crack <O-hex> <U-hex> <P> <ID0-hex> <charset> <length> <start> <end> <budget-seconds>
 *
 * Output lines:
 *   space  len=.. base=.. total=.. start=.. end=.. threads=..
 *   progress done=.. elapsed=..s rate=../s
 *   HIT <index>
 *   MISS done=.. elapsed=.. rate=../s
 *   BUDGET done=.. elapsed=.. (time budget reached before end)
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <omp.h>

typedef unsigned long long u64;

static uint8_t g_static[52];  /* O(32) || P(4 little endian) || ID0(16) */
static uint8_t g_U[32];
static uint8_t g_uhash[16];   /* MD5(PAD || ID0) */
static volatile int g_hit = 0;
static volatile u64 g_hit_index = 0;

static const uint8_t PAD[32] = {
    0x28,0xBF,0x4E,0x5E,0x4E,0x75,0x8A,0x41,0x64,0x00,0x4E,0x56,0xFF,0xFA,0x01,0x08,
    0x2E,0x2E,0x00,0xB6,0xD0,0x68,0x3E,0x80,0x2F,0x0C,0xA9,0xFE,0x64,0x53,0x69,0x7A};

static const uint32_t K[64] = {
0xd76aa478,0xe8c7b756,0x242070db,0xc1bdceee,0xf57c0faf,0x4787c62a,0xa8304613,0xfd469501,
0x698098d8,0x8b44f7af,0xffff5bb1,0x895cd7be,0x6b901122,0xfd987193,0xa679438e,0x49b40821,
0xf61e2562,0xc040b340,0x265e5a51,0xe9b6c7aa,0xd62f105d,0x02441453,0xd8a1e681,0xe7d3fbc8,
0x21e1cde6,0xc33707d6,0xf4d50d87,0x455a14ed,0xa9e3e905,0xfcefa3f8,0x676f02d9,0x8d2a4c8a,
0xfffa3942,0x8771f681,0x6d9d6122,0xfde5380c,0xa4beea44,0x4bdecfa9,0xf6bb4b60,0xbebfbc70,
0x289b7ec6,0xeaa127fa,0xd4ef3085,0x04881d05,0xd9d4d039,0xe6db99e5,0x1fa27cf8,0xc4ac5665,
0xf4292244,0x432aff97,0xab9423a7,0xfc93a039,0x655b59c3,0x8f0ccc92,0xffeff47d,0x85845dd1,
0x6fa87e4f,0xfe2ce6e0,0xa3014314,0x4e0811a1,0xf7537e82,0xbd3af235,0x2ad7d2bb,0xeb86d391};

static const uint8_t S[64] = {
7,12,17,22,7,12,17,22,7,12,17,22,7,12,17,22,
5,9,14,20,5,9,14,20,5,9,14,20,5,9,14,20,
4,11,16,23,4,11,16,23,4,11,16,23,4,11,16,23,
6,10,15,21,6,10,15,21,6,10,15,21,6,10,15,21};

#define ROTL(x, n) (((x) << (n)) | ((x) >> (32 - (n))))

static inline void md5_compress(uint32_t st[4], const uint8_t *p)
{
    uint32_t M[16];
    for (int i = 0; i < 16; i++)
        M[i] = (uint32_t)p[i * 4] | ((uint32_t)p[i * 4 + 1] << 8) |
               ((uint32_t)p[i * 4 + 2] << 16) | ((uint32_t)p[i * 4 + 3] << 24);
    uint32_t a = st[0], b = st[1], c = st[2], d = st[3];
    for (int i = 0; i < 64; i++) {
        uint32_t f;
        int g;
        if (i < 16)      { f = (b & c) | (~b & d); g = i; }
        else if (i < 32) { f = (d & b) | (~d & c); g = (5 * i + 1) & 15; }
        else if (i < 48) { f = b ^ c ^ d;          g = (3 * i + 5) & 15; }
        else             { f = c ^ (b | ~d);       g = (7 * i) & 15; }
        uint32_t tmp = d;
        d = c;
        c = b;
        b = b + ROTL(a + f + K[i] + M[g], S[i]);
        a = tmp;
    }
    st[0] += a; st[1] += b; st[2] += c; st[3] += d;
}

static inline void digest_out(const uint32_t st[4], uint8_t out[16])
{
    for (int i = 0; i < 4; i++) {
        out[i * 4]     = (uint8_t)(st[i]);
        out[i * 4 + 1] = (uint8_t)(st[i] >> 8);
        out[i * 4 + 2] = (uint8_t)(st[i] >> 16);
        out[i * 4 + 3] = (uint8_t)(st[i] >> 24);
    }
}

static inline void md5_16(const uint8_t in[16], uint8_t out[16])
{
    uint8_t blk[64];
    memcpy(blk, in, 16);
    blk[16] = 0x80;
    memset(blk + 17, 0, 39);
    blk[56] = 0x80; /* bit length 128 */
    blk[57] = 0; blk[58] = 0; blk[59] = 0;
    blk[60] = 0; blk[61] = 0; blk[62] = 0; blk[63] = 0;
    uint32_t st[4] = {0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476};
    md5_compress(st, blk);
    digest_out(st, out);
}

/* Algorithm 2 for R3: MD5(padded pw || O || P || ID0), 50 rehashes, 16-byte key. */
static inline void derive_key(const char *pw, int len, uint8_t key[16])
{
    uint8_t b[32], blk[64], blk2[64], t16[16];
    memcpy(b, pw, (size_t)len);
    memcpy(b + len, PAD, (size_t)(32 - len));

    memcpy(blk, b, 32);
    memcpy(blk + 32, g_static, 32);
    uint32_t st[4] = {0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476};
    md5_compress(st, blk);

    memset(blk2, 0, sizeof blk2);
    memcpy(blk2, g_static + 32, 20); /* P || ID0 */
    blk2[20] = 0x80;
    blk2[56] = 0xA0; /* bit length 84 * 8 = 672 */
    blk2[57] = 0x02;
    md5_compress(st, blk2);

    digest_out(st, key);
    for (int k = 0; k < 50; k++) {
        md5_16(key, t16);
        memcpy(key, t16, 16);
    }
}

/* Algorithm 5 for R3: U = 20 RC4 passes over MD5(PAD || ID0), key XOR pass counter. */
static inline int check(const char *pw, int len)
{
    uint8_t key[16];
    derive_key(pw, len, key);

    uint8_t h[16];
    memcpy(h, g_uhash, 16);
    for (int it = 0; it < 20; it++) {
        uint8_t k[16], s[256];
        for (int i = 0; i < 16; i++) k[i] = (uint8_t)(key[i] ^ it);
        for (int i = 0; i < 256; i++) s[i] = (uint8_t)i;
        int j = 0;
        for (int i = 0; i < 256; i++) {
            j = (j + s[i] + k[i & 15]) & 255;
            uint8_t t = s[i]; s[i] = (uint8_t)s[j]; s[j] = t;
        }
        int i = 0;
        j = 0;
        for (int n = 0; n < 16; n++) {
            i = (i + 1) & 255;
            j = (j + s[i]) & 255;
            uint8_t t = s[i]; s[i] = (uint8_t)s[j]; s[j] = t;
            h[n] ^= s[(s[i] + s[j]) & 255];
        }
    }
    return memcmp(h, g_U, 16) == 0;
}

static int hex2bin(const char *h, uint8_t *out, int n)
{
    for (int i = 0; i < n; i++) {
        unsigned v;
        if (sscanf(h + i * 2, "%2x", &v) != 1) return 0;
        out[i] = (uint8_t)v;
    }
    return 1;
}

int main(int argc, char **argv)
{
    if (argc < 10) {
        fprintf(stderr,
            "usage: %s <O-hex> <U-hex> <P> <ID0-hex> <charset> <length> <start> <end> <budget-seconds>\n",
            argv[0]);
        return 2;
    }

    memset(g_static, 0, sizeof g_static);
    if (!hex2bin(argv[1], g_static, 32)) { fprintf(stderr, "bad O\n"); return 2; }
    if (!hex2bin(argv[2], g_U, 32))      { fprintf(stderr, "bad U\n"); return 2; }
    long P = strtol(argv[3], NULL, 10);
    g_static[32] = (uint8_t)(P & 0xff);
    g_static[33] = (uint8_t)((P >> 8) & 0xff);
    g_static[34] = (uint8_t)((P >> 16) & 0xff);
    g_static[35] = (uint8_t)((P >> 24) & 0xff);
    if (!hex2bin(argv[4], g_static + 36, 16)) { fprintf(stderr, "bad ID0\n"); return 2; }

    {
        uint8_t blk[64];
        memset(blk, 0, sizeof blk);
        memcpy(blk, PAD, 32);
        memcpy(blk + 32, g_static + 36, 16);
        blk[48] = 0x80;
        blk[56] = 0x80; /* bit length 384 */
        blk[57] = 0x01;
        uint32_t st[4] = {0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476};
        md5_compress(st, blk);
        digest_out(st, g_uhash);
    }

    const char *charset = argv[5];
    int base = (int)strlen(charset);
    int len = atoi(argv[6]);
    u64 start = strtoull(argv[7], NULL, 10);
    u64 end = strtoull(argv[8], NULL, 10);
    double budget = atof(argv[9]);

    if (base < 1 || len < 1 || len > 32) { fprintf(stderr, "bad charset/length\n"); return 2; }

    u64 total = 1;
    for (int i = 0; i < len; i++) {
        if (total > ULLONG_MAX / (u64)base) { total = ULLONG_MAX; break; }
        total *= (u64)base;
    }
    if (end > total) end = total;
    if (start >= end) {
        printf("EMPTY start=%llu end=%llu total=%llu\n", start, end, total);
        return 0;
    }

    int threads = omp_get_max_threads();
    printf("space len=%d base=%d total=%llu start=%llu end=%llu threads=%d budget=%.0fs\n",
           len, base, total, start, end, threads, budget);
    fflush(stdout);

    const u64 BLK = 1u << 14;
    u64 span = end - start;
    u64 nblocks = (span + BLK - 1) / BLK;
    double t0 = omp_get_wtime();
    u64 done = 0;
    int budget_hit = 0;

    #pragma omp parallel for schedule(dynamic, 1)
    for (u64 b = 0; b < nblocks; b++) {
        int stop;
        #pragma omp atomic read
        stop = g_hit;
        if (stop) continue;
        if (budget > 0 && omp_get_wtime() - t0 > budget) continue;

        u64 lo = start + b * BLK;
        u64 hi = lo + BLK;
        if (hi > end) hi = end;

        char buf[64];
        for (u64 idx = lo; idx < hi; idx++) {
            u64 v = idx;
            for (int i = len - 1; i >= 0; i--) {
                buf[i] = charset[v % (u64)base];
                v /= (u64)base;
            }
            if (check(buf, len)) {
                #pragma omp atomic write
                g_hit = 1;
                #pragma omp critical
                { g_hit_index = idx; printf("HIT %llu\n", idx); fflush(stdout); }
                break;
            }
        }

        #pragma omp atomic update
        done += hi - lo;

        if (omp_get_thread_num() == 0 && (b & 63) == 0) {
            double el = omp_get_wtime() - t0;
            u64 d;
            #pragma omp atomic read
            d = done;
            printf("progress done=%llu elapsed=%.0fs rate=%.0f/s\n",
                   d, el, el > 0 ? (double)d / el : 0.0);
            fflush(stdout);
        }
    }

    double el = omp_get_wtime() - t0;
    int hit;
    #pragma omp atomic read
    hit = g_hit;
    if (hit) {
        u64 hi_idx;
        #pragma omp atomic read
        hi_idx = g_hit_index;
        printf("HITINFO index=%llu elapsed=%.0fs\n", hi_idx, el);
        return 0;
    }
    if (budget > 0 && el >= budget && (u64)done < span) budget_hit = 1;
    /* BUDGET means part of this window was skipped and must be re-run. */
    printf("%s done=%llu elapsed=%.0fs rate=%.0f/s\n",
           budget_hit ? "BUDGET" : "MISS", (u64)done, el, el > 0 ? (double)done / el : 0.0);
    return 0;
}
