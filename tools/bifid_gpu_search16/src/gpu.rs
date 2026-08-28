use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use cudarc::driver::safe::{CudaContext, CudaModule, CudaSlice, CudaStream};
use cudarc::driver::PushKernelArg;
use cudarc::nvrtc::Ptx;

use crate::cpu::{symbol_index, BASE_SQUARE, FREE_POSITIONS, FREE_SYMBOLS};

pub const BLOCK_SIZE: u32 = 256;

#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct BlockBest {
    pub rank: u64,
    pub score: f32,
    pub valid: u32,
}

unsafe impl cudarc::driver::DeviceRepr for BlockBest {}
unsafe impl cudarc::driver::ValidAsZeroBits for BlockBest {}

struct FixedData {
    faed_symbols: CudaSlice<u8>,
    base_cell_symbols: CudaSlice<u8>,
    free_positions: CudaSlice<u8>,
    free_symbols: CudaSlice<u8>,
    quadgrams: CudaSlice<f32>,
}

pub struct GpuSearcher {
    ctx: Arc<CudaContext>,
    module: Arc<CudaModule>,
    streams: [Arc<CudaStream>; 2],
    fixed: FixedData,
}

impl GpuSearcher {
    pub fn new(faed_symbols: &[u8], quadgrams: &[f32]) -> Result<Self, Box<dyn std::error::Error>> {
        if faed_symbols.len() != 570 {
            return Err(format!(
                "GPU contract requires 570 FAED symbols, got {}",
                faed_symbols.len()
            )
            .into());
        }
        if quadgrams.len() != 390_625 {
            return Err(format!(
                "GPU contract requires 390625 quadgrams, got {}",
                quadgrams.len()
            )
            .into());
        }
        let ctx = CudaContext::new(0)?;
        let ptx_bytes = include_bytes!(env!("BIFID_CUDA_PTX_PATH"));
        let module = ctx.load_module(Ptx::from_src(std::str::from_utf8(ptx_bytes)?))?;
        let stream0 = ctx.new_stream()?;
        let stream1 = ctx.new_stream()?;

        let base_cell_symbols: Vec<u8> = BASE_SQUARE
            .iter()
            .map(|&ch| symbol_index(ch).expect("base square symbol missing"))
            .collect();
        let free_symbols: Vec<u8> = FREE_SYMBOLS
            .iter()
            .map(|&ch| symbol_index(ch).expect("free symbol missing"))
            .collect();
        let faed_symbol_indices: Vec<u8> = faed_symbols
            .iter()
            .map(|&ch| symbol_index(ch).expect("FAED symbol missing"))
            .collect();
        let fixed = FixedData {
            faed_symbols: stream0.clone_htod(&faed_symbol_indices)?,
            base_cell_symbols: stream0.clone_htod(&base_cell_symbols)?,
            free_positions: stream0.clone_htod(&FREE_POSITIONS)?,
            free_symbols: stream0.clone_htod(&free_symbols)?,
            quadgrams: stream0.clone_htod(quadgrams)?,
        };
        stream0.synchronize()?;

        Ok(Self {
            ctx,
            module,
            streams: [stream0, stream1],
            fixed,
        })
    }

    pub fn device_name(&self) -> Result<String, Box<dyn std::error::Error>> {
        Ok(self.ctx.name()?)
    }

    pub fn scan<F>(
        &self,
        start: u64,
        end_exclusive: u64,
        grid_size: u32,
        stride: u32,
        interrupted: &AtomicBool,
        mut on_batch: F,
    ) -> Result<u64, Box<dyn std::error::Error>>
    where
        F: FnMut(u64, u64, &[BlockBest]) -> Result<(), Box<dyn std::error::Error>>,
    {
        if start > end_exclusive {
            return Err("start exceeds end-exclusive".into());
        }
        if grid_size == 0 || stride == 0 {
            return Err("grid-size and stride must both be positive".into());
        }
        let batch_capacity = grid_size as u64 * BLOCK_SIZE as u64 * stride as u64;
        let function = self.module.load_function("bifid_crib_block_best")?;
        let config = cudarc::driver::LaunchConfig {
            grid_dim: (grid_size, 1, 1),
            block_dim: (BLOCK_SIZE, 1, 1),
            shared_mem_bytes: 0,
        };
        let mut outputs: [CudaSlice<BlockBest>; 2] = [
            self.streams[0].alloc_zeros(grid_size as usize)?,
            self.streams[1].alloc_zeros(grid_size as usize)?,
        ];
        let mut metadata: [Option<(u64, u64)>; 2] = [None, None];
        let mut next = start;
        let mut launches = 0usize;
        let mut completed = start;

        while next < end_exclusive {
            if interrupted.load(Ordering::SeqCst) {
                break;
            }
            let current = launches % 2;
            let count = (end_exclusive - next).min(batch_capacity);
            unsafe {
                self.streams[current]
                    .launch_builder(&function)
                    .arg(&next)
                    .arg(&count)
                    .arg(&stride)
                    .arg(&self.fixed.faed_symbols)
                    .arg(&self.fixed.base_cell_symbols)
                    .arg(&self.fixed.free_positions)
                    .arg(&self.fixed.free_symbols)
                    .arg(&self.fixed.quadgrams)
                    .arg(&mut outputs[current])
                    .launch(config)?;
            }
            metadata[current] = Some((next, count));
            next += count;

            if launches > 0 {
                let previous = 1 - current;
                if let Some((batch_start, batch_count)) = metadata[previous].take() {
                    self.streams[previous].synchronize()?;
                    let host = self.streams[previous].clone_dtoh(&outputs[previous])?;
                    on_batch(batch_start, batch_count, &host)?;
                    completed = batch_start + batch_count;
                }
            }
            launches += 1;
        }

        for index in 0..2 {
            if let Some((batch_start, batch_count)) = metadata[index].take() {
                self.streams[index].synchronize()?;
                let host = self.streams[index].clone_dtoh(&outputs[index])?;
                on_batch(batch_start, batch_count, &host)?;
                completed = completed.max(batch_start + batch_count);
            }
        }
        Ok(completed)
    }

    pub fn score_one(&self, rank: u64) -> Result<BlockBest, Box<dyn std::error::Error>> {
        let interrupted = AtomicBool::new(false);
        let mut result = None;
        self.scan(
            rank,
            rank + 1,
            1,
            1,
            &interrupted,
            |_start, _count, rows| {
                result = rows.iter().copied().find(|row| row.valid != 0);
                Ok(())
            },
        )?;
        result.ok_or_else(|| "GPU returned no result for one-rank probe".into())
    }
}
