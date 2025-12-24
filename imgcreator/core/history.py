"""History tracking for image generations."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class HistoryEntry:
    """A single history entry for a generation."""

    id: str
    timestamp: str
    prompt: str
    resolved_prompt: str
    model: str
    params: dict[str, Any]
    output_path: str | None = None
    status: str = "success"  # "success" or "failed"
    duration_ms: int = 0
    series: str | None = None
    item_id: str | None = None
    error_message: str | None = None
    request_id: str | None = None
    seed: int | None = None

    # Image metadata
    image_hash: str | None = None
    file_size: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryEntry":
        """Create from dictionary."""
        return cls(**data)


class HistoryError(Exception):
    """Base exception for history errors."""

    pass


class HistoryManager:
    """Manages generation history tracking."""

    HISTORY_DIR = "history"

    def __init__(self, project_path: Path | None = None):
        """Initialize the history manager.

        Args:
            project_path: Path to project directory (default: current directory)
        """
        self.project_path = project_path or Path.cwd()
        self.history_dir = self.project_path / self.HISTORY_DIR
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _generate_id(self, prompt: str, timestamp: datetime) -> str:
        """Generate a unique ID for a history entry.

        Format: {timestamp}_{hash}

        Args:
            prompt: Generation prompt
            timestamp: Generation timestamp

        Returns:
            Unique ID string
        """
        ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        return f"{ts_str}_{prompt_hash}"

    def _calculate_image_hash(self, image_path: Path) -> str:
        """Calculate SHA256 hash of an image file.

        Args:
            image_path: Path to image file

        Returns:
            Hex digest of file hash
        """
        sha256 = hashlib.sha256()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def record(
        self,
        prompt: str,
        resolved_prompt: str,
        model: str,
        params: dict[str, Any],
        output_path: Path | None = None,
        status: str = "success",
        duration_ms: int = 0,
        series: str | None = None,
        item_id: str | None = None,
        error_message: str | None = None,
        request_id: str | None = None,
        seed: int | None = None,
        timestamp: datetime | None = None,
    ) -> HistoryEntry:
        """Record a generation in history.

        Args:
            prompt: Original prompt
            resolved_prompt: Resolved prompt (after template substitution)
            model: Model used
            params: Generation parameters (width, height, etc.)
            output_path: Path to generated image (if successful)
            status: "success" or "failed"
            duration_ms: Generation duration in milliseconds
            series: Series name (if from series generation)
            item_id: Item ID (if from series generation)
            error_message: Error message (if failed)
            request_id: API request ID
            seed: Random seed used
            timestamp: Generation timestamp (defaults to now)

        Returns:
            Created HistoryEntry
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        entry_id = self._generate_id(resolved_prompt, timestamp)
        timestamp_str = timestamp.isoformat()

        # Calculate image hash if file exists
        image_hash = None
        file_size = None
        if output_path and output_path.exists():
            try:
                image_hash = self._calculate_image_hash(output_path)
                file_size = output_path.stat().st_size
            except OSError:
                pass  # File might have been deleted

        entry = HistoryEntry(
            id=entry_id,
            timestamp=timestamp_str,
            prompt=prompt,
            resolved_prompt=resolved_prompt,
            model=model,
            params=params,
            output_path=str(output_path) if output_path else None,
            status=status,
            duration_ms=duration_ms,
            series=series,
            item_id=item_id,
            error_message=error_message,
            request_id=request_id,
            seed=seed,
            image_hash=image_hash,
            file_size=file_size,
        )

        # Write to file
        filename = f"{entry_id}.json"
        file_path = self.history_dir / filename

        try:
            with open(file_path, "w") as f:
                json.dump(entry.to_dict(), f, indent=2, default=str)
        except OSError as e:
            raise HistoryError(f"Cannot write history file {file_path}: {e}")

        return entry

    def list_entries(self, limit: int | None = None) -> list[HistoryEntry]:
        """List history entries, most recent first.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of HistoryEntry objects
        """
        entries = []

        # Find all JSON files in history directory
        json_files = list(self.history_dir.glob("*.json"))
        # Sort by modification time (most recent first)
        json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        for file_path in json_files:
            try:
                with open(file_path) as f:
                    data = json.load(f)
                entry = HistoryEntry.from_dict(data)
                entries.append(entry)

                if limit and len(entries) >= limit:
                    break
            except (json.JSONDecodeError, OSError, TypeError):
                # Skip invalid files
                continue

        return entries

    def get_entry(self, entry_id: str) -> HistoryEntry | None:
        """Get a specific history entry by ID.

        Args:
            entry_id: Entry ID (with or without .json extension)

        Returns:
            HistoryEntry or None if not found
        """
        # Remove .json extension if present
        if entry_id.endswith(".json"):
            entry_id = entry_id[:-5]

        file_path = self.history_dir / f"{entry_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path) as f:
                data = json.load(f)
            return HistoryEntry.from_dict(data)
        except (json.JSONDecodeError, OSError, TypeError):
            return None

    def search(
        self,
        prompt: str | None = None,
        series: str | None = None,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[HistoryEntry]:
        """Search history entries by criteria.

        Args:
            prompt: Search for entries containing this text in prompt
            series: Filter by series name
            status: Filter by status ("success" or "failed")
            limit: Maximum number of results

        Returns:
            List of matching HistoryEntry objects
        """
        all_entries = self.list_entries()

        filtered = []
        for entry in all_entries:
            # Filter by prompt
            if prompt:
                prompt_lower = prompt.lower()
                if (
                    prompt_lower not in entry.prompt.lower()
                    and prompt_lower not in entry.resolved_prompt.lower()
                ):
                    continue

            # Filter by series
            if series:
                if entry.series != series:
                    continue

            # Filter by status
            if status:
                if entry.status != status:
                    continue

            filtered.append(entry)

            if limit and len(filtered) >= limit:
                break

        return filtered

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about history.

        Returns:
            Dictionary with statistics
        """
        entries = self.list_entries()

        total = len(entries)
        successful = sum(1 for e in entries if e.status == "success")
        failed = total - successful

        total_duration = sum(e.duration_ms for e in entries)
        avg_duration = total_duration / total if total > 0 else 0

        series_count = len(set(e.series for e in entries if e.series))

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "total_duration_ms": total_duration,
            "avg_duration_ms": int(avg_duration),
            "series_count": series_count,
        }


def create_manager(project_path: Path | None = None) -> HistoryManager:
    """Create a history manager.

    Args:
        project_path: Project directory path

    Returns:
        Configured HistoryManager
    """
    return HistoryManager(project_path=project_path)

