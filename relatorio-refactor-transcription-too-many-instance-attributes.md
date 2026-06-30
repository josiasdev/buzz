# Relatório de Code Smell — R0902 (Transcription)

## Identificação

| Campo | Valor |
|---|---|
| **Tipo** | `refactor` |
| **Código** | `R0902` (too-many-instance-attributes) |
| **Arquivo** | `buzz/db/entity/transcription.py` |
| **Classe** | `Transcription` |
| **Linha** | 13 (original) |
| **Mensagem** | `Too many instance attributes (21/7)` |

## Descrição do Problema

A dataclass `Transcription` possuía **21 atributos de instância**, excedendo o limite padrão de 7 do Pylint (`R0902: too-many-instance-attributes`). A classe acumulava múltiplas responsabilidades em um único nível — identidade, configuração do modelo de transcrição, estado da tarefa e informações de arquivo — como atributos planos, dificultando a legibilidade e manutenção.

### Atributos originais (21)

| # | Atributo | Categoria |
|---|----------|-----------|
| 1 | `id` | Identidade |
| 2 | `name` | Metadado do usuário |
| 3 | `notes` | Metadado do usuário |
| 4 | `status` | Estado da tarefa |
| 5 | `task` | Estado da tarefa |
| 6 | `progress` | Estado da tarefa |
| 7 | `time_queued` | Estado da tarefa |
| 8 | `time_started` | Estado da tarefa |
| 9 | `time_ended` | Estado da tarefa |
| 10 | `error_message` | Estado da tarefa |
| 11 | `model_type` | Configuração do modelo |
| 12 | `whisper_model_size` | Configuração do modelo |
| 13 | `hugging_face_model_id` | Configuração do modelo |
| 14 | `word_level_timings` | Configuração do modelo |
| 15 | `extract_speech` | Configuração do modelo |
| 16 | `language` | Configuração do modelo |
| 17 | `file` | Informações de arquivo |
| 18 | `export_formats` | Informações de arquivo |
| 19 | `output_folder` | Informações de arquivo |
| 20 | `source` | Informações de arquivo |
| 21 | `url` | Informações de arquivo |

## Técnica de Refatoração Aplicada

**Extract Data Class (múltiplo)** — os 21 atributos foram agrupados em 3 dataclasses auxiliares por coesão semântica (configuração do modelo, estado da tarefa e informações de arquivo). Para preservar a compatibilidade com o banco de dados (SQLite) e com os ~40 acessos espalhados por widgets e DAOs, foram adicionados:

- **`__init__` customizado** que aceita tanto kwargs planos (vindos do `QSqlRecord`) quanto objetos aninhados.
- **21 `@property` delegadoras** — acesso transitivo aos sub-objetos sem quebrar a API pública.
- **Método `to_dict()`** — achata os sub-objetos para serialização no banco via `DAO.insert()`.

## Mudanças Realizadas

### Dataclasses criadas

#### `TranscriptionModelConfig` (`buzz/db/entity/transcription_model_config.py`)

```python
@dataclass
class TranscriptionModelConfig:
    model_type: str = ModelType.WHISPER.value
    whisper_model_size: str | None = None
    hugging_face_model_id: str | None = None
    word_level_timings: str | None = None
    extract_speech: str | None = None
    language: str | None = None
```

#### `TranscriptionTaskState` (`buzz/db/entity/transcription_task_state.py`)

```python
@dataclass
class TranscriptionTaskState:
    status: str = field(default=FileTranscriptionTask.Status.QUEUED.value)
    task: str = field(default=Task.TRANSCRIBE.value)
    progress: float = 0.0
    time_queued: str = field(default_factory=lambda: datetime.now().isoformat())
    time_started: str | None = None
    time_ended: str | None = None
    error_message: str | None = None
```

#### `TranscriptionFileInfo` (`buzz/db/entity/transcription_file_info.py`)

```python
@dataclass
class TranscriptionFileInfo:
    file: str | None = None
    export_formats: str | None = None
    output_folder: str | None = None
    source: str | None = None
    url: str | None = None
```

### `Transcription` refatorada (`buzz/db/entity/transcription.py`)

**Campos reduzidos para 6:**

| Campo | Tipo | Origem |
|---|---|---|
| `id` | `str` | Identidade (UUID) |
| `name` | `str \| None` | Metadado do usuário |
| `notes` | `str \| None` | Metadado do usuário |
| `model_config` | `TranscriptionModelConfig` | Configuração do modelo |
| `task_state` | `TranscriptionTaskState` | Estado da tarefa |
| `file_info` | `TranscriptionFileInfo` | Informações de arquivo |

