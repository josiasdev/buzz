import datetime
from dataclasses import dataclass, field

from buzz.transcriber.transcriber import FileTranscriptionTask, Task


@dataclass
class TranscriptionTaskState:
    status: str = field(default=FileTranscriptionTask.Status.QUEUED.value)
    task: str = field(default=Task.TRANSCRIBE.value)
    progress: float = 0.0
    time_queued: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    time_started: str | None = None
    time_ended: str | None = None
    error_message: str | None = None
