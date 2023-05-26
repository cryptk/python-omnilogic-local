from enum import Enum
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class PrettyEnum(Enum):
    def pretty(self) -> str:
        return self.name.replace("_", " ").title()

    @classmethod
    def from_pretty(cls, name: str) -> Self:
        return cls[name.upper().replace(" ", "_")]
