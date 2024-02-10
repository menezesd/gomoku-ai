import heapq
import itertools

class myPriorityQueue:
    """
    Class for a priority queue implemented with a max heap.
    """

    def __init__(self):
        self.pq = []                         # list of entries arranged in a heap
        self.entry_finder = {}               # mapping of tasks to entries
        self.REMOVED = '<removed-task>'      # placeholder for a removed task
        self.counter = itertools.count()     # unique sequence count

    def add_task(self, task, priority=0):
        """
        Add a new task or update the priority of an existing task.
        
        Args:
            task: The task to be added or updated.
            priority: The priority of the task.
        """
        pq = self.pq
        entry_finder = self.entry_finder
        counter = self.counter
        
        if task in entry_finder:
            self.remove_task(task)
        count = next(counter)
        entry = [-priority, count, task]
        entry_finder[task] = entry
        heapq.heappush(pq, entry)

    def remove_task(self, task):
        """
        Mark an existing task as REMOVED. Raise KeyError if not found.
        
        Args:
            task: The task to be removed.
        """
        entry_finder = self.entry_finder
        entry = entry_finder.pop(task)
        entry[-1] = self.REMOVED

    def pop_task(self):
        """
        Remove and return the lowest priority task. Raise KeyError if empty.
        
        Returns:
            The lowest priority task.
        """
        pq = self.pq
        entry_finder = self.entry_finder
        while pq:
            priority, count, task = heapq.heappop(pq)
            if task is not self.REMOVED:
                del entry_finder[task]
                return task
        raise KeyError('pop from an empty priority queue')

    def increase_priority(self, task, n):
        """
        Increase the priority of a task by n.
        
        Args:
            task: The task whose priority needs to be increased.
            n: The amount by which the priority should be increased.
        """
        entry_finder = self.entry_finder
        if task not in entry_finder:
            return
        priority, count, task = entry_finder[task]
        self.add_task(task, n - priority)  # funny because max heap

    def sorted_list(self):
        """
        Return a sorted list of tasks.
        
        Returns:
            A list of tasks sorted by priority.
        """
        pq = self.pq
        REMOVED = self.REMOVED
        l = heapq.nsmallest(len(pq), pq)
        ret = []
        for entry in l:
            if (add := entry[2]) is not REMOVED:
                ret.append(add)
        return ret

    def truncated_sorted_list(self, t):
        """
        Return a sorted list of tasks up to a given priority.
        
        Args:
            t: The priority threshold.
        
        Returns:
            A list of tasks sorted by priority up to the given threshold.
        """
        pq = self.pq
        REMOVED = self.REMOVED
        l = heapq.nsmallest(len(pq), pq)
        ret = []
        for entry in l:
            add = entry[2]
            pri = entry[0]
            if pri >= -t:
                return ret
            if add is not REMOVED:
                ret.append(add)
        return ret
