<<<<<<< HEAD
"""Phase 13 Lesson 22 - SKILL.md loader and agent bundle demo.

Parses SKILL.md files with a stdlib YAML-frontmatter parser (no pyyaml),
builds an in-memory skill registry, and simulates an agent loop that loads
a skill by name and uses it to prefix the system prompt.

Skills live under ./skills/*/SKILL.md (created in /tmp for this demo).

Run: python code/main.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


SKILL_ROOT = Path("/tmp/lesson-21-skills")


# ------------------------------------------------------------------
# toy fixture skills
# ------------------------------------------------------------------

RELEASE_NOTES_SKILL = """\
---
name: release-notes-writer
description: Write a changelog entry for the latest merged PRs following this project's style.
---

# Release notes writer

When invoked, run these steps:

1. List PRs merged since the last tag.
2. Group by label: feature, fix, chore, docs.
3. For each PR, write one line: `- <title> (#<num>)`.
4. Draft the release notes and stage them in CHANGELOG.md.

If the user says "ship", run `git tag vX.Y.Z` and `gh release create`.

See style-guide.md for the house style rules.
"""

RELEASE_STYLE = """\
# Release notes style guide

- One line per PR. No prose.
- Feature entries first; fixes second; chores third; docs last.
- Skip chores from public changelog.
"""

PR_REVIEW_SKILL = """\
---
name: pr-reviewer
description: Review a PR diff against the project's style guide and open clarifying comments.
---

# PR reviewer

Steps:

1. Fetch the PR diff.
2. Identify rules from AGENTS.md that the diff touches.
3. Write one comment per clear violation.
"""


def setup_fixtures() -> None:
    SKILL_ROOT.mkdir(parents=True, exist_ok=True)
    rn = SKILL_ROOT / "release-notes-writer"
    rn.mkdir(exist_ok=True)
    (rn / "SKILL.md").write_text(RELEASE_NOTES_SKILL)
    (rn / "style-guide.md").write_text(RELEASE_STYLE)
    pr = SKILL_ROOT / "pr-reviewer"
    pr.mkdir(exist_ok=True)
    (pr / "SKILL.md").write_text(PR_REVIEW_SKILL)


# ------------------------------------------------------------------
# loader
# ------------------------------------------------------------------

@dataclass
class Skill:
    name: str
    description: str
    body: str
    root: Path


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_raw = text[4:end]
    body = text[end + 5:]
    fm: dict = {}
    for line in fm_raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body


def load_skill(folder: Path) -> Skill | None:
    skill_md = folder / "SKILL.md"
    if not skill_md.exists():
        return None
    text = skill_md.read_text()
    fm, body = parse_frontmatter(text)
    if "name" not in fm:
        return None
    return Skill(name=fm["name"], description=fm.get("description", ""),
                 body=body.strip(), root=folder)


def discover_skills(root: Path) -> dict[str, Skill]:
    registry: dict[str, Skill] = {}
    if not root.exists():
        return registry
    for item in sorted(root.iterdir()):
        if item.is_dir():
            s = load_skill(item)
            if s:
                registry[s.name] = s
    return registry


def read_subresource(skill: Skill, filename: str) -> str:
    path = skill.root / filename
    if not path.exists():
        return f"(no such subresource: {filename})"
    return path.read_text()


# ------------------------------------------------------------------
# demo agent loop
# ------------------------------------------------------------------

def agent_run(skill: Skill, user_task: str) -> str:
    print(f"  [loader] loading skill '{skill.name}'")
    print(f"  [loader] progressive disclosure: read style-guide only if needed")
    system_prompt = f"""You are an assistant with the {skill.name} skill loaded.

Skill instructions:
{skill.body}

