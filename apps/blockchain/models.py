from django.db import models

class Block(models.Model):
    index = models.PositiveIntegerField(unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    transactions = models.JSONField(default=list)
    previous_hash = models.CharField(max_length=64)
    block_hash = models.CharField(max_length=64, unique=True)
    nonce = models.PositiveIntegerField(default=0)
    merkle_root = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return f"Block #{self.index} - {self.block_hash[:8]}"
