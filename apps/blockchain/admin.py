from django.contrib import admin
from .models import Block

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('index', 'timestamp', 'block_hash', 'previous_hash', 'nonce')
    readonly_fields = ('index', 'timestamp', 'transactions', 'previous_hash', 'block_hash', 'nonce', 'merkle_root')
