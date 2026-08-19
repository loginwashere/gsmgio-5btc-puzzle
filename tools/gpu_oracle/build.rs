use std::env;
use std::path::PathBuf;
use std::process::Command;

fn main() {
    // No-op unless building with --features cuda (mirrors key-seeker's build.rs).
    if env::var("CARGO_FEATURE_CUDA").is_err() {
        return;
    }

    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());

    println!("cargo:rerun-if-env-changed=GO_CUDA_ARCH");

    // RTX 5070 (Blackwell) reports compute capability 12.0 via
    // `nvidia-smi --query-gpu=compute_cap` on the dev machine this was built for.
    // Override with GO_CUDA_ARCH for a different card.
    let cuda_arch = env::var("GO_CUDA_ARCH").unwrap_or_else(|_| "sm_120".into());

    compile_kernel("kernels/aes_kdf_oracle.cu", &out_dir.join("aes_kdf_oracle.ptx"), &cuda_arch);
    println!(
        "cargo:rustc-env=AES_KDF_ORACLE_PTX_PATH={}",
        out_dir.join("aes_kdf_oracle.ptx").display()
    );

    // Bloom/API key-shape stream-cipher check (Phase 325) -- see
    // stream_key_check.rs and kernels/secp256k1_brainwallet.cu's own header
    // comment for why this is a copied excerpt of ../../../key-seeker's
    // kernels/secp256k1.cu rather than a from-scratch port.
    compile_kernel(
        "kernels/secp256k1_brainwallet.cu",
        &out_dir.join("secp256k1_brainwallet.ptx"),
        &cuda_arch,
    );
    println!(
        "cargo:rustc-env=SECP256K1_BRAINWALLET_PTX_PATH={}",
        out_dir.join("secp256k1_brainwallet.ptx").display()
    );
}

fn compile_kernel(kernel_src: &str, ptx_out: &PathBuf, cuda_arch: &str) {
    println!("cargo:rerun-if-changed={kernel_src}");

    let args: Vec<String> = vec![
        "--ptx".into(),
        format!("--gpu-architecture={cuda_arch}"),
        "-O3".into(),
        "--use_fast_math".into(),
        "-o".into(),
        ptx_out.to_str().unwrap().to_string(),
        kernel_src.into(),
    ];

    let status = Command::new("nvcc")
        .args(&args)
        .status()
        .expect("nvcc not found -- install CUDA toolkit or build via Dockerfile.cuda");

    assert!(status.success(), "nvcc failed to compile {kernel_src}");
}