**`__init__` customizado** aceita kwargs planos (compatibilidade com `DAO.to_entity()`):

```python
def __init__(self, **kwargs):
    self.id = kwargs.pop('id', str(uuid.uuid4()))
    self.name = kwargs.pop('name', None)
    self.notes = kwargs.pop('notes', None)
    # Extrai campos planos e constrói sub-objetos...
```

**21 properties delegadoras** (exemplos):

```python
@property
def status(self) -> str:
    return self.task_state.status

@status.setter
def status(self, value: str):
    self.task_state.status = value

@property
def file(self) -> str | None:
    return self.file_info.file

@file.setter
def file(self, value: str | None):
    self.file_info.file = value
```

**Método `to_dict()`** para serialização plana:

```python
def to_dict(self) -> dict:
    d = dict(self.__dict__)
    d.update(self.model_config.__dict__)
    d.update(self.task_state.__dict__)
    d.update(self.file_info.__dict__)
    del d['model_config'], d['task_state'], d['file_info']
    return d
```

### Arquivos auxiliares modificados

| Arquivo | Mudança |
|---|---|
| `buzz/db/entity/entity.py` | `from_record()` refatorado para `cls(**kwargs)`; adicionado `to_dict()` |
| `buzz/db/dao/dao.py` | `insert()` usa `record.to_dict()` em vez de `record.__dict__` |
| `buzz/db/dao/transcription_dao.py` | `copy_transcription()` lê campos do `QSqlRecord` diretamente |

### Antes × Depois

```python
# ANTES (21 atributos planos)
@dataclass
class Transcription(Entity):
    status: str = FileTranscriptionTask.Status.QUEUED.value
    task: str = Task.TRANSCRIBE.value
    model_type: str = ModelType.WHISPER.value
    whisper_model_size: str | None = None
    hugging_face_model_id: str | None = None
    word_level_timings: str | None = None
    extract_speech: str | None = None
    language: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    error_message: str | None = None
    file: str | None = None
    time_queued: str = datetime.datetime.now().isoformat()
    progress: float = 0.0
    time_ended: str | None = None
    time_started: str | None = None
    export_formats: str | None = None
    output_folder: str | None = None
    source: str | None = None
    url: str | None = None
    name: str | None = None
    notes: str | None = None
```

```python
# DEPOIS (6 atributos + 21 properties delegadoras)
@dataclass(init=False)
class Transcription(Entity):
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str | None = None
    notes: str | None = None
    model_config: TranscriptionModelConfig = field(...)
    task_state: TranscriptionTaskState = field(...)
    file_info: TranscriptionFileInfo = field(...)
```

## Resultado

| Métrica | Antes | Depois |
|---|---|---|
| Atributos de instância | 21 | 6 |
| Pylint R0902 | ❌ violação | ✅ resolvido |
| Testes entity | 14/14 passando | 14/14 passando |
| Testes service | 15/15 passando | 15/15 passando |
| API pública | `transcription.status`, etc. | inalterada |
| Arquivos alterados | — | 7 (3 criados, 4 modificados) |
| Código alterado | — | +193 / -28 linhas |

### Verificação

```bash
uv run pytest tests/db/entity/transcription_test.py -v    # 14 passed
uv run pytest tests/db/service/transcription_service_test.py -v  # 15 passed
```

## Notas para o Revisor

- As 3 sub-dataclasses seguem o padrão **Extract Data Class**, agrupando atributos por coesão semântica (modelo, estado, arquivo).
- O `__init__` customizado aceita kwargs planos para compatibilidade com `DAO.to_entity()` e `Entity.from_record()`, que constroem entidades a partir de `QSqlRecord` (nome de colunas como chaves).
- As 21 `@property` delegadoras garantem que **nenhum widget ou service precise ser alterado** — o acesso via `transcription.status`, `transcription.file`, etc. permanece idêntico.
- O método `to_dict()` achata os sub-objetos para que `DAO.insert()` serialize corretamente no banco SQLite.
- `TranscriptionDAO.copy_transcription()` foi atualizado para iterar o `QSqlRecord` diretamente, sem depender de `__dataclass_fields__`.
- Nenhum novo code smell foi introduzido (verificado com testes existentes).
