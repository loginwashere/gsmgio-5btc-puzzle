#include <cuda_runtime.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

#ifndef PHASE484_WIDTH
#define PHASE484_WIDTH 19
#endif
#ifndef PHASE484_ROWS
#define PHASE484_ROWS 30
#endif
constexpr int WIDTH = PHASE484_WIDTH;
constexpr int ROWS = PHASE484_ROWS;
constexpr int TOKENS = 25;
constexpr int FEATURES = 20;

#define CUDA_OK(call) do { \
  cudaError_t e = (call); \
  if (e != cudaSuccess) { std::fprintf(stderr, "%s\n", cudaGetErrorString(e)); std::exit(2); } \
} while (0)

__host__ __device__ double entropy_term(const unsigned short *counts, int n,
                                         int total) {
  if (!total) return 0.0;
  double value = 0.0;
  for (int i = 0; i < n; ++i) {
    if (counts[i]) {
      const double p = double(counts[i]) / double(total);
      value -= p * log(p);
    }
  }
  return value;
}

__host__ __device__ double score_one(const unsigned char *blocks,
                                      const unsigned char *path, int depth,
                                      const double *coef, double intercept) {
  unsigned short counts[TOKENS] = {};
  unsigned short transitions[TOKENS * TOKENS] = {};
  int flat_total = 0, singles = 0, incomplete = 0;
  int start_escape = 0, end_escape = 0, raw_equal = 0;
  int lag_match[8] = {}, lag_total[8] = {};

  for (int row = 0; row < ROWS; ++row) {
    int sequence[WIDTH];
    int sequence_length = 0;
    unsigned char chars[WIDTH];
    for (int j = 0; j < depth; ++j) {
      chars[j] = blocks[int(path[j]) * ROWS + row];
      if (j && chars[j] == chars[j - 1]) ++raw_equal;
    }
    start_escape += chars[0] < 2;
    end_escape += chars[depth - 1] < 2;
    int j = 0;
    while (j < depth) {
      const int symbol = chars[j];
      if (symbol < 2) {
        if (j + 1 == depth) { ++incomplete; break; }
        sequence[sequence_length++] = 7 + symbol * 9 + chars[j + 1];
        j += 2;
      } else {
        sequence[sequence_length++] = symbol - 2;
        ++singles;
        ++j;
      }
    }
    flat_total += sequence_length;
    for (int k = 0; k < sequence_length; ++k) {
      ++counts[sequence[k]];
      if (k) ++transitions[sequence[k - 1] * TOKENS + sequence[k]];
    }
    for (int lag = 1; lag <= 8; ++lag) {
      for (int k = lag; k < sequence_length; ++k) {
        lag_match[lag - 1] += sequence[k] == sequence[k - lag];
        ++lag_total[lag - 1];
      }
    }
  }

  const int raw_symbols = ROWS * depth;
  const int raw_pairs = ROWS * (depth - 1);
  const int transition_total = flat_total - ROWS;
  int occupied_counts = 0, occupied_transitions = 0, trace = 0;
  double symmetry = 0.0;
  for (int i = 0; i < TOKENS; ++i) occupied_counts += counts[i] != 0;
  for (int i = 0; i < TOKENS; ++i) {
    for (int j = 0; j < TOKENS; ++j) {
      const int v = transitions[i * TOKENS + j];
      occupied_transitions += v != 0;
      if (i == j) trace += v;
      symmetry += double(v) * double(transitions[j * TOKENS + i]);
    }
  }
  double f[FEATURES];
  f[0] = double(flat_total) / raw_symbols;
  f[1] = double(singles) / (flat_total ? flat_total : 1);
  f[2] = double(occupied_counts) / 25.0;
  f[3] = entropy_term(counts, TOKENS, flat_total) / log(25.0);
  f[4] = entropy_term(transitions, TOKENS * TOKENS, transition_total) / log(625.0);
  f[5] = transition_total ? double(trace) / transition_total : 0.0;
  f[6] = transition_total ? symmetry / (double(transition_total) * transition_total) : 0.0;
  f[7] = double(occupied_transitions) / 625.0;
  f[8] = double(incomplete) / ROWS;
  f[9] = double(end_escape) / ROWS;
  f[10] = double(start_escape) / ROWS;
  f[11] = raw_pairs ? double(raw_equal) / raw_pairs : 0.0;
  for (int lag = 0; lag < 8; ++lag)
    f[12 + lag] = lag_total[lag] ? double(lag_match[lag]) / lag_total[lag] : 0.0;
  double score = intercept;
  for (int i = 0; i < FEATURES; ++i) score += coef[i] * f[i];
  return score;
}

