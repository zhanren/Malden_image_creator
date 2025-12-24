"""Tests for history tracking."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from imgcreator.core.history import (
    HistoryEntry,
    HistoryError,
    HistoryManager,
    create_manager,
)


class TestHistoryEntry:
    """Tests for HistoryEntry."""

    def test_entry_creation(self):
        """Test creating a history entry."""
        entry = HistoryEntry(
            id="test_123",
            timestamp="2024-12-24T14:30:00Z",
            prompt="test prompt",
            resolved_prompt="resolved test prompt",
            model="图片生成4.0",
            params={"width": 512, "height": 512},
        )
        assert entry.id == "test_123"
        assert entry.status == "success"  # default

    def test_entry_to_dict(self):
        """Test entry serialization."""
        entry = HistoryEntry(
            id="test",
            timestamp="2024-12-24T14:30:00Z",
            prompt="test",
            resolved_prompt="test",
            model="test",
            params={},
        )
        data = entry.to_dict()
        assert data["id"] == "test"
        assert "timestamp" in data

    def test_entry_from_dict(self):
        """Test entry deserialization."""
        data = {
            "id": "test",
            "timestamp": "2024-12-24T14:30:00Z",
            "prompt": "test",
            "resolved_prompt": "test",
            "model": "test",
            "params": {"width": 512},
        }
        entry = HistoryEntry.from_dict(data)
        assert entry.id == "test"
        assert entry.params["width"] == 512


class TestHistoryManager:
    """Tests for HistoryManager."""

    @pytest.fixture
    def history_dir(self, tmp_path):
        """Create a temporary history directory."""
        history_dir = tmp_path / "history"
        history_dir.mkdir()
        return history_dir

    def test_manager_creates_directory(self, tmp_path):
        """Test that manager creates history directory if missing."""
        manager = HistoryManager(project_path=tmp_path)
        assert manager.history_dir.exists()
        assert manager.history_dir.name == "history"

    def test_record_success(self, history_dir):
        """Test recording a successful generation."""
        manager = HistoryManager(project_path=history_dir.parent)

        entry = manager.record(
            prompt="test prompt",
            resolved_prompt="resolved test prompt",
            model="图片生成4.0",
            params={"width": 512, "height": 512},
            output_path=history_dir.parent / "output" / "test.png",
            status="success",
            duration_ms=1000,
        )

        assert entry.id is not None
        assert entry.status == "success"
        assert entry.duration_ms == 1000

        # Verify file was created
        history_file = history_dir / f"{entry.id}.json"
        assert history_file.exists()

        # Verify file content
        with open(history_file) as f:
            data = json.load(f)
        assert data["prompt"] == "test prompt"
        assert data["status"] == "success"

    def test_record_failure(self, history_dir):
        """Test recording a failed generation."""
        manager = HistoryManager(project_path=history_dir.parent)

        entry = manager.record(
            prompt="test",
            resolved_prompt="test",
            model="test",
            params={},
            status="failed",
            error_message="API error",
        )

        assert entry.status == "failed"
        assert entry.error_message == "API error"

    def test_record_with_series(self, history_dir):
        """Test recording with series information."""
        manager = HistoryManager(project_path=history_dir.parent)

        entry = manager.record(
            prompt="test",
            resolved_prompt="test",
            model="test",
            params={},
            series="app-icons",
            item_id="home",
        )

        assert entry.series == "app-icons"
        assert entry.item_id == "home"

    def test_record_calculates_image_hash(self, history_dir):
        """Test that image hash is calculated when file exists."""
        # Create a test image file
        output_dir = history_dir.parent / "output"
        output_dir.mkdir()
        image_file = output_dir / "test.png"
        image_file.write_bytes(b"fake image data")

        manager = HistoryManager(project_path=history_dir.parent)

        entry = manager.record(
            prompt="test",
            resolved_prompt="test",
            model="test",
            params={},
            output_path=image_file,
        )

        assert entry.image_hash is not None
        assert entry.file_size == len(b"fake image data")

    def test_list_entries(self, history_dir):
        """Test listing history entries."""
        manager = HistoryManager(project_path=history_dir.parent)

        # Create some entries
        manager.record(
            prompt="first",
            resolved_prompt="first",
            model="test",
            params={},
        )
        manager.record(
            prompt="second",
            resolved_prompt="second",
            model="test",
            params={},
        )

        entries = manager.list_entries()

        assert len(entries) == 2
        # Should be in reverse chronological order (most recent first)
        assert entries[0].prompt == "second"

    def test_list_entries_with_limit(self, history_dir):
        """Test listing with limit."""
        manager = HistoryManager(project_path=history_dir.parent)

        for i in range(5):
            manager.record(
                prompt=f"prompt {i}",
                resolved_prompt=f"prompt {i}",
                model="test",
                params={},
            )

        entries = manager.list_entries(limit=3)
        assert len(entries) == 3

    def test_get_entry(self, history_dir):
        """Test getting a specific entry."""
        manager = HistoryManager(project_path=history_dir.parent)

        entry = manager.record(
            prompt="test",
            resolved_prompt="test",
            model="test",
            params={},
        )

        retrieved = manager.get_entry(entry.id)
        assert retrieved is not None
        assert retrieved.id == entry.id
        assert retrieved.prompt == "test"

    def test_get_entry_not_found(self, history_dir):
        """Test getting non-existent entry."""
        manager = HistoryManager(project_path=history_dir.parent)

        entry = manager.get_entry("nonexistent")
        assert entry is None

    def test_get_entry_without_extension(self, history_dir):
        """Test getting entry without .json extension."""
        manager = HistoryManager(project_path=history_dir.parent)

        entry = manager.record(
            prompt="test",
            resolved_prompt="test",
            model="test",
            params={},
        )

        # Try with .json extension
        retrieved = manager.get_entry(f"{entry.id}.json")
        assert retrieved is not None
        assert retrieved.id == entry.id

    def test_search_by_prompt(self, history_dir):
        """Test searching by prompt."""
        manager = HistoryManager(project_path=history_dir.parent)

        manager.record(
            prompt="cat icon",
            resolved_prompt="flat cat icon",
            model="test",
            params={},
        )
        manager.record(
            prompt="dog icon",
            resolved_prompt="flat dog icon",
            model="test",
            params={},
        )

        results = manager.search(prompt="cat")
        assert len(results) == 1
        assert "cat" in results[0].prompt.lower()

    def test_search_by_series(self, history_dir):
        """Test searching by series."""
        import time

        manager = HistoryManager(project_path=history_dir.parent)

        # Use different prompts to ensure different IDs
        manager.record(
            prompt="test one",
            resolved_prompt="test one",
            model="test",
            params={},
            series="app-icons",
        )
        # Small delay to ensure different timestamps
        time.sleep(0.01)
        manager.record(
            prompt="test two",
            resolved_prompt="test two",
            model="test",
            params={},
            series="other-series",
        )

        results = manager.search(series="app-icons")
        assert len(results) == 1
        assert results[0].series == "app-icons"

    def test_search_by_status(self, history_dir):
        """Test searching by status."""
        manager = HistoryManager(project_path=history_dir.parent)

        manager.record(
            prompt="test",
            resolved_prompt="test",
            model="test",
            params={},
            status="success",
        )
        manager.record(
            prompt="test",
            resolved_prompt="test",
            model="test",
            params={},
            status="failed",
        )

        results = manager.search(status="failed")
        assert len(results) == 1
        assert results[0].status == "failed"

    def test_search_combined_filters(self, history_dir):
        """Test searching with multiple filters."""
        manager = HistoryManager(project_path=history_dir.parent)

        manager.record(
            prompt="cat icon",
            resolved_prompt="flat cat icon",
            model="test",
            params={},
            series="app-icons",
            status="success",
        )
        manager.record(
            prompt="dog icon",
            resolved_prompt="flat dog icon",
            model="test",
            params={},
            series="app-icons",
            status="failed",
        )

        results = manager.search(prompt="cat", series="app-icons", status="success")
        assert len(results) == 1
        assert "cat" in results[0].prompt.lower()

    def test_get_stats(self, history_dir):
        """Test getting history statistics."""
        manager = HistoryManager(project_path=history_dir.parent)

        # Create some entries
        for i in range(3):
            manager.record(
                prompt=f"test {i}",
                resolved_prompt=f"test {i}",
                model="test",
                params={},
                status="success",
                duration_ms=1000,
            )

        manager.record(
            prompt="failed",
            resolved_prompt="failed",
            model="test",
            params={},
            status="failed",
        )

        stats = manager.get_stats()

        assert stats["total"] == 4
        assert stats["successful"] == 3
        assert stats["failed"] == 1
        assert stats["total_duration_ms"] == 3000
        assert stats["avg_duration_ms"] == 750  # 3000 / 4
        assert stats["series_count"] == 0

    def test_get_stats_with_series(self, history_dir):
        """Test stats with series."""
        import time

        manager = HistoryManager(project_path=history_dir.parent)

        # Use different prompts to ensure different IDs
        manager.record(
            prompt="test one",
            resolved_prompt="test one",
            model="test",
            params={},
            series="app-icons",
        )
        # Small delay to ensure different timestamps
        time.sleep(0.01)
        manager.record(
            prompt="test two",
            resolved_prompt="test two",
            model="test",
            params={},
            series="other-series",
        )

        stats = manager.get_stats()
        # Should count unique series
        assert stats["series_count"] == 2

    def test_get_stats_empty(self, history_dir):
        """Test stats with no entries."""
        manager = HistoryManager(project_path=history_dir.parent)

        stats = manager.get_stats()

        assert stats["total"] == 0
        assert stats["successful"] == 0
        assert stats["failed"] == 0
        assert stats["avg_duration_ms"] == 0


class TestCreateManager:
    """Tests for create_manager function."""

    def test_create_manager_default(self):
        """Test creating manager with defaults."""
        manager = create_manager()
        assert isinstance(manager, HistoryManager)

    def test_create_manager_with_path(self, tmp_path):
        """Test creating manager with project path."""
        manager = create_manager(project_path=tmp_path)
        assert manager.project_path == tmp_path


class TestHistoryIntegration:
    """Integration tests for history tracking."""

    def test_history_persists_across_sessions(self, tmp_path):
        """Test that history persists across manager instances."""
        # First session
        manager1 = HistoryManager(project_path=tmp_path)
        entry = manager1.record(
            prompt="test",
            resolved_prompt="test",
            model="test",
            params={},
        )

        # Second session
        manager2 = HistoryManager(project_path=tmp_path)
        retrieved = manager2.get_entry(entry.id)

        assert retrieved is not None
        assert retrieved.id == entry.id

    def test_history_handles_invalid_json(self, tmp_path):
        """Test that invalid JSON files are skipped."""
        history_dir = tmp_path / "history"
        history_dir.mkdir()

        # Create an invalid JSON file
        invalid_file = history_dir / "invalid.json"
        invalid_file.write_text("not valid json")

        manager = HistoryManager(project_path=tmp_path)

        # Should not crash, just skip invalid file
        entries = manager.list_entries()
        assert isinstance(entries, list)

