#include <cuda_runtime.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

constexpr int WIDTH = 19;
constexpr int ROWS = 30;
constexpr int SLOTS = 25;
constexpr int QUAD_SIZE = 25 * 25 * 25 * 25;

#define CUDA_OK(call) do { cudaError_t e = (call); if (e != cudaSuccess) { \
  std::fprintf(stderr, "%s\n", cudaGetErrorString(e)); std::exit(2); } } while (0)

__global__ void board_score_kernel(const unsigned char *blocks,
    const unsigned char *paths, int count, int depth,
    const unsigned char *board, const double *quad, double *scores) {
  int index = blockIdx.x * blockDim.x + threadIdx.x;
  if (index >= count) return;
  const unsigned char *path = paths + size_t(index) * depth;
  double total = 0.0;
  int windows = 0;
  for (int row = 0; row < ROWS; ++row) {
    unsigned char letters[WIDTH];
    int length = 0;
    for (int j = 0; j < depth;) {
      int symbol = blocks[int(path[j]) * ROWS + row];
      if (symbol < 2) {
        if (j + 1 == depth) break;
        int next = blocks[int(path[j + 1]) * ROWS + row];
        letters[length++] = board[7 + symbol * 9 + next];
        j += 2;
      } else {
        letters[length++] = board[symbol - 2];
        ++j;
      }
    }
    for (int j = 3; j < length; ++j) {
      int key = ((int(letters[j - 3]) * 25 + letters[j - 2]) * 25 +
                 letters[j - 1]) * 25 + letters[j];
      total += quad[key];
      ++windows;
    }
  }
  scores[index] = windows ? total / windows : -1.0e9;
}

template <typename T> bool read_exact(T *target, size_t count) {
  return std::fread(target, sizeof(T), count, stdin) == count;
}

int main() {
  char magic[8];
  if (!read_exact(magic, size_t(8)) ||
      std::memcmp(magic, "P484WG1\0", 8)) return 3;
  unsigned char blocks[WIDTH * ROWS];
  std::vector<double> quad(QUAD_SIZE);
  if (!read_exact(blocks, size_t(WIDTH * ROWS)) ||
      !read_exact(quad.data(), size_t(QUAD_SIZE))) return 3;

  unsigned char *d_blocks, *d_board, *d_paths = nullptr;
  double *d_quad, *d_scores = nullptr;
  size_t path_capacity = 0, score_capacity = 0;
  CUDA_OK(cudaMalloc(&d_blocks, sizeof(blocks)));
  CUDA_OK(cudaMalloc(&d_board, SLOTS));
  CUDA_OK(cudaMalloc(&d_quad, sizeof(double) * QUAD_SIZE));
  CUDA_OK(cudaMemcpy(d_blocks, blocks, sizeof(blocks), cudaMemcpyHostToDevice));
  CUDA_OK(cudaMemcpy(d_quad, quad.data(), sizeof(double) * QUAD_SIZE,
                     cudaMemcpyHostToDevice));

  bool board_loaded = false;
  for (;;) {
    uint32_t command;
    if (!read_exact(&command, size_t(1))) break;
    if (command == 0) break;
    if (command == 1) {
      unsigned char board[SLOTS];
      if (!read_exact(board, size_t(SLOTS))) return 3;
      CUDA_OK(cudaMemcpy(d_board, board, SLOTS, cudaMemcpyHostToDevice));
      board_loaded = true;
      continue;
    }
    if (command != 2 || !board_loaded) return 4;
    uint32_t header[2];
    if (!read_exact(header, size_t(2))) return 3;
    size_t count = header[0];
    int depth = int(header[1]);
    if (!count || count > (1u << 24) || depth < 4 || depth > WIDTH) return 4;
    size_t path_bytes = count * size_t(depth);
    std::vector<unsigned char> paths(path_bytes);
    std::vector<double> scores(count);
    if (!read_exact(paths.data(), path_bytes)) return 3;
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
    CUDA_OK(cudaMemcpy(d_paths, paths.data(), path_bytes,
                       cudaMemcpyHostToDevice));
    board_score_kernel<<<(count + 127) / 128, 128>>>(
        d_blocks, d_paths, int(count), depth, d_board, d_quad, d_scores);
    CUDA_OK(cudaGetLastError());
    CUDA_OK(cudaMemcpy(scores.data(), d_scores, count * sizeof(double),
                       cudaMemcpyDeviceToHost));
    if (std::fwrite(scores.data(), sizeof(double), count, stdout) != count)
      return 5;
    std::fflush(stdout);
  }
  return 0;
}
