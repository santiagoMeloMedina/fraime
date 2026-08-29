import platform
import shutil
import subprocess
from enum import Enum
from pathlib import Path

import torch
from pydantic import BaseModel, Field

from api.config import environment


class Accelerator(str, Enum):
    CUDA = "cuda"
    MPS = "mps"
    CPU = "cpu"


class HardwareInfo(BaseModel):
    accelerator: Accelerator
    device_name: str | None = Field(
        default=None, description="Human-readable accelerator/device name"
    )
    device_count: int = Field(default=0, ge=0, description="Number of accelerator devices found")
    vram_gb: float = Field(
        default=0.0,
        ge=0,
        description=(
            "Usable accelerator memory in GB. On MPS this is unified system memory "
            "(shared with the CPU) rather than dedicated VRAM; 0 on CPU-only machines."
        ),
    )
    system_ram_gb: float = Field(ge=0, description="Total physical system RAM in GB")
    disk_free_gb: float = Field(
        ge=0, description="Free space in GB on the filesystem holding the model cache directory"
    )
    disk_total_gb: float = Field(
        ge=0, description="Total size in GB of the filesystem holding the model cache directory"
    )


def detect_hardware() -> HardwareInfo:
    """Detect the local accelerator, system RAM, and disk space for the model cache."""
    system_ram_gb = _system_ram_gb()
    disk_free_gb, disk_total_gb = _disk_usage_gb(environment.generation.model_cache_dir)

    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        # Diffusers pipelines run on a single device with no built-in model-parallel
        # strategy, so the binding constraint is the smallest device, not the total.
        vram_gb = min(
            torch.cuda.get_device_properties(i).total_memory for i in range(device_count)
        ) / (1024**3)
        return HardwareInfo(
            accelerator=Accelerator.CUDA,
            device_name=torch.cuda.get_device_name(0),
            device_count=device_count,
            vram_gb=vram_gb,
            system_ram_gb=system_ram_gb,
            disk_free_gb=disk_free_gb,
            disk_total_gb=disk_total_gb,
        )

    if torch.backends.mps.is_available():
        return HardwareInfo(
            accelerator=Accelerator.MPS,
            device_name="Apple Silicon (unified memory)",
            device_count=1,
            vram_gb=system_ram_gb,
            system_ram_gb=system_ram_gb,
            disk_free_gb=disk_free_gb,
            disk_total_gb=disk_total_gb,
        )

    return HardwareInfo(
        accelerator=Accelerator.CPU,
        system_ram_gb=system_ram_gb,
        disk_free_gb=disk_free_gb,
        disk_total_gb=disk_total_gb,
    )


def _system_ram_gb() -> float:
    system = platform.system()

    if system == "Darwin":
        result = subprocess.run(
            ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, check=True
        )
        return int(result.stdout.strip()) / (1024**3)

    if system == "Linux":
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) / (1024**2)  # value is in kB
        raise RuntimeError("MemTotal not found in /proc/meminfo")

    if system == "Windows":
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        return status.ullTotalPhys / (1024**3)

    raise RuntimeError(f"Unsupported platform for system RAM detection: {system}")


def _disk_usage_gb(cache_dir: str | None) -> tuple[float, float]:
    """Return (free, total) GB for the filesystem holding `cache_dir` (or the home dir)."""
    target = Path(cache_dir) if cache_dir else Path.home()
    while not target.exists():
        target = target.parent
    usage = shutil.disk_usage(target)
    return usage.free / (1024**3), usage.total / (1024**3)
