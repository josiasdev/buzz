from dataclasses import dataclass


@dataclass
class TranscriptionFileInfo:
    file: str | None = None
    export_formats: str | None = None
    output_folder: str | None = None
    source: str | None = None
    url: str | None = None
