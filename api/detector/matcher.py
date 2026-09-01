from dataclasses import dataclass
from typing import Any

from api.detector.catalog import load_catalog
from api.detector.hardware import HardwareInfo, detect_hardware
from api.generation.media_type import MediaType

# Ordered best-fidelity-first: "standard" precision is preferred whenever it fits;
# the others are fallbacks that trade fidelity/speed for a lower VRAM floor.
VRAM_FIELDS = [
    ("standard", "min_vram_gb"),
    ("quantized", "min_vram_gb_quantized"),
    ("optimized", "min_vram_gb_optimized"),
]

DEFAULT_CAPABILITIES_BY_MEDIA_TYPE = {
    MediaType.VIDEO: ["text-to-video"],
    MediaType.IMAGE: ["text-to-image"],
    MediaType.SOUND: ["text-to-speech"],
}

# Catalog VRAM figures are approximate (see models.json's own note) and real usage can
# run over them — e.g. the VAE decode step spikes above the steady-state denoising
# usage. This reserves headroom instead of matching right up to the stated floor.
SAFETY_MARGIN_RATIO = 0.15


class NoModelFitsError(RuntimeError):
    """Raised when no catalog model matches the required capabilities and/or hardware."""


@dataclass
class ModelMatch:
    model_key: str
    model_id: str
    variant: str | None
    hardware: HardwareInfo
    matched_vram_gb: float
    precision: str  # "standard" | "quantized" | "optimized"
    media_type: MediaType
    requested_video_type: str | None
    required_capabilities: list[str]
    capabilities: list[str]
    matched_by_preference: bool
    safety_margin_applied: bool
    notes: str | None


def select_best_model(
    video_type: str | None = None,
    capabilities: list[str] | None = None,
    hardware: HardwareInfo | None = None,
    safety_margin: bool = False,
    media_type: MediaType = MediaType.VIDEO,
) -> ModelMatch:
    """Detect local hardware (unless provided) and pick the best-fitting catalog model.

    Matches on exact figures rather than a coarse hardware/model tier: a model is a
    candidate if it belongs to `media_type`, has all the required capabilities, and
    has at least one of its VRAM figures (standard/quantized/optimized) fitting the
    detected VRAM. Among candidates tagged `preferred_for` this video_type, the one
    using the most VRAM while still fitting wins; if none of those fit, the same rule
    applies across all candidates.

    If `safety_margin` is set, matching is done against a reduced VRAM budget
    (`SAFETY_MARGIN_RATIO` reserved as headroom) instead of the full detected amount,
    to absorb the gap between the catalog's approximate figures and real usage spikes
    (e.g. VAE decode).
    """
    hardware = hardware or detect_hardware()
    catalog = load_catalog()
    match_vram_gb = hardware.vram_gb * (1 - SAFETY_MARGIN_RATIO) if safety_margin else hardware.vram_gb

    required = set(capabilities or [])
    if video_type is not None:
        mapping = catalog["video_type_capabilities"].get(video_type)
        if mapping is None:
            raise ValueError(f"Unknown video_type: {video_type!r}")
        required |= set(mapping["required"])
    if not required:
        required = set(DEFAULT_CAPABILITIES_BY_MEDIA_TYPE[media_type])

    capable = {
        key: model
        for key, model in catalog["models"].items()
        if model.get("media_type", MediaType.VIDEO.value) == media_type.value
        and required.issubset(model["capabilities"])
    }
    if not capable:
        raise NoModelFitsError(
            f"No {media_type.value} catalog model has all required capabilities: {sorted(required)}."
        )

    fits = {}
    for key, model in capable.items():
        fit = _best_fit(model, match_vram_gb)
        if fit is not None:
            fits[key] = fit

    if not fits:
        cheapest_requirement = min(
            (
                value
                for model in capable.values()
                for _, field in VRAM_FIELDS
                if (value := model.get(field)) is not None
            ),
            default=None,
        )
        detail = (
            f"cheapest capability-matching model needs {cheapest_requirement}GB"
            if cheapest_requirement is not None
            else "no capability-matching model has a confirmed VRAM figure"
        )
        budget_note = f" (with a {SAFETY_MARGIN_RATIO:.0%} safety margin applied)" if safety_margin else ""
        raise NoModelFitsError(
            f"Detected {hardware.vram_gb:.1f}GB on {hardware.accelerator.value}{budget_note}; {detail}."
        )

    preferred_keys = (
        {key for key in fits if video_type in capable[key].get("preferred_for", [])}
        if video_type is not None
        else set()
    )
    pool = preferred_keys or set(fits)

    key = max(pool, key=lambda k: fits[k][0])
    matched_vram_gb, precision = fits[key]
    model = capable[key]
    return ModelMatch(
        model_key=key,
        model_id=model["id"],
        variant=model.get("variant"),
        hardware=hardware,
        matched_vram_gb=matched_vram_gb,
        precision=precision,
        media_type=media_type,
        requested_video_type=video_type,
        required_capabilities=sorted(required),
        capabilities=model.get("capabilities", []),
        matched_by_preference=key in preferred_keys,
        safety_margin_applied=safety_margin,
        notes=model.get("notes"),
    )


def _best_fit(model: dict[str, Any], vram_gb: float) -> tuple[float, str] | None:
    for precision, field in VRAM_FIELDS:
        value = model.get(field)
        if value is not None and value <= vram_gb:
            return value, precision
    return None
