#include <cuda_runtime.h>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

// Width-30 port of phase484q_coarse_board_server.cu: same per-fragment board
// anneal, geometry swapped for the complementary 30-column orientation (30
// candidate columns, 19 raw-symbol rows per column instead of 19/30).  The
// token index convention (7+symbol*9+next, no escape-pair relabeling) is
// intentionally identical to the width-19 kernel so an annealed board here
// composes correctly with phase484y_width30_extend_board_server.cu, which
// uses the same unconverted convention.  See phase484y_width30_board_score_
// server.cu for the different, absolute-alphabet convention needed only when
// scoring against the true planted board directly (the ceiling-map oracle).
constexpr int WIDTH = 30, ROWS = 19, SLOTS = 25;
constexpr int QUAD_SIZE = SLOTS * SLOTS * SLOTS * SLOTS;
constexpr uint64_t PCG_MULT = 6364136223846793005ULL;
#define CUDA_OK(call) do { cudaError_t e=(call); if(e!=cudaSuccess){std::fprintf(stderr,"%s\n",cudaGetErrorString(e));std::exit(2);} } while(0)

struct Pcg32 {
  uint64_t state, inc;
  __device__ uint32_t next() { uint64_t old=state; state=old*PCG_MULT+inc; uint32_t x=uint32_t(((old>>18)^old)>>27), r=uint32_t(old>>59); return (x>>r)|(x<<((-r)&31)); }
  __device__ void initialise(uint64_t s) { state=0; inc=(0x484AULL<<1)|1; next(); state+=s; next(); }
  __device__ uint32_t below(uint32_t n) { return next()%n; }
  __device__ double uniform() { return double(next())/4294967296.0; }
};
__device__ uint64_t derive_seed(uint64_t v,uint64_t a,uint64_t b){v=(v^a)*0x9E3779B97F4A7C15ULL;v^=v>>29;v=(v^b)*0x9E3779B97F4A7C15ULL;v^=v>>29;return v;}
__device__ uint64_t path_seed(uint64_t seed_base,const unsigned char *path,int depth){uint64_t value=derive_seed(seed_base,uint64_t(depth),0);for(int i=0;i<depth;++i)value=derive_seed(value,uint64_t(path[i])+1,uint64_t(i)+1);return value;}
__device__ int qkey(unsigned char a,unsigned char b,unsigned char c,unsigned char d){return ((int(a)*SLOTS+int(b))*SLOTS+int(c))*SLOTS+int(d);}

