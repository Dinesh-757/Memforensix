"""
File handling utilities: safe saving, hashing, format detection.
"""
import hashlib
import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.models.database import DumpFormat

MAGIC_BYTES = {
    b"PAGEDU64": DumpFormat.DMP,
    b"PAGEDUMP": DumpFormat.DMP,
    b"\x7fELF": DumpFormat.ELF,
    b"\xcf\xfa\xed\xfe": DumpFormat.MACHO,
    b"\xfe\xed\xfa\xcf": DumpFormat.MACHO,
}


def detect_format(file_path: str, fallback_ext: str) -> DumpFormat:
    """Inspect leading bytes to guess dump format, fall back to extension."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)
        for magic, fmt in MAGIC_BYTES.items():
            if header.startswith(magic):
                return fmt
    except OSError:
        pass

    ext = fallback_ext.lower().lstrip(".")
    if ext in ("dmp",):
        return DumpFormat.DMP
    if ext == "elf" or ext == "core":
        return DumpFormat.ELF
    return DumpFormat.RAW


def validate_extension(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in settings.ALLOWED_EXTENSIONS


def safe_filename(original_filename: str) -> str:
    ext = Path(original_filename).suffix
    return f"{uuid.uuid4().hex}{ext}"


async def save_upload_file(upload_file: UploadFile, destination_dir: str) -> tuple[str, int, str]:
    """Stream-save an UploadFile to disk, return (path, size_bytes, sha256_hex)."""
    os.makedirs(destination_dir, exist_ok=True)
    stored_name = safe_filename(upload_file.filename)
    dest_path = os.path.join(destination_dir, stored_name)

    sha256 = hashlib.sha256()
    size = 0
    chunk_size = 1024 * 1024  # 1MB

    with open(dest_path, "wb") as out_file:
        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
            size += len(chunk)
            out_file.write(chunk)

    await upload_file.close()
    return dest_path, size, sha256.hexdigest()
