import asyncio
from concurrent.futures import Future
from concurrent.futures import ProcessPoolExecutor as ProcessPoolExecutorBase
from multiprocessing import cpu_count
from typing import Any, Callable, Set, Tuple, TypeVar

from .compat import EventLoopMixin
from .counters import Statistic


T = TypeVar("T")
FuturesSet = Set[asyncio.Future]
_CreateFutureType = Tuple[
    Callable[[T], None],
    Callable[[T], None],
    asyncio.Future,
]


class ProcessPoolStatistic(Statistic):
    processes: int
    done: int
    error: int
    success: int
    submitted: int
    sum_time: float


class ProcessPoolExecutor(ProcessPoolExecutorBase, EventLoopMixin):
    DEFAULT_MAX_WORKERS = max((cpu_count(), 4))

    def __init__(self, max_workers: int = DEFAULT_MAX_WORKERS, **kwargs: Any):
        super().__init__(max_workers=max_workers, **kwargs)
        self._statistic = ProcessPoolStatistic()
        self._statistic.processes = max_workers

    def _statistic_callback(
        self, future: Future, execution_time: float,
    ) -> None:
        if future.exception():
            self._statistic.error += 1
        else:
            self._statistic.success += 1
        self._statistic.done += 1
        self._statistic.sum_time += execution_time

    def submit(self, *args: Any, **kwargs: Any) -> Future:
        """
        Submit blocking function to the pool
        """
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        future = super().submit(*args, **kwargs)
        self._statistic.submitted += 1
        future.add_done_callback(
            lambda f: self._statistic_callback(f, loop.time() - start_time),
        )
        return future

    def __del__(self) -> None:
        self.shutdown()
