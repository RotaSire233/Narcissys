from dataclasses import dataclass
from typing import Optional
@dataclass
class ChunkChain:
    data: bytes
    chunk_id: int
    next: Optional['ChunkChain'] = None

    @classmethod
    def append(cls,
               head: Optional['ChunkChain'],
               data: bytes,
               chunck_id: int) -> 'ChunkChain':
        return cls(data=data,
                   chunck_id=chunck_id,
                   next=head)
