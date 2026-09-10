import hashlib
import json
from django.utils import timezone
from .models import Block

def calculate_block_hash(index, timestamp_str, transactions_json, previous_hash, nonce) -> str:
    """Calculates SHA-256 hash for a block."""
    data_string = f"{index}|{timestamp_str}|{transactions_json}|{previous_hash}|{nonce}"
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

def mine_block(transactions, difficulty=2) -> Block:
    """Mines a new block with a synchronous Proof-of-Work."""
    last_block = Block.objects.order_by('-index').first()
    
    if last_block:
        index = last_block.index + 1
        previous_hash = last_block.block_hash
    else:
        index = 0
        previous_hash = "0" * 64

    now = timezone.now()
    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
    transactions_json = json.dumps(transactions, sort_keys=True)
    
    nonce = 0
    prefix = "0" * difficulty
    
    while True:
        computed_hash = calculate_block_hash(index, timestamp_str, transactions_json, previous_hash, nonce)
        if computed_hash.startswith(prefix):
            break
        nonce += 1
        
    block = Block(
        index=index,
        transactions=transactions,
        previous_hash=previous_hash,
        block_hash=computed_hash,
        nonce=nonce
    )
    block.save()
    
    # Overwrite the auto_now_add to exactly match what we hashed
    block.timestamp = now
    block.save(update_fields=['timestamp'])
    return block

def anchor_document_version(document_version, actor):
    """Anchors a document hash on the blockchain."""
    import uuid
    from apps.audit.services import log_audit_event
    
    tx = {
        "tx_id": str(uuid.uuid4()),
        "type": "DOCUMENT_ANCHOR",
        "doc_id": document_version.document.id,
        "version": document_version.version_number,
        "sha256_hash": document_version.sha256_hash,
        "case_number": document_version.document.case.case_number,
        "actor": actor.username if actor and actor.is_authenticated else "System",
        "timestamp": str(timezone.now())
    }
    
    block = mine_block([tx])
    log_audit_event(actor, "BLOCKCHAIN_BLOCK_MINED", "Block", block.id, details={"index": block.index})
    return block

def verify_blockchain_integrity() -> tuple[bool, int | None]:
    """Verifies the integrity of the entire blockchain."""
    blocks = Block.objects.order_by('index')
    expected_previous = "0" * 64
    
    for block in blocks:
        if block.previous_hash != expected_previous:
            return False, block.index
            
        timestamp_str = block.timestamp.strftime('%Y-%m-%dT%H:%M:%S')
        transactions_json = json.dumps(block.transactions, sort_keys=True)
        
        computed_hash = calculate_block_hash(
            block.index, timestamp_str, transactions_json, block.previous_hash, block.nonce
        )
        
        if block.block_hash != computed_hash:
            return False, block.index
            
        expected_previous = block.block_hash
        
    return True, None
