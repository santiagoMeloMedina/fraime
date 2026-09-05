import contextlib
import io
import logging
import warnings

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)


@contextlib.contextmanager
def suppress_stdout():
    """For third-party model-loading code with a hardcoded print() and no logging/
    warnings hook to disable through (e.g. resemble-perth's watermarker checkpoint
    loader) — redirects stdout away for the duration of the wrapped call only."""
    with contextlib.redirect_stdout(io.StringIO()):
        yield


def suppress_library_noise() -> None:
    """Silences model-download progress bars and remaining per-library progress-bar
    output from huggingface_hub/diffusers/transformers and chatterbox's own sampling
    loop, so the only things printed during generation are our own log_event calls.
    The warnings/logging suppression above runs at import time rather than in here,
    since some library warnings (e.g. transformers' lazy image-processor fallback
    notice) fire as a side effect of merely importing a module, before any function
    in this file would get a chance to run — this module must be imported first,
    ahead of torch/diffusers/transformers, for that suppression to actually land
    before those imports trigger it. tqdm itself is patched directly because
    chatterbox's sampling loop instantiates it raw, with no library-level toggle to
    disable through.
    """
    import diffusers.utils.logging as diffusers_logging
    import huggingface_hub.utils as hf_hub_utils
    import transformers.utils.logging as transformers_logging
    from tqdm import tqdm

    hf_hub_utils.disable_progress_bars()
    diffusers_logging.disable_progress_bar()
    diffusers_logging.set_verbosity_error()
    transformers_logging.disable_progress_bar()
    transformers_logging.set_verbosity_error()

    original_init = tqdm.__init__

    def _silent_init(self, *args, **kwargs):
        kwargs["disable"] = True
        original_init(self, *args, **kwargs)

    tqdm.__init__ = _silent_init