User task: {user_task}
"""
    # demonstrate progressive disclosure
    if "style-guide" in skill.body.lower():
        style = read_subresource(skill, "style-guide.md")
        print(f"  [loader] subresource pulled ({len(style)} bytes)")
        system_prompt += f"\n\nAdditional style guide:\n{style}"
    return system_prompt


def demo() -> None:
    print("=" * 72)
    print("PHASE 13 LESSON 21 - SKILLS AND AGENT SDK LOADER")
    print("=" * 72)

    setup_fixtures()

    print(f"\n--- discovery under {SKILL_ROOT} ---")
    skills = discover_skills(SKILL_ROOT)
    for name, s in skills.items():
        print(f"  {name:25s} -> {s.description}")

    print(f"\n--- invoke release-notes-writer with a fake user task ---")
    prompt = agent_run(skills["release-notes-writer"],
                       "draft the 1.4.0 release notes")
    print(f"\n[the system prompt the agent would send to the model]")
    print("-" * 72)
    print(prompt[:600] + "...")

    print("\n--- AGENTS.md + SKILL.md + MCP : the three-layer stack ---")
    print("  AGENTS.md (repo root)   -> project conventions at session start")
    print("  SKILL.md (./skills/*/)  -> reusable workflows on demand")
    print("  MCP server              -> tools the skill invokes (Phase 13 / 06-14)")


if __name__ == "__main__":
    demo()
=======
from __future__ import annotations

import json
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


CORE_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class SkillReport:
    valid: bool
    name: str | None
    description: str | None
    body: str
    core_fields: tuple[str, ...]
    runtime_extensions: tuple[str, ...]
    issues: tuple[ValidationIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["issues"] = [asdict(issue) for issue in self.issues]
        return data


class FrontmatterSyntaxError(ValueError):
    """Raised when the lesson's deliberately small YAML subset is invalid."""


