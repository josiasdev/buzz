import datetime
import os
import uuid
from dataclasses import dataclass, field
from uuid import UUID

from buzz.db.entity.entity import Entity
from buzz.db.entity.transcription_file_info import TranscriptionFileInfo
from buzz.db.entity.transcription_model_config import TranscriptionModelConfig
from buzz.db.entity.transcription_task_state import TranscriptionTaskState
from buzz.model_loader import ModelType
from buzz.settings.settings import Settings
from buzz.transcriber.transcriber import OutputFormat, Task, FileTranscriptionTask


@dataclass(init=False)
class Transcription(Entity):
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str | None = None
    notes: str | None = None
    model_config: TranscriptionModelConfig = field(
        default_factory=TranscriptionModelConfig,
    )
    task_state: TranscriptionTaskState = field(
        default_factory=TranscriptionTaskState,
    )
    file_info: TranscriptionFileInfo = field(default_factory=TranscriptionFileInfo)

    def __init__(self, **kwargs):
        self.id = kwargs.pop('id', str(uuid.uuid4()))
        self.name = kwargs.pop('name', None)
        self.notes = kwargs.pop('notes', None)

        model_config = kwargs.pop('model_config', None)
        if model_config is not None:
            if isinstance(model_config, dict):
                self.model_config = TranscriptionModelConfig(**model_config)
            else:
                self.model_config = model_config
        else:
            model_fields = TranscriptionModelConfig.__dataclass_fields__
            model_kwargs = {k: kwargs.pop(k) for k in list(kwargs) if k in model_fields}
            self.model_config = TranscriptionModelConfig(**model_kwargs)

        task_state = kwargs.pop('task_state', None)
        if task_state is not None:
            if isinstance(task_state, dict):
                self.task_state = TranscriptionTaskState(**task_state)
            else:
                self.task_state = task_state
        else:
            task_fields = TranscriptionTaskState.__dataclass_fields__
            task_kwargs = {k: kwargs.pop(k) for k in list(kwargs) if k in task_fields}
            self.task_state = TranscriptionTaskState(**task_kwargs)

        file_info = kwargs.pop('file_info', None)
        if file_info is not None:
            if isinstance(file_info, dict):
                self.file_info = TranscriptionFileInfo(**file_info)
            else:
                self.file_info = file_info
        else:
            file_fields = TranscriptionFileInfo.__dataclass_fields__
            file_kwargs = {k: kwargs.pop(k) for k in list(kwargs) if k in file_fields}
            self.file_info = TranscriptionFileInfo(**file_kwargs)

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d.update(self.model_config.__dict__)
        d.update(self.task_state.__dict__)
        d.update(self.file_info.__dict__)
        del d['model_config']
        del d['task_state']
        del d['file_info']
        return d

    @property
    def status(self) -> str:
        return self.task_state.status

    @status.setter
    def status(self, value: str):
        self.task_state.status = value

    @property
    def task(self) -> str:
        return self.task_state.task

    @property
    def model_type(self) -> str:
        return self.model_config.model_type

    @property
    def whisper_model_size(self) -> str | None:
        return self.model_config.whisper_model_size

    @property
    def hugging_face_model_id(self) -> str | None:
        return self.model_config.hugging_face_model_id

    @property
    def word_level_timings(self) -> str | None:
        return self.model_config.word_level_timings

    @word_level_timings.setter
    def word_level_timings(self, value: str | None):
        self.model_config.word_level_timings = value

    @property
    def extract_speech(self) -> str | None:
        return self.model_config.extract_speech

    @property
    def language(self) -> str | None:
        return self.model_config.language

    @property
    def error_message(self) -> str | None:
        return self.task_state.error_message

    @property
    def file(self) -> str | None:
        return self.file_info.file

    @file.setter
    def file(self, value: str | None):
        self.file_info.file = value

    @property
    def time_queued(self) -> str:
        return self.task_state.time_queued

    @property
    def progress(self) -> float:
        return self.task_state.progress

    @property
    def time_ended(self) -> str | None:
        return self.task_state.time_ended

    @property
    def time_started(self) -> str | None:
        return self.task_state.time_started

    @property
    def export_formats(self) -> str | None:
        return self.file_info.export_formats

    @property
    def output_folder(self) -> str | None:
        return self.file_info.output_folder

    @property
    def source(self) -> str | None:
        return self.file_info.source

    @property
    def url(self) -> str | None:
        return self.file_info.url

    @property
    def id_as_uuid(self):
        return UUID(hex=self.id)

    @property
    def status_as_status(self):
        return FileTranscriptionTask.Status(self.status)

    def get_output_file_path(
        self,
        output_format: OutputFormat,
        output_directory: str | None = None,
    ):
        input_file_name = os.path.splitext(os.path.basename(self.file))[0]

        date_time_now = datetime.datetime.now().strftime("%d-%b-%Y %H-%M-%S")

        export_file_name_template = Settings().get_default_export_file_template()

        output_file_name = (
            export_file_name_template.replace("{{ input_file_name }}", input_file_name)
            .replace("{{ task }}", self.task)
            .replace("{{ language }}", self.language or "")
            .replace("{{ model_type }}", self.model_type)
            .replace("{{ model_size }}", self.whisper_model_size or "")
            .replace("{{ date_time }}", date_time_now)
            + f".{output_format.value}"
        )

        output_directory = output_directory or os.path.dirname(self.file)
        return os.path.join(output_directory, output_file_name)
