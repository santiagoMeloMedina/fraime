from collections.abc import Callable

from tqdm.auto import tqdm


def make_progress_reporter(on_update: Callable[[float], None]) -> type[tqdm]:
    class ProgressReporter(tqdm):
        def update(self, n=1):
            super().update(n)
            if self.total:
                on_update(self.n / self.total * 100)

    return ProgressReporter


def report(title: str, percent: float) -> None:
    print(f"${title} progress: {percent:.1f}%")
