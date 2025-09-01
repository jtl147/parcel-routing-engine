# Author: Jedi Lee
# Student ID: 012594297

from typing import Any, Iterable, List, Optional, Tuple

class ChainingHashTable:
    """
    - Separate-chaining hash table for package storage: key=Package ID, value=Package object.
    - O(1) average insert/search/remove; supports frequent status updates in real time.
    - Chaining gracefully handles collisions via per-bucket lists.

    - insert(): place/update (key,value) in bucket; resize when load factor exceeded
    - search(): return value for key or None
    - remove(): delete key if present
    - items(): iterate all pairs
    - print_table(): pretty-prints core package fields for screenshots
    """

    __slots__ = ("_buckets", "_size", "_max_load_factor")

    def __init__(self, init_capacity: int = 64, max_load_factor: float = 0.75) -> None:
        if init_capacity < 1:
            raise ValueError("init_capacity must be >= 1")
        self._buckets: List[List[Tuple[Any, Any]]] = [[] for _ in range(init_capacity)]
        self._size: int = 0
        self._max_load_factor: float = max_load_factor

    def insert(self, key: Any, value: Any) -> None:
        """Insert or update a (key, value) pair; doubles capacity when load factor exceeds threshold."""
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
        """Iterate all (key, value) pairs for reporting/UI."""
        for bucket in self._buckets:
            for kv in bucket:
                yield kv

    def capacity(self) -> int:
        return len(self._buckets)

    def load_factor(self) -> float:
        return self._size / len(self._buckets)

    def _index(self, key: Any) -> int:
        # Built-in hash % capacity routes key to a bucket
        return hash(key) % len(self._buckets)

    def _resize(self, new_capacity: int) -> None:
        """Rehash all entries into a larger bucket array to maintain O(1) average ops."""
        old_buckets = self._buckets
        self._buckets = [[] for _ in range(new_capacity)]
        self._size = 0
        for bucket in old_buckets:
            for k, v in bucket:
                idx = hash(k) % new_capacity
                self._buckets[idx].append((k, v))
                self._size += 1

    def print_table(self):
        rows = []
        for bucket in self._buckets:
            for key, value in bucket:
                rows.append([
                    str(key),
                    f"{value.street}, {value.city}, {value.state} {value.zip}",
                    str(value.deadline),
                    str(value.weight),
                    str(value.status),
                    str(value.delivery_time)
                ])
        col_widths = [max(
            len(row[i]) for row in rows + [["Package ID", "Address", "Deadline", "Weight", "Status", "Delivery Time"]])
                      for i in range(6)]
        header = ["Package ID", "Address", "Deadline", "Weight", "Status", "Delivery Time"]
        print("  ".join(header[i].ljust(col_widths[i]) for i in range(6)))
        print("-" * (sum(col_widths) + 10))
        for row in rows:
            print("  ".join(row[i].ljust(col_widths[i]) for i in range(6)))

if __name__ == "__main__":
    # Small smoke test for local debugging
    ht = ChainingHashTable()
    ht.insert(1, "Package 1")
    ht.insert(2, "Package 2")
    print("Search 1:", ht.search(1))
    print("Search 2:", ht.search(2))
    ht.remove(1)
    print("After remove, search 1:", ht.search(1))
