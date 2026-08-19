import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

SKILLS_DIR = Path(__file__).parent / "skills"

SKILL_NAME_PATTERN = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
)


@dataclass(frozen=True)
class SkillMetadata:
    name: str
    description: str
    path: Path


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    instructions: str


def _parse_skill_file(
    path: Path,
) -> tuple[dict, str]:
    content = path.read_text(
        encoding="utf-8",
    )

    lines = content.splitlines()

    if not lines or lines[0].strip() != "---":
        raise ValueError(
            f"Skill sem frontmatter YAML: {path}"
        )

    try:
        end_index = next(
            index
            for index, line in enumerate(
                lines[1:],
                start=1,
            )
            if line.strip() == "---"
        )
    except StopIteration as exc:
        raise ValueError(
            f"Frontmatter não finalizado: {path}"
        ) from exc

    frontmatter_text = "\n".join(
        lines[1:end_index]
    )

    metadata = (
        yaml.safe_load(frontmatter_text)
        or {}
    )

    instructions = "\n".join(
        lines[end_index + 1 :]
    ).strip()

    return metadata, instructions


def _validate_metadata(
    path: Path,
    metadata: dict,
) -> None:
    name = metadata.get("name")
    description = metadata.get("description")

    if not isinstance(name, str):
        raise ValueError(
            f"Skill sem name válido: {path}"
        )

    if not SKILL_NAME_PATTERN.fullmatch(name):
        raise ValueError(
            f"Nome de skill inválido: {name}"
        )

    if len(name) > 64:
        raise ValueError(
            f"Nome de skill muito longo: {name}"
        )

    if path.parent.name != name:
        raise ValueError(
            "O name da skill deve ser igual "
            "ao nome do diretório."
        )

    if not isinstance(description, str):
        raise ValueError(
            f"Skill sem description válida: {name}"
        )

    if not description.strip():
        raise ValueError(
            f"Skill sem description: {name}"
        )

    if len(description) > 1024:
        raise ValueError(
            f"Description muito longa: {name}"
        )


@lru_cache(maxsize=1)
def discover_skills() -> dict[str, SkillMetadata]:
    registry: dict[str, SkillMetadata] = {}

    for path in sorted(
        SKILLS_DIR.glob("*/SKILL.md")
    ):
        metadata, _ = _parse_skill_file(path)

        _validate_metadata(
            path,
            metadata,
        )

        name = metadata["name"]

        registry[name] = SkillMetadata(
            name=name,
            description=metadata["description"],
            path=path,
        )

    return registry


@lru_cache(maxsize=None)
def load_skill(
    name: str,
) -> Skill:
    registry = discover_skills()

    metadata = registry.get(name)

    if metadata is None:
        raise KeyError(
            f"Skill desconhecida: {name}"
        )

    _, instructions = _parse_skill_file(
        metadata.path
    )

    return Skill(
        name=metadata.name,
        description=metadata.description,
        instructions=instructions,
    )