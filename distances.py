import csv
from typing import Dict, List

class AddressIndex:
    def __init__(self) -> None:
        self.addr_to_node: Dict[str, int] = {}
        self.node_to_addr: List[str] = []

    @staticmethod
    def _normalize(addr: str) -> str:
        return addr.strip()

    def load(self, path: str) -> None:
        rows = list(csv.reader(open(path, newline="")))
        for row in rows:
            try:
                node = int(row[0])
            except ValueError:
                continue
            addr = self._normalize(row[2])
            while len(self.node_to_addr) <= node:
                self.node_to_addr.append("")
            self.node_to_addr[node] = addr
            self.addr_to_node[addr] = node

    def node_for(self, address: str) -> int:
        return self.addr_to_node[self._normalize(address)]

    def address_for(self, node: int) -> str:
        return self.node_to_addr[node]


class DistanceMatrix:
    def __init__(self) -> None:
        self._miles: List[List[float]] = []

    def load(self, path: str) -> None:
        rows = list(csv.reader(open(path, newline="")))
        n = len(rows)
        self._miles = [[0.0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(len(rows[i])):
                cell = rows[i][j].strip()
                if cell:
                    self._miles[i][j] = float(cell)

        for i in range(n):
            for j in range(n):
                if i == j:
                    self._miles[i][j] = 0.0
                elif self._miles[i][j] == 0.0 and self._miles[j][i] != 0.0:
                    self._miles[i][j] = self._miles[j][i]

    def get(self, i: int, j: int) -> float:
        return self._miles[i][j]

    def distance_between_addresses(self, a: str, b: str, index: AddressIndex) -> float:
        return self.get(index.node_for(a), index.node_for(b))
