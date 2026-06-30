from dataclasses import dataclass

from buzz.model_loader import ModelType


@dataclass
class TranscriptionModelConfig:
    model_type: str = ModelType.WHISPER.value
    whisper_model_size: str | None = None
    hugging_face_model_id: str | None = None
    word_level_timings: str | None = None
    extract_speech: str | None = None
    language: str | None = None
