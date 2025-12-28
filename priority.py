from __future__ import annotations
import heapq
import itertools
from typing import Any, Iterator

# Sentinel value for removed entries
_REMOVED = "<removed-task>"


class myPriorityQueue:
    """
    Priority queue implemented with a max heap.

    Uses Python's heapq (min-heap) with negated priorities to achieve
    max-heap behavior. Supports efficient priority updates and removals.
    """

    def __init__(self) -> None:
        self._pq: list[list[Any]] = []  # Heap of [priority, count, task]
        self._entry_finder: dict[Any, list[Any]] = {}  # task -> entry mapping
        self._counter: Iterator[int] = itertools.count()  # Unique sequence count

    def add_task(self, task: Any, priority: float = 0) -> None:
        """
        Add a new task or update the priority of an existing task.

        Args:
            task: The task to be added or updated
            priority: The priority of the task (higher = more important)
        """
        if task in self._entry_finder:
            self.remove_task(task)

        count = next(self._counter)
        entry: list[Any] = [-priority, count, task]
        self._entry_finder[task] = entry
        heapq.heappush(self._pq, entry)

    def remove_task(self, task: Any) -> None:
        """
        Mark an existing task as removed.

        Args:
            task: The task to be removed

        Raises:
            KeyError: If task is not found
        """
        entry = self._entry_finder.pop(task)
        entry[-1] = _REMOVED

    def pop_task(self) -> Any:
        """
        Remove and return the highest priority task.

        Returns:
            The highest priority task

        Raises:
            KeyError: If queue is empty
        """
        while self._pq:
            priority, count, task = heapq.heappop(self._pq)
            if task is not _REMOVED:
                del self._entry_finder[task]
                return task
        raise KeyError("pop from an empty priority queue")

    def increase_priority(self, task: Any, n: float) -> None:
        """
        Increase the priority of a task by n.

        Args:
            task: The task whose priority needs to be increased
            n: The amount by which to increase priority
        """
        if task not in self._entry_finder:
            return
        priority, count, task = self._entry_finder[task]
        # Priority is stored negated, so we add to increase
        self.add_task(task, n - priority)

    def sorted_list(self) -> list[Any]:
        """
        Return a sorted list of all tasks (highest priority first).

        Returns:
            List of tasks sorted by priority
        """
        items = heapq.nsmallest(len(self._pq), self._pq)
        return [entry[2] for entry in items if entry[2] is not _REMOVED]

    def truncated_sorted_list(self, threshold: float) -> list[Any]:
        """
        Return tasks with priority above the given threshold.

        Args:
            threshold: Minimum priority threshold

        Returns:
            List of tasks with priority above threshold
        """
        items = heapq.nsmallest(len(self._pq), self._pq)
        result: list[Any] = []
        for entry in items:
            task = entry[2]
            priority = entry[0]
            # Priority is stored negated
            if priority >= -threshold:
                return result
            if task is not _REMOVED:
                result.append(task)
        return result

    def __len__(self) -> int:
        """Return number of tasks in the queue."""
        return len(self._entry_finder)

    def __bool__(self) -> bool:
        """Return True if queue is not empty."""
        return bool(self._entry_finder)
