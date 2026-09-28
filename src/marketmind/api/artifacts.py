"""Integrity checks for immutable, repository-bundled production artifacts."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

MANIFEST_PATH = Path("models/artifact_manifest.json")


class ArtifactVerificationError(RuntimeError):
    """Safe artifact verification failure; messages contain no filesystem paths."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ArtifactEntry:
    module: str
    path: str
    sha256: str
    size_bytes: int
    version: str
    artifact_role: str
    immutable: bool


class ArtifactVerifier:
    def __init__(self, project_root: Path, manifest_path: Path = MANIFEST_PATH):
        self.root = project_root.resolve()
        self.entries = self._read_manifest(manifest_path)

    def _safe_path(self, relative: str) -> Path:
        candidate = Path(relative)
        if candidate.is_absolute():
            raise ArtifactVerificationError("ARTIFACT_PATH_UNSAFE")
        resolved = (self.root / candidate).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ArtifactVerificationError("ARTIFACT_PATH_UNSAFE") from exc
        return resolved

    def _read_manifest(self, relative: Path) -> dict[str, ArtifactEntry]:
        try:
            path = self._safe_path(str(relative))
            raw = json.loads(path.read_text(encoding="utf-8"))
            if raw.get("manifest_version") != "1.0" or not isinstance(raw.get("artifacts"), list):
                raise ValueError
            entries: dict[str, ArtifactEntry] = {}
            for item in raw["artifacts"]:
                entry = ArtifactEntry(**item)
                if (
                    not entry.module
                    or entry.module in entries
                    or not entry.immutable
                    or entry.size_bytes < 1
                    or len(entry.sha256) != 64
                    or any(c not in "0123456789abcdef" for c in entry.sha256)
                ):
                    raise ValueError
                self._safe_path(entry.path)
                entries[entry.module] = entry
            return entries
        except ArtifactVerificationError:
            raise
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ArtifactVerificationError("ARTIFACT_MANIFEST_INVALID") from exc

    def verify(self, module: str, expected_relative_path: str | None = None) -> Path:
        entry = self.entries.get(module)
        if entry is None:
            raise ArtifactVerificationError("ARTIFACT_MANIFEST_ENTRY_MISSING")
        if expected_relative_path is not None and entry.path != expected_relative_path:
            raise ArtifactVerificationError("ARTIFACT_PATH_MISMATCH")
        path = self._safe_path(entry.path)
        try:
            stat = path.stat()
        except OSError as exc:
            raise ArtifactVerificationError("ARTIFACT_MISSING") from exc
        if not path.is_file():
            raise ArtifactVerificationError("ARTIFACT_MISSING")
        if stat.st_size != entry.size_bytes:
            raise ArtifactVerificationError("ARTIFACT_SIZE_MISMATCH")
        digest = hashlib.sha256()
        try:
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError as exc:
            raise ArtifactVerificationError("ARTIFACT_UNREADABLE") from exc
        if digest.hexdigest() != entry.sha256:
            raise ArtifactVerificationError("ARTIFACT_CHECKSUM_MISMATCH")
        return path

    def verify_all(self) -> dict[str, Path]:
        return {module: self.verify(module) for module in self.entries}


def verify_repository_artifacts(project_root: Path = Path(".")) -> dict[str, Path]:
    return ArtifactVerifier(project_root).verify_all()


if __name__ == "__main__":
    verified = verify_repository_artifacts()
    print(f"verified {len(verified)} immutable production artifacts")
