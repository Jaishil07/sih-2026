from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Block
from .services import verify_blockchain_integrity

@login_required
def blockchain_explorer_view(request):
    blocks = Block.objects.order_by('-index')
    
    integrity_status = None
    tampered_index = None
    
    if 'verify' in request.GET:
        integrity_status, tampered_index = verify_blockchain_integrity()
        if integrity_status:
            messages.success(request, "Blockchain integrity verified. All cryptographic links are intact.")
        else:
            messages.error(request, f"TAMPER DETECTED: Blockchain integrity check failed at Block #{tampered_index}!")
            
    return render(request, 'blockchain/explorer.html', {
        'blocks': blocks,
        'integrity_status': integrity_status,
        'tampered_index': tampered_index
    })
