"""Database backup automation script."""

import os
import subprocess
import datetime
import boto3
from pathlib import Path


class BackupService:
    def __init__(self, database_url: str = None, s3_bucket: str = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "")
        self.s3_bucket = s3_bucket or os.getenv("BACKUP_S3_BUCKET", "")
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self) -> str:
        """Create a database backup."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kitchenos_backup_{timestamp}.sql"
        filepath = self.backup_dir / filename

        if "postgresql" in self.database_url:
            self._backup_postgresql(filepath)
        elif "sqlite" in self.database_url:
            self._backup_sqlite(filepath)
        else:
            raise ValueError(f"Unsupported database: {self.database_url}")

        print(f"Backup created: {filepath}")
        return str(filepath)

    def _backup_postgresql(self, filepath: Path):
        """Backup PostgreSQL using pg_dump."""
        # Parse connection details from URL
        # postgresql://user:pass@host:port/dbname
        cmd = [
            "pg_dump",
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            "-f", str(filepath),
            self.database_url
        ]
        subprocess.run(cmd, check=True)

    def _backup_sqlite(self, filepath: Path):
        """Backup SQLite database."""
        db_path = self.database_url.replace("sqlite:///", "")
        import shutil
        shutil.copy2(db_path, filepath)

    def upload_to_s3(self, filepath: str) -> str:
        """Upload backup to S3."""
        if not self.s3_bucket:
            print("S3 bucket not configured, skipping upload")
            return ""

        s3 = boto3.client("s3")
        filename = Path(filepath).name
        s3_key = f"backups/{filename}"

        s3.upload_file(filepath, self.s3_bucket, s3_key)
        print(f"Uploaded to s3://{self.s3_bucket}/{s3_key}")
        return f"s3://{self.s3_bucket}/{s3_key}"

    def cleanup_old_backups(self, keep_days: int = 30):
        """Remove backups older than keep_days."""
        cutoff = datetime.datetime.now() - datetime.timedelta(days=keep_days)

        for backup_file in self.backup_dir.glob("kitchenos_backup_*.sql"):
            if backup_file.stat().st_mtime < cutoff.timestamp():
                backup_file.unlink()
                print(f"Deleted old backup: {backup_file}")

    def list_backups(self) -> list:
        """List available backups."""
        backups = []
        for backup_file in sorted(self.backup_dir.glob("kitchenos_backup_*.sql")):
            backups.append({
                "filename": backup_file.name,
                "size_mb": backup_file.stat().st_size / (1024 * 1024),
                "created": datetime.datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
            })
        return backups


if __name__ == "__main__":
    import sys
    backup_service = BackupService()

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        for b in backup_service.list_backups():
            print(f"  {b['filename']} ({b['size_mb']:.1f} MB) - {b['created']}")
    else:
        filepath = backup_service.create_backup()
        backup_service.upload_to_s3(filepath)
        backup_service.cleanup_old_backups()
