#include <stdint.h>
#include <math.h>

#define FREE_COUNT 16
#define CELL_COUNT 25
#define TEXT_LENGTH 570
#define TAIL_START 7
#define BLOCK_SIZE 256

struct BlockBest {
    uint64_t rank;
    float score;
    uint32_t valid;
};

__device__ __constant__ uint64_t FACTORIALS[17] = {
    1ULL,
    1ULL,
    2ULL,
    6ULL,
    24ULL,
    120ULL,
    720ULL,
    5040ULL,
    40320ULL,
    362880ULL,
    3628800ULL,
    39916800ULL,
    479001600ULL,
    6227020800ULL,
    87178291200ULL,
    1307674368000ULL,
    20922789888000ULL
};

__device__ __forceinline__ void unrank16(uint64_t rank, uint8_t permutation[FREE_COUNT]) {
    uint8_t available[FREE_COUNT];
    #pragma unroll
    for (int i = 0; i < FREE_COUNT; ++i) available[i] = (uint8_t)i;
    int available_len = FREE_COUNT;

    #pragma unroll
    for (int position = 0; position < FREE_COUNT; ++position) {
        int remaining = FREE_COUNT - 1 - position;
        uint64_t factor = FACTORIALS[remaining];
        int selected = (int)(rank / factor);
        rank %= factor;
        permutation[position] = available[selected];
        #pragma unroll
        for (int i = 0; i < FREE_COUNT - 1; ++i) {
            if (i >= selected && i + 1 < available_len) available[i] = available[i + 1];
        }
        --available_len;
    }
}

__device__ __forceinline__ uint8_t decoded_symbol(
    int output_index,
    const uint8_t* __restrict__ faed_symbols,
    const uint8_t cell_symbols[CELL_COUNT],
    const uint8_t symbol_cells[CELL_COUNT]
) {
    int left_flat = output_index;
    int right_flat = TEXT_LENGTH + output_index;
    uint8_t left_cell = symbol_cells[faed_symbols[left_flat >> 1]];
    uint8_t right_cell = symbol_cells[faed_symbols[right_flat >> 1]];
    uint8_t left = (left_flat & 1) ? (left_cell % 5) : (left_cell / 5);
    uint8_t right = (right_flat & 1) ? (right_cell % 5) : (right_cell / 5);
    return cell_symbols[left * 5 + right];
}

__device__ __forceinline__ float score_rank(
    uint64_t rank,
    const uint8_t* __restrict__ faed_symbols,
    const uint8_t* __restrict__ base_cell_symbols,
    const uint8_t* __restrict__ free_positions,
    const uint8_t* __restrict__ free_symbols,
    const float* __restrict__ quadgrams
) {
    uint8_t permutation[FREE_COUNT];
    uint8_t cell_symbols[CELL_COUNT];
    uint8_t symbol_cells[CELL_COUNT];
    unrank16(rank, permutation);

    #pragma unroll
    for (int i = 0; i < CELL_COUNT; ++i) cell_symbols[i] = base_cell_symbols[i];
    #pragma unroll
    for (int i = 0; i < FREE_COUNT; ++i) {
        cell_symbols[free_positions[i]] = free_symbols[permutation[i]];
    }
    #pragma unroll
    for (int i = 0; i < CELL_COUNT; ++i) symbol_cells[cell_symbols[i]] = (uint8_t)i;

    uint32_t rolling = 0;
    #pragma unroll
    for (int i = TAIL_START; i < TAIL_START + 3; ++i) {
        rolling = rolling * 25u + (uint32_t)decoded_symbol(
            i, faed_symbols, cell_symbols, symbol_cells
        );
    }
    float total = 0.0f;
    for (int i = TAIL_START + 3; i < TEXT_LENGTH; ++i) {
        rolling = (rolling % 15625u) * 25u + (uint32_t)decoded_symbol(
            i, faed_symbols, cell_symbols, symbol_cells
        );
        total += quadgrams[rolling];
    }
    return total;
}

extern "C" __global__ void bifid_crib_block_best(
    uint64_t start_rank,
    uint64_t candidate_count,
    uint32_t stride,
    const uint8_t* __restrict__ faed_symbols,
    const uint8_t* __restrict__ base_cell_symbols,
    const uint8_t* __restrict__ free_positions,
    const uint8_t* __restrict__ free_symbols,
    const float* __restrict__ quadgrams,
    BlockBest* __restrict__ block_bests
) {
    uint64_t tid = (uint64_t)blockIdx.x * blockDim.x + threadIdx.x;
    uint64_t offset = tid * (uint64_t)stride;
    float best_score = -INFINITY;
    uint64_t best_rank = 0;
    uint32_t valid = 0;

    for (uint32_t step = 0; step < stride; ++step) {
        uint64_t relative = offset + step;
        if (relative >= candidate_count) break;
        uint64_t rank = start_rank + relative;
        float score = score_rank(
            rank, faed_symbols, base_cell_symbols, free_positions, free_symbols, quadgrams
        );
        if (!valid || score > best_score || (score == best_score && rank < best_rank)) {
            best_score = score;
            best_rank = rank;
            valid = 1;
        }
    }

    __shared__ float shared_scores[BLOCK_SIZE];
    __shared__ uint64_t shared_ranks[BLOCK_SIZE];
    __shared__ uint32_t shared_valid[BLOCK_SIZE];
    shared_scores[threadIdx.x] = best_score;
    shared_ranks[threadIdx.x] = best_rank;
    shared_valid[threadIdx.x] = valid;
    __syncthreads();

    for (uint32_t width = blockDim.x / 2; width > 0; width >>= 1) {
        if (threadIdx.x < width) {
            uint32_t other = threadIdx.x + width;
            uint32_t other_valid = shared_valid[other];
            if (other_valid &&
                (!shared_valid[threadIdx.x] ||
                 shared_scores[other] > shared_scores[threadIdx.x] ||
                 (shared_scores[other] == shared_scores[threadIdx.x] &&
                  shared_ranks[other] < shared_ranks[threadIdx.x]))) {
                shared_scores[threadIdx.x] = shared_scores[other];
                shared_ranks[threadIdx.x] = shared_ranks[other];
                shared_valid[threadIdx.x] = 1;
            }
        }
        __syncthreads();
    }

    if (threadIdx.x == 0) {
        block_bests[blockIdx.x].rank = shared_ranks[0];
        block_bests[blockIdx.x].score = shared_scores[0];
        block_bests[blockIdx.x].valid = shared_valid[0];
    }
}