__global__ void score_kernel(const unsigned char *blocks,
                             const unsigned char *paths, int count, int depth,
                             const double *coef, double intercept,
                             double *scores) {
  const int index = blockIdx.x * blockDim.x + threadIdx.x;
  if (index < count)
    scores[index] = score_one(blocks, paths + index * depth, depth, coef, intercept);
}

static uint32_t next32(uint64_t &state) {
  state = state * 6364136223846793005ULL + 1442695040888963407ULL;
  return uint32_t(state >> 32);
}

#ifndef PHASE484N_PREFIX_SCORE_NO_MAIN
int main(int argc, char **argv) {
  const int count = argc > 1 ? std::atoi(argv[1]) : 65536;
  const int depth = argc > 2 ? std::atoi(argv[2]) : 8;
  const int repeats = argc > 3 ? std::atoi(argv[3]) : 5;
  if (count < 1 || depth < 4 || depth > WIDTH || repeats < 1) return 2;
  std::vector<unsigned char> blocks(WIDTH * ROWS), paths(size_t(count) * depth);
  double coef[FEATURES];
  uint64_t state = 0x484E000ULL;
  for (auto &v : blocks) v = next32(state) % 9;
  for (int i = 0; i < FEATURES; ++i) coef[i] = (double(int(next32(state) % 2001) - 1000)) / 997.0;
  for (int n = 0; n < count; ++n) {
    unsigned char values[WIDTH];
    for (int i = 0; i < WIDTH; ++i) values[i] = i;
    for (int i = WIDTH - 1; i > 0; --i) {
      int j = next32(state) % (i + 1);
      std::swap(values[i], values[j]);
    }
    std::copy(values, values + depth, paths.begin() + size_t(n) * depth);
  }

  unsigned char *d_blocks, *d_paths;
  double *d_coef, *d_scores;
  CUDA_OK(cudaMalloc(&d_blocks, blocks.size()));
  CUDA_OK(cudaMalloc(&d_paths, paths.size()));
  CUDA_OK(cudaMalloc(&d_coef, sizeof(coef)));
  CUDA_OK(cudaMalloc(&d_scores, sizeof(double) * count));
  CUDA_OK(cudaMemcpy(d_blocks, blocks.data(), blocks.size(), cudaMemcpyHostToDevice));
  CUDA_OK(cudaMemcpy(d_paths, paths.data(), paths.size(), cudaMemcpyHostToDevice));
  CUDA_OK(cudaMemcpy(d_coef, coef, sizeof(coef), cudaMemcpyHostToDevice));
  score_kernel<<<(count + 127) / 128, 128>>>(d_blocks, d_paths, count, depth, d_coef, 0.125, d_scores);
  CUDA_OK(cudaDeviceSynchronize());

  cudaEvent_t start, stop;
  CUDA_OK(cudaEventCreate(&start)); CUDA_OK(cudaEventCreate(&stop));
  CUDA_OK(cudaEventRecord(start));
  for (int r = 0; r < repeats; ++r)
    score_kernel<<<(count + 127) / 128, 128>>>(d_blocks, d_paths, count, depth, d_coef, 0.125, d_scores);
  CUDA_OK(cudaEventRecord(stop)); CUDA_OK(cudaEventSynchronize(stop));
  float gpu_ms = 0; CUDA_OK(cudaEventElapsedTime(&gpu_ms, start, stop));
  std::vector<double> gpu_scores(count);
  CUDA_OK(cudaMemcpy(gpu_scores.data(), d_scores, sizeof(double) * count, cudaMemcpyDeviceToHost));

  const int cpu_count = std::min(count, 2048);
  std::vector<double> cpu_scores(cpu_count);
  const auto cpu_start = std::chrono::steady_clock::now();
  for (int i = 0; i < cpu_count; ++i)
    cpu_scores[i] = score_one(blocks.data(), paths.data() + size_t(i) * depth, depth, coef, 0.125);
  const double cpu_seconds = std::chrono::duration<double>(
      std::chrono::steady_clock::now() - cpu_start).count();
  double max_error = 0;
  for (int i = 0; i < cpu_count; ++i)
    max_error = std::max(max_error, std::abs(cpu_scores[i] - gpu_scores[i]));
  const double gpu_seconds = gpu_ms / 1000.0;
  const double gpu_rate = double(count) * repeats / gpu_seconds;
  const double cpu_rate = cpu_count / cpu_seconds;
  std::printf("{\"paths\":%d,\"depth\":%d,\"repeats\":%d,", count, depth, repeats);
  std::printf("\"cpu_paths_per_second\":%.3f,\"gpu_paths_per_second\":%.3f,", cpu_rate, gpu_rate);
  std::printf("\"speedup\":%.3f,\"max_abs_error\":%.17g,", gpu_rate / cpu_rate, max_error);
  std::printf("\"parity\":%s}\n", max_error <= 1e-10 ? "true" : "false");
  return max_error <= 1e-10 ? 0 : 1;
}
#endif
