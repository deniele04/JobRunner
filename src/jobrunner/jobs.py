import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

QUEUED = "QUEUED"
RUNNING = "RUNNING"
SUCCEEDED = "SUCCEEDED"
FAILED = "FAILED"
CANCELED = "CANCELED"

FINAL_STATES = {SUCCEEDED, FAILED, CANCELED}

VALID_TRANSITIONS = {
    QUEUED: {RUNNING, CANCELED},
    RUNNING: {SUCCEEDED, FAILED, CANCELED},
    SUCCEEDED: set(),
    FAILED: set(),
    CANCELED: set(),
}


def now_iso() -> str:
    return datetime.now().isoformat()


@dataclass
class Job:
    id: str
    argv: list
    created_at: str
    state: str = QUEUED
    exit_code: Optional[int] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def new(cls, argv):
        return cls(id=uuid.uuid4().hex[:4], argv=list(argv), created_at=now_iso())

    def transition(self, new_state: str) -> None:
        if new_state not in VALID_TRANSITIONS[self.state]:
            raise ValueError(f"Transición inválida: {self.state} -> {new_state}")
        self.state = new_state

    def to_dict(self) -> dict:
        return asdict(self)