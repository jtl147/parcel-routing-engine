# Author: Jedi Lee
# Student ID: 012594297

from typing import Any, Iterable, List, Optional, Tuple

class ChainingHashTable:
    """
    Chaining hash table (separate chaining with linked-list buckets).
    Average-case time: O(1) for insert/search/remove.
    Worst-case time: O(n) within a single bucket under heavy collisions.
    """

    __slots__ = ("_buckets", "_size", "_max_load_factor")

    def __init__(self, init_capacity: int = 64, max_load_factor: float = 0.75) -> None:
        if init_capacity < 1:
            raise ValueError("init_capacity must be >= 1")
        self._buckets: List[List[Tuple[Any, Any]]] = [[] for _ in range(init_capacity)]
        self._size: int = 0
        self._max_load_factor: float = max_load_factor

    def insert(self, key: Any, value: Any) -> None:
        """Insert or update a (key, value) pair."""
        idx = self._index(key)
        bucket = self._buckets[idx]

        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return

        bucket.append((key, value))
        self._size += 1
        if self.load_factor() > self._max_load_factor:
            self._resize(len(self._buckets) * 2)

    def search(self, key: Any) -> Optional[Any]:
        """Return value for key, or None if absent."""
        bucket = self._buckets[self._index(key)]
        for k, v in bucket:
            if k == key:
                return v
        return None

    def remove(self, key: Any) -> bool:
        """Remove key from table. Returns True if removed, False if not found."""
        idx = self._index(key)
        bucket = self._buckets[idx]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket.pop(i)
                self._size -= 1
                return True
        return False

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: Any) -> bool:
        return self.search(key) is not None

    def items(self) -> Iterable[Tuple[Any, Any]]:
        """Iterate all (key, value) pairs."""
        for bucket in self._buckets:
            for kv in bucket:
                yield kv

    def capacity(self) -> int:
        return len(self._buckets)

    def load_factor(self) -> float:
        return self._size / len(self._buckets)

    def _index(self, key: Any) -> int:
        return hash(key) % len(self._buckets)

    def _resize(self, new_capacity: int) -> None:
        """Rehash into a larger bucket array."""
        old_buckets = self._buckets
        self._buckets = [[] for _ in range(new_capacity)]
        self._size = 0
        for bucket in old_buckets:
            for k, v in bucket:
                idx = hash(k) % new_capacity
                self._buckets[idx].append((k, v))
                self._size += 1

if __name__ == "__main__":
    ht = ChainingHashTable()
    ht.insert(1, "Package 1")
    ht.insert(2, "Package 2")
    print("Search 1:", ht.search(1))
    print("Search 2:", ht.search(2))
    ht.remove(1)
    print("After remove, search 1:", ht.search(1))