def _decode_scalar(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value.startswith('"'):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as error:
            raise FrontmatterSyntaxError(f"invalid quoted scalar: {error.msg}") from error
        if not isinstance(decoded, str):
            raise FrontmatterSyntaxError("frontmatter scalars must be strings")
        return decoded
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise FrontmatterSyntaxError("unterminated single-quoted scalar")
        return value[1:-1].replace("''", "'")
    if value[0] in "[{&*!":
        raise FrontmatterSyntaxError("unsupported YAML construct in portable subset")
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse top-level scalars, block scalars, and a one-level metadata map."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise FrontmatterSyntaxError("SKILL.md must begin with an exact --- line")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise FrontmatterSyntaxError("frontmatter needs a closing --- line") from error

    metadata: dict[str, Any] = {}
    index = 1
    while index < end:
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line[:1].isspace() or ":" not in line:
            raise FrontmatterSyntaxError(f"malformed top-level line {index + 1}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", key):
            raise FrontmatterSyntaxError(f"invalid field name {key!r}")
        if key in metadata:
            raise FrontmatterSyntaxError(f"duplicate field {key!r}")

        value = raw_value.strip()
        if value in {">", "|"}:
            block: list[str] = []
            index += 1
            while index < end and (not lines[index] or lines[index][:1].isspace()):
                block.append(lines[index].lstrip())
                index += 1
            metadata[key] = (" " if value == ">" else "\n").join(block).strip()
            continue
        if key == "metadata" and not value:
            nested: dict[str, str] = {}
            index += 1
            while index < end and (not lines[index] or lines[index][:1].isspace()):
                nested_line = lines[index].strip()
                if nested_line:
                    if ":" not in nested_line:
                        raise FrontmatterSyntaxError(
                            f"malformed metadata line {index + 1}"
                        )
                    nested_key, nested_value = nested_line.split(":", 1)
                    nested_key = nested_key.strip()
                    if nested_key in nested:
                        raise FrontmatterSyntaxError(
                            f"duplicate metadata field {nested_key!r}"
                        )
                    nested[nested_key] = _decode_scalar(nested_value)
                index += 1
            metadata[key] = nested
            continue
        metadata[key] = _decode_scalar(value)
        index += 1

    body = "\n".join(lines[end + 1 :]).strip()
    return metadata, body


def validate_skill_text(
    text: str,
    directory_name: str,
    allowed_runtime_extensions: Iterable[str] = (),
) -> SkillReport:
    issues: list[ValidationIssue] = []
    try:
        fields, body = parse_frontmatter(text)
    except FrontmatterSyntaxError as error:
        issue = ValidationIssue("frontmatter-syntax", str(error))
        return SkillReport(False, None, None, "", (), (), (issue,))

    name_value = fields.get("name")
    description_value = fields.get("description")
    name = name_value if isinstance(name_value, str) else None
    description = description_value if isinstance(description_value, str) else None

    if not name:
        issues.append(ValidationIssue("name-required", "name must be a non-empty string"))
    elif len(name) > 64:
        issues.append(ValidationIssue("name-too-long", "name must be at most 64 characters"))
    elif not NAME_PATTERN.fullmatch(name):
        issues.append(
            ValidationIssue(
                "name-format",
                "name must use lowercase letters, digits, and single hyphens",
            )
        )
    elif name != directory_name:
        issues.append(
            ValidationIssue(
                "directory-mismatch",
                f"name {name!r} must match directory {directory_name!r}",
            )
        )

    if not description or not description.strip():
        issues.append(
            ValidationIssue("description-required", "description must explain when to use the skill")
        )
    elif len(description) > 1024:
        issues.append(
            ValidationIssue(
                "description-too-long", "description must be at most 1024 characters"
            )
        )

    if "compatibility" in fields:
        compatibility = fields["compatibility"]
        if not isinstance(compatibility, str) or not compatibility.strip():
            issues.append(
                ValidationIssue(
                    "compatibility-empty",
                    "compatibility must be a non-empty string when provided",
                )
            )
        elif len(compatibility) > 500:
            issues.append(
                ValidationIssue(
                    "compatibility-too-long",
                    "compatibility must be at most 500 characters",
                )
            )

    if "metadata" in fields:
        metadata = fields["metadata"]
        if not isinstance(metadata, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in metadata.items()
        ):
            issues.append(
                ValidationIssue(
                    "metadata-shape",
                    "metadata must map string keys to string values",
                )
            )

    if "allowed-tools" in fields:
        allowed_tools = fields["allowed-tools"]
        if not isinstance(allowed_tools, str) or not allowed_tools.strip():
            issues.append(
                ValidationIssue(
                    "allowed-tools-shape",
                    "allowed-tools must be a non-empty space-separated string",
                )
            )
    if not body:
        issues.append(ValidationIssue("body-required", "SKILL.md needs instruction content"))

    extension_names = sorted(set(fields) - CORE_FIELDS)
    allowed = set(allowed_runtime_extensions)
    for field in extension_names:
        if field not in allowed:
            issues.append(
                ValidationIssue(
                    "unsupported-runtime-field",
                    f"{field!r} is not part of the portable contract or this host policy",
                )
            )

    return SkillReport(
        valid=not issues,
        name=name,
        description=description,
        body=body,
        core_fields=tuple(sorted(set(fields) & CORE_FIELDS)),
        runtime_extensions=tuple(extension_names),
        issues=tuple(issues),
    )


@dataclass(frozen=True)
class TaskShape:
    repeatable_method: bool = False
    repository_default: bool = False
    external_capability: bool = False
    lifecycle_event: bool = False
    deterministic_logic: bool = False
    isolated_delegation: bool = False


def select_primitives(task: TaskShape) -> tuple[str, ...]:
    """Select composable primitives by responsibility, not by product branding."""
    choices: list[str] = []
    if task.repository_default:
        choices.append("AGENTS.md")
    if task.repeatable_method:
        choices.append("Agent Skill")
    if task.external_capability:
        choices.append("MCP tool")
    if task.lifecycle_event:
        choices.append("hook")
    if task.deterministic_logic:
        choices.append("ordinary code")
    if task.isolated_delegation:
        choices.append("subagent")
    return tuple(choices or ["prompt"])


def demo() -> None:
    portable_example = """---
name: incident-summary
description: Summarize an incident timeline when the user supplies event notes.
metadata:
  owner: reliability
---

# Incident summary

Preserve timestamps and separate observations from inferences.
"""
    host_extended_example = portable_example.replace(
        "description:", "user-invocable: true\ndescription:", 1
    )
    invalid_example = portable_example.replace(
        "name: incident-summary", "name: Incident_Summary", 1
    )
    with tempfile.TemporaryDirectory(prefix="lesson-22-") as temp_dir:
        base = Path(temp_dir)
        portable_dir = base / "incident-summary"
        portable_dir.mkdir()
        portable_path = portable_dir / "SKILL.md"
        portable_path.write_text(portable_example, encoding="utf-8")
        portable_report = validate_skill_text(
            portable_path.read_text(encoding="utf-8"), portable_dir.name
        )
        host_report = validate_skill_text(
            host_extended_example,
            "incident-summary",
            allowed_runtime_extensions={"user-invocable"},
        )
        invalid_report = validate_skill_text(
            invalid_example, "incident-summary"
        )

    result = {
        "validation": portable_report.to_dict(),
        "validation_cases": {
            "portable_core": portable_report.to_dict(),
            "host_extended": host_report.to_dict(),
            "invalid_package": invalid_report.to_dict(),
        },
        "decision_examples": {
            "one_off_rewrite": select_primitives(TaskShape()),
            "repeatable_repo_workflow_with_api": select_primitives(
                TaskShape(
                    repeatable_method=True,
                    repository_default=True,
                    external_capability=True,
                )
            ),
            "post_test_automation": select_primitives(TaskShape(lifecycle_event=True)),
            "schema_normalization": select_primitives(TaskShape(deterministic_logic=True)),
            "parallel_isolated_research": select_primitives(
                TaskShape(isolated_delegation=True)
            ),
        },
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    demo()
>>>>>>> main
