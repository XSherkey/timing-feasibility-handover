"""Cross-process concurrency limiter for LLM calls.

Running eight campaign processes in parallel means eight concurrent requests to
the same endpoint, which the provider throttles or holds open until the client
timeout expires.  A slot file-directory semaphore caps the number of *in-flight
API calls* while all processes keep computing in parallel.

Stale slots (a crashed process) are reclaimed after ``stale_s`` seconds, so a
killed campaign cannot deadlock the next one.
"""
from __future__ import annotations

import contextlib
import os
import tempfile
import time
from pathlib import Path


class FileSemaphore:
    def __init__(self, name: str = "almond_llm", slots: int = 3, timeout_s: float = 600.0,
                 stale_s: float = 60.0, root: str | Path | None = None):
        self.dir = Path(root or tempfile.gettempdir()) / f"{name}_sem"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.slots = max(1, int(slots))
        self.timeout_s = timeout_s
        self.stale_s = stale_s

    def _reap_stale(self) -> None:
        now = time.time()
        for p in self.dir.glob("slot*"):
            try:
                if now - p.stat().st_mtime > self.stale_s:
                    p.unlink()
            except (FileNotFoundError, PermissionError):
                pass

    @contextlib.contextmanager
    def acquire(self):
        t0 = time.time()
        held: Path | None = None
        while True:
            for i in range(self.slots):
                p = self.dir / f"slot{i}"
                try:
                    fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.close(fd)
                    held = p
                    break
                except FileExistsError:
                    continue
            if held is not None:
                break
            if time.time() - t0 > self.timeout_s:
                # give up waiting and run anyway (correctness over throttling)
                break
            self._reap_stale()
            time.sleep(0.15 + 0.25 * os.urandom(1)[0] / 255.0)
        try:
            yield
        finally:
            if held is not None:
                try:
                    held.unlink()
                except FileNotFoundError:
                    pass
