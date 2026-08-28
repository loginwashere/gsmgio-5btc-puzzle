use std::env;
use std::path::PathBuf;
use std::process::Command;

fn main() {
    if env::var("CARGO_FEATURE_CUDA").is_err() {
        return;
    }

    let kernel = "kernels/bifid_crib_search.cu";
    let out =
        PathBuf::from(env::var("OUT_DIR").expect("OUT_DIR missing")).join("bifid_crib_search.ptx");
    let arch = env::var("BIFID_CUDA_ARCH").unwrap_or_else(|_| "sm_120".into());

    println!("cargo:rerun-if-changed={kernel}");
    println!("cargo:rerun-if-env-changed=BIFID_CUDA_ARCH");

    let status = Command::new("nvcc")
        .args([
            "--ptx",
            &format!("--gpu-architecture={arch}"),
            "-O3",
            "--use_fast_math",
            "-lineinfo",
            "-o",
            out.to_str().expect("non-UTF8 PTX path"),
            kernel,
        ])
        .status()
        .expect("nvcc not found; use Dockerfile.cuda or install CUDA 13");
    assert!(status.success(), "nvcc failed to compile {kernel}");
    println!("cargo:rustc-env=BIFID_CUDA_PTX_PATH={}", out.display());
    println!("cargo:rustc-env=BIFID_CUDA_ARCH={arch}");
}
