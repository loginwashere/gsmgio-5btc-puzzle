#define PHASE484_WIDTH 30
#define PHASE484_ROWS 19
#define PHASE484N_PREFIX_SCORE_NO_MAIN
#include "phase484n_prefix_score_benchmark.cu"

#include <cstring>

template <typename T>
static bool read_exact_y(T *target, size_t count) {
  return std::fread(target, sizeof(T), count, stdin) == count;
}

int main() {
  char magic[8];
  if (!read_exact_y(magic, size_t(8)) || std::memcmp(magic, "P484YG1\0", 8)) return 3;
  unsigned char blocks[WIDTH * ROWS];
  double coef[FEATURES], intercept;
  if (!read_exact_y(blocks, size_t(WIDTH * ROWS)) ||
      !read_exact_y(coef, size_t(FEATURES)) ||
      !read_exact_y(&intercept, size_t(1))) return 3;

  unsigned char *d_blocks = nullptr, *d_paths = nullptr;
  double *d_coef = nullptr, *d_scores = nullptr;
  size_t path_capacity = 0, score_capacity = 0;
  CUDA_OK(cudaMalloc(&d_blocks, sizeof(blocks)));
  CUDA_OK(cudaMalloc(&d_coef, sizeof(coef)));
  CUDA_OK(cudaMemcpy(d_blocks, blocks, sizeof(blocks), cudaMemcpyHostToDevice));
  CUDA_OK(cudaMemcpy(d_coef, coef, sizeof(coef), cudaMemcpyHostToDevice));

  for (;;) {
    uint32_t header[2];
    if (!read_exact_y(header, size_t(2))) break;
    const size_t count = header[0];
    const int depth = int(header[1]);
    if (!count) break;
    if (depth < 4 || depth > WIDTH || count > (1u << 25)) return 4;
    const size_t path_bytes = count * size_t(depth);
    std::vector<unsigned char> paths(path_bytes);
    std::vector<double> scores(count);
    if (!read_exact_y(paths.data(), path_bytes)) return 3;
    if (path_bytes > path_capacity) {
      if (d_paths) CUDA_OK(cudaFree(d_paths));
      CUDA_OK(cudaMalloc(&d_paths, path_bytes));
      path_capacity = path_bytes;
    }
    if (count > score_capacity) {
      if (d_scores) CUDA_OK(cudaFree(d_scores));
      CUDA_OK(cudaMalloc(&d_scores, count * sizeof(double)));
      score_capacity = count;
    }
    CUDA_OK(cudaMemcpy(d_paths, paths.data(), path_bytes, cudaMemcpyHostToDevice));
    score_kernel<<<(count + 127) / 128, 128>>>(
        d_blocks, d_paths, int(count), depth, d_coef, intercept, d_scores);
    CUDA_OK(cudaGetLastError());
    CUDA_OK(cudaMemcpy(scores.data(), d_scores, count * sizeof(double), cudaMemcpyDeviceToHost));
    if (std::fwrite(scores.data(), sizeof(double), count, stdout) != count) return 5;
    std::fflush(stdout);
  }
  if (d_scores) CUDA_OK(cudaFree(d_scores));
  if (d_paths) CUDA_OK(cudaFree(d_paths));
  CUDA_OK(cudaFree(d_coef));
  CUDA_OK(cudaFree(d_blocks));
  return 0;
}
