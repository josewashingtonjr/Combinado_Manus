#!/usr/bin/env python3
"""
Simple test for the Proposal model using existing app structure
"""

import os
import sys
from decimal import Decimal

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path setup
from models import db, Proposal, Invite

def test_proposal_model():
    """Test the Proposal model basic functionality"""
    
    print("Testing Proposal model...")
    
    # Test 1: Create a Proposal instance
    print("\n1. Creating Proposal instance...")
    proposal = Proposal(
        invite_id=1,
        prestador_id=1,
        original_value=Decimal('100.00'),
        proposed_value=Decimal('150.00'),
        justification='Need more materials'
    )
    
    print(f"   ✓ Proposal created: {proposal}")
    print(f"   ✓ Is pending: {proposal.is_pending}")
    print(f"   ✓ Is increase: {proposal.is_increase}")
    print(f"   ✓ Value difference: {proposal.value_difference}")
    
    # Test 2: Test status changes
    print("\n2. Testing status changes...")
    
    # Accept proposal
    proposal.accept("Looks good!")
    print(f"   ✓ After accept - Status: {proposal.status}")
    print(f"   ✓ Is accepted: {proposal.is_accepted}")
    print(f"   ✓ Response reason: {proposal.client_response_reason}")
    
    # Reset and test rejection
    proposal.status = 'pending'
    proposal.responded_at = None
    proposal.client_response_reason = None
    
    proposal.reject("Too expensive")
    print(f"   ✓ After reject - Status: {proposal.status}")
    print(f"   ✓ Is rejected: {proposal.is_rejected}")
    print(f"   ✓ Response reason: {proposal.client_response_reason}")
    
    # Test 3: Test Invite model enhancements
    print("\n3. Testing Invite model enhancements...")
    from datetime import datetime, timedelta
    
    invite = Invite(
        client_id=1,
        invited_phone='+5511999999999',
        service_title='Test Service',
        service_description='Test description',
        original_value=Decimal('100.00'),
        delivery_date=datetime.utcnow() + timedelta(days=7)
    )
    
    print(f"   ✓ Invite created: {invite}")
    print(f"   ✓ Current value: {invite.current_value}")
    print(f"   ✓ Has pending proposal: {invite.has_pending_proposal}")
    print(f"   ✓ Can be accepted: {invite.can_be_accepted}")
    
    # Test setting active proposal
    invite.set_active_proposal(proposal)
    print(f"   ✓ After setting active proposal:")
    print(f"     - Has active proposal: {invite.has_active_proposal}")
    print(f"     - Current proposal ID: {invite.current_proposal_id}")
    print(f"     - Can be accepted: {invite.can_be_accepted}")
    
    # Test clearing active proposal
    invite.clear_active_proposal()
    print(f"   ✓ After clearing active proposal:")
    print(f"     - Has active proposal: {invite.has_active_proposal}")
    print(f"     - Current proposal ID: {invite.current_proposal_id}")
    print(f"     - Can be accepted: {invite.can_be_accepted}")
    
    print("\n✓ All model tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_proposal_model()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)