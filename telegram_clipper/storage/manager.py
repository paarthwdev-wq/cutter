"""
Storage and temporary workspace lifecycle manager.
"""
import os
import shutil
import uuid
import logging
from pathlib import Path
from telegram_clipper.config.settings import TEMP_STORAGE_DIR

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, base_dir: Path = TEMP_STORAGE_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_job_workspace(self, job_id: str | None = None) -> Path:
        """Create a dedicated temporary directory for a processing task."""
        if not job_id:
            job_id = str(uuid.uuid4())[:8]
        job_dir = self.base_dir / f"job_{job_id}"
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    def cleanup_workspace(self, job_dir: Path) -> None:
        """Safely delete job temporary files and workspace directory."""
        if job_dir and job_dir.exists():
            try:
                shutil.rmtree(job_dir, ignore_errors=True)
                logger.info(f"Cleaned up workspace {job_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanly remove {job_dir}: {e}")