__global__ void anneal_kernel(const unsigned char *blocks,const unsigned char *paths,int count,int depth,const double *quad,uint64_t seed_base,int iterations,double t0,double t1,double *best_scores,unsigned char *best_boards,int *window_counts){
  int index=blockIdx.x*blockDim.x+threadIdx.x; if(index>=count)return;
  const unsigned char *path=paths+size_t(index)*depth;
  unsigned char tokens[ROWS*WIDTH],lengths[ROWS]; int windows=0;
  for(int row=0;row<ROWS;++row){int length=0;for(int j=0;j<depth;){int symbol=blocks[int(path[j])*ROWS+row];if(symbol<2){if(j+1==depth)break;int next=blocks[int(path[j+1])*ROWS+row];tokens[row*WIDTH+length++]=7+symbol*9+next;j+=2;}else{tokens[row*WIDTH+length++]=symbol-2;++j;}}lengths[row]=static_cast<unsigned char>(length);if(length>=4)windows+=length-3;}
  Pcg32 rng;rng.initialise(path_seed(seed_base,path,depth));unsigned char board[SLOTS],best_board[SLOTS];for(int i=0;i<SLOTS;++i)board[i]=static_cast<unsigned char>(i);for(int i=SLOTS-1;i>0;--i){int other=int(rng.below(uint32_t(i+1)));unsigned char x=board[i];board[i]=board[other];board[other]=x;}
  double current=0.0;for(int row=0;row<ROWS;++row){const unsigned char *r=tokens+row*WIDTH;for(int j=3;j<lengths[row];++j)current+=quad[qkey(board[r[j-3]],board[r[j-2]],board[r[j-1]],board[r[j]])];}
  double best=current;for(int i=0;i<SLOTS;++i)best_board[i]=board[i];double cooling=iterations>0?pow(t1/t0,1.0/double(iterations)):1.0,temperature=t0;
  for(int step=0;step<iterations;++step){int left=int(rng.below(SLOTS)),right=int(rng.below(SLOTS));if(left!=right){double delta=0.0;for(int row=0;row<ROWS;++row){const unsigned char *r=tokens+row*WIDTH;for(int j=3;j<lengths[row];++j){unsigned char s0=r[j-3],s1=r[j-2],s2=r[j-1],s3=r[j];if(s0==left||s0==right||s1==left||s1==right||s2==left||s2==right||s3==left||s3==right){unsigned char a0=board[s0],a1=board[s1],a2=board[s2],a3=board[s3];unsigned char b0=s0==left?board[right]:(s0==right?board[left]:a0),b1=s1==left?board[right]:(s1==right?board[left]:a1),b2=s2==left?board[right]:(s2==right?board[left]:a2),b3=s3==left?board[right]:(s3==right?board[left]:a3);delta+=quad[qkey(b0,b1,b2,b3)]-quad[qkey(a0,a1,a2,a3)];}}}if(delta>=0.0||rng.uniform()<exp(delta/temperature)){unsigned char x=board[left];board[left]=board[right];board[right]=x;current+=delta;if(current>best){best=current;for(int i=0;i<SLOTS;++i)best_board[i]=board[i];}}}temperature*=cooling;}
  best_scores[index]=windows?best/double(windows):-1.0e9;window_counts[index]=windows;for(int i=0;i<SLOTS;++i)best_boards[size_t(index)*SLOTS+i]=best_board[i];
}
template<typename T>bool read_exact(T*t,size_t n){return std::fread(t,sizeof(T),n,stdin)==n;}
int main(){char magic[8];if(!read_exact(magic,size_t(8))||std::memcmp(magic,"P484YQ1\0",8))return 3;unsigned char blocks[WIDTH*ROWS];std::vector<double>quad(QUAD_SIZE);if(!read_exact(blocks,size_t(WIDTH*ROWS))||!read_exact(quad.data(),size_t(QUAD_SIZE)))return 3;uint32_t header[3];uint64_t seed;double temp[2];if(!read_exact(header,size_t(3))||!read_exact(&seed,size_t(1))||!read_exact(temp,size_t(2)))return 3;size_t count=header[0];int depth=int(header[1]),iterations=int(header[2]);if(!count||count>(1u<<20)||depth<4||depth>WIDTH||iterations<0||temp[0]<=0||temp[1]<=0)return 4;size_t path_bytes=count*size_t(depth);std::vector<unsigned char>paths(path_bytes),boards(count*SLOTS);std::vector<double>scores(count);std::vector<int>windows(count);if(!read_exact(paths.data(),path_bytes))return 3;unsigned char *db,*dp,*dbo;double *dq,*ds;int *dw;CUDA_OK(cudaMalloc(&db,sizeof(blocks)));CUDA_OK(cudaMalloc(&dp,path_bytes));CUDA_OK(cudaMalloc(&dq,sizeof(double)*QUAD_SIZE));CUDA_OK(cudaMalloc(&ds,sizeof(double)*count));CUDA_OK(cudaMalloc(&dbo,count*SLOTS));CUDA_OK(cudaMalloc(&dw,sizeof(int)*count));CUDA_OK(cudaMemcpy(db,blocks,sizeof(blocks),cudaMemcpyHostToDevice));CUDA_OK(cudaMemcpy(dp,paths.data(),path_bytes,cudaMemcpyHostToDevice));CUDA_OK(cudaMemcpy(dq,quad.data(),sizeof(double)*QUAD_SIZE,cudaMemcpyHostToDevice));anneal_kernel<<<(count+127)/128,128>>>(db,dp,int(count),depth,dq,seed,iterations,temp[0],temp[1],ds,dbo,dw);CUDA_OK(cudaGetLastError());CUDA_OK(cudaDeviceSynchronize());CUDA_OK(cudaMemcpy(scores.data(),ds,sizeof(double)*count,cudaMemcpyDeviceToHost));CUDA_OK(cudaMemcpy(boards.data(),dbo,count*SLOTS,cudaMemcpyDeviceToHost));CUDA_OK(cudaMemcpy(windows.data(),dw,sizeof(int)*count,cudaMemcpyDeviceToHost));if(std::fwrite(scores.data(),sizeof(double),count,stdout)!=count||std::fwrite(windows.data(),sizeof(int),count,stdout)!=count||std::fwrite(boards.data(),1,count*SLOTS,stdout)!=count*SLOTS)return 5;return 0;}
