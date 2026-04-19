"""
Device selection utilities for PyTorch models.

Handles device selection across different hardware:
- Apple Silicon (M1/M2/M3) via MPS
- NVIDIA GPUs via CUDA
- CPU fallback
"""

import torch
import logging

logger = logging.getLogger(__name__)


def select_device(use_gpu: bool = True, verbose: bool = True) -> torch.device:
    """
    Select the best available compute device for PyTorch.

    Priority order:
    1. MPS (Metal Performance Shaders) - Apple Silicon M1/M2/M3 Macs
    2. CUDA - NVIDIA GPUs
    3. CPU - Universal fallback

    Args:
        use_gpu: Whether to attempt GPU usage (default: True)
        verbose: Log device selection info (default: True)

    Returns:
        torch.device instance ready for use

    Examples:
        >>> device = select_device()
        >>> tensor = torch.randn(100, 100, device=device)

        >>> # Force CPU
        >>> device = select_device(use_gpu=False)
    """
    if not use_gpu:
        if verbose:
            logger.info("GPU disabled by user, using CPU")
        return torch.device("cpu")

    # Try Apple Silicon GPU first (common on M1/M2/M3 Macs)
    if torch.backends.mps.is_available():
        try:
            # Verify MPS actually works with a small test
            # (sometimes is_available() returns True but MPS is broken)
            test_tensor = torch.zeros(1, device="mps")
            del test_tensor  # Clean up

            if verbose:
                logger.info("Using Apple Silicon GPU (MPS)")
            return torch.device("mps")

        except Exception as e:
            if verbose:
                logger.warning(
                    f"MPS reported as available but failed test: {e}. "
                    "Falling back to next option."
                )

    # Try NVIDIA GPU (common on Linux/Windows workstations)
    if torch.cuda.is_available():
        device = torch.device("cuda")
        if verbose:
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"Using NVIDIA GPU (CUDA): {gpu_name}")
        return device

    # Fallback to CPU
    if verbose:
        logger.info("No GPU available, using CPU")
    return torch.device("cpu")


def get_device_info() -> dict:
    """
    Get detailed information about available compute devices.

    Returns:
        Dictionary with device information:
        {
            "cpu": True,
            "cuda": {
                "available": bool,
                "device_count": int,
                "device_name": str (if available)
            },
            "mps": {
                "available": bool,
                "built": bool
            },
            "selected": str  # The device that would be selected
        }

    Example:
        >>> info = get_device_info()
        >>> print(f"Running on: {info['selected']}")
        >>> if info['cuda']['available']:
        ...     print(f"GPU: {info['cuda']['device_name']}")
    """
    info = {
        "cpu": True,
        "cuda": {
            "available": torch.cuda.is_available(),
            "device_count": 0,
            "device_name": None
        },
        "mps": {
            "available": torch.backends.mps.is_available(),
            "built": torch.backends.mps.is_built()
        }
    }

    # Get CUDA details
    if torch.cuda.is_available():
        info["cuda"]["device_count"] = torch.cuda.device_count()
        info["cuda"]["device_name"] = torch.cuda.get_device_name(0)

    # Determine which device would be selected
    device = select_device(use_gpu=True, verbose=False)
    info["selected"] = str(device)

    return info


def benchmark_device(device: torch.device, size: int = 10_000) -> float:
    """
    Benchmark matrix multiplication on a device.

    Useful for comparing CPU vs GPU performance.

    Args:
        device: Device to benchmark
        size: Matrix size (default: 10000x10000)

    Returns:
        Time in milliseconds for 100 matrix multiplications

    Example:
        >>> cpu_time = benchmark_device(torch.device("cpu"))
        >>> gpu_time = benchmark_device(torch.device("mps"))
        >>> speedup = cpu_time / gpu_time
        >>> print(f"GPU is {speedup:.1f}x faster")
    """
    import time

    # Create test matrices
    a = torch.randn(size, size, device=device)
    b = torch.randn(size, size, device=device)

    # Warmup
    for _ in range(10):
        _ = torch.matmul(a, b)

    # Synchronize (important for accurate timing)
    if device.type == "cuda":
        torch.cuda.synchronize()
    elif device.type == "mps":
        torch.mps.synchronize()

    # Benchmark
    start = time.time()
    for _ in range(100):
        _ = torch.matmul(a, b)

    # Synchronize again
    if device.type == "cuda":
        torch.cuda.synchronize()
    elif device.type == "mps":
        torch.mps.synchronize()

    elapsed = (time.time() - start) * 1000  # Convert to ms

    return elapsed


if __name__ == "__main__":
    """Run device diagnostics."""
    import json

    print("=" * 60)
    print("PyTorch Device Diagnostics")
    print("=" * 60)

    size = 2_000

    # Get device info
    info = get_device_info()
    print("\nDevice Information:")
    print(json.dumps(info, indent=2))

    print(f"\n✓ Selected device: {info['selected']}")

    # Benchmark if GPU available
    device = select_device(use_gpu=True, verbose=True)

    print(f"\nBenchmarking {device}...")
    time_ms = benchmark_device(device, size=size)
    print(f"  {size}x{size} matmul x100: {time_ms:.2f}ms")

    # Compare with CPU if we're on GPU
    if device.type != "cpu":
        print("\nBenchmarking CPU for comparison...")
        cpu_time = benchmark_device(torch.device("cpu"), size=size)
        print(f"  {size}x{size} matmul x100: {cpu_time:.2f}ms")

        speedup = cpu_time / time_ms
        print(f"\n⚡ GPU is {speedup:.1f}x faster than CPU")
