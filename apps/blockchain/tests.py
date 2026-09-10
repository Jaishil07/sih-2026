from django.test import TestCase
from django.utils import timezone
from .models import Block
from .services import mine_block, verify_blockchain_integrity

class BlockchainCoreTests(TestCase):
    def test_genesis_block_generation(self):
        """Test that the first mined block is the Genesis Block."""
        txs = [{"msg": "Genesis Transaction"}]
        block = mine_block(txs, difficulty=1)
        
        self.assertEqual(block.index, 0)
        self.assertEqual(block.previous_hash, "0" * 64)
        self.assertEqual(block.transactions, txs)
        self.assertTrue(block.block_hash.startswith("0"))

    def test_verify_blockchain_integrity(self):
        """Test the integrity verification function."""
        # Mine genesis block
        block1 = mine_block([{"data": "A"}], difficulty=1)
        # Mine second block
        block2 = mine_block([{"data": "B"}], difficulty=1)
        
        is_valid, tampered_idx = verify_blockchain_integrity()
        self.assertTrue(is_valid)
        self.assertIsNone(tampered_idx)
        
        # Tamper with the database
        block1.transactions = [{"data": "TAMPERED"}]
        block1.save(update_fields=['transactions'])
        
        is_valid, tampered_idx = verify_blockchain_integrity()
        self.assertFalse(is_valid)
        self.assertEqual(tampered_idx, 0)
