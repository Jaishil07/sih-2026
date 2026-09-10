import hashlib
import os
import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from apps.documents.models import Document, DocumentVersion, DocumentSignature

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
    if document.is_locked:
        raise PermissionDenied("Document is permanently locked. No further versions may be uploaded.")

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

def sign_document_version(version, signer):
    """Generates an ephemeral RSA keypair, signs the document version, and locks it."""
    if version.document.is_locked:
        raise PermissionDenied("Document is already locked.")
        
    # Generate ephemeral keypair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    
    # Export public key
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    # Sign payload
    payload = f"{version.sha256_hash}:{signer.username}:{version.version_number}".encode('utf-8')
    signature = private_key.sign(
        payload,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    signature_hex = signature.hex()
    
    certificate_id = f"SIG-2026-{uuid.uuid4().hex[:8].upper()}"
    
    with transaction.atomic():
        # Create Signature
        doc_sig = DocumentSignature.objects.create(
            version=version,
            signer=signer,
            certificate_id=certificate_id,
            signature_hex=signature_hex,
            public_key_pem=public_key_pem,
            algorithm="RSA-PSS-SHA256"
        )
        
        # Lock Document
        document = version.document
        document.is_locked = True
        document.locked_at = timezone.now()
        document.locked_by = signer
        document.save()
        
        version.is_signed = True
        version.save()
        
        # Anchor to Blockchain
        from apps.blockchain.services import mine_block
        block_data = {
            "type": "DOCUMENT_DIGITALLY_SIGNED",
            "doc_id": document.id,
            "certificate_id": certificate_id,
            "signer": signer.username,
            "sha256": version.sha256_hash
        }
        mine_block(block_data)
        
        # Audit log
        from apps.audit.services import log_audit_event
        log_audit_event(signer, 'DOCUMENT_DIGITALLY_SIGNED', 'Document', document.id)
        
    return doc_sig

def verify_signature(signature: DocumentSignature) -> bool:
    """Verifies the document signature using the stored public key."""
    try:
        public_key = serialization.load_pem_public_key(
            signature.public_key_pem.encode('utf-8')
        )
        
        payload = f"{signature.version.sha256_hash}:{signature.signer.username}:{signature.version.version_number}".encode('utf-8')
        signature_bytes = bytes.fromhex(signature.signature_hex)
        
        public_key.verify(
            signature_bytes,
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False
