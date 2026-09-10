import hashlib
import os
from django.core.exceptions import ValidationError
from django.db import transaction
from apps.documents.models import Document, DocumentVersion

ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.txt', '.docx'}

def calculate_sha256(file_obj) -> str:
    """Calculates SHA-256 hash by reading the file in chunks."""
    sha256_hash = hashlib.sha256()
    file_obj.seek(0)
    for byte_block in iter(lambda: file_obj.read(65536), b""):
        sha256_hash.update(byte_block)
    file_obj.seek(0)
    return sha256_hash.hexdigest()

def create_document_version(document, uploaded_file, user, change_reason="") -> DocumentVersion:
    """Creates a new DocumentVersion."""
    # Validate extension
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File extension {ext} is not allowed.")
        
    # Calculate hash
    file_hash = calculate_sha256(uploaded_file)
    
    with transaction.atomic():
        # Determine next version
        last_version = document.versions.order_by('-version_number').first()
        next_version_num = (last_version.version_number + 1) if last_version else 1
        
        # Create version
        version = DocumentVersion(
            document=document,
            version_number=next_version_num,
            file=uploaded_file,
            sha256_hash=file_hash,
            change_reason=change_reason,
            created_by=user
        )
        version.save()
        
        # Anchor to blockchain
        from apps.blockchain.services import anchor_document_version
        anchor_document_version(version, user)
        
        return version

def verify_document_version_integrity(version) -> bool:
    """Verifies if the file on disk matches the stored SHA-256 hash."""
    if not version.file or not version.file.storage.exists(version.file.name):
        return False
        
    with version.file.open('rb') as f:
        current_hash = calculate_sha256(f)
        
    return current_hash == version.sha256_hash
