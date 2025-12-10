#!/usr/bin/env python3
"""
Test script for the new Proposal model and updated Invite model
"""

import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Invite, Proposal
from config import Config

def test_proposal_models():
    """Test the Proposal model and updated Invite model functionality"""
    
    # Create Flask app with test configuration
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./instance/test_combinado.db'
    app.config['TESTING'] = True
    
    # Initialize the database with the app
    db.init_app(app)
    
    with app.app_context():
        print("Testing Proposal and Invite models...")
        
        # Test 1: Create a test user (client)
        print("\n1. Creating test client...")
        client = User.query.filter_by(email='test_client@example.com').first()
        if not client:
            client = User(
                email='test_client@example.com',
                nome='Test Client',
                cpf='12345678901',
                roles='cliente'
            )
            client.set_password('password123')
            db.session.add(client)
            db.session.commit()
        print(f"   Client created: {client}")
        
        # Test 2: Create a test user (prestador)
        print("\n2. Creating test prestador...")
        prestador = User.query.filter_by(email='test_prestador@example.com').first()
        if not prestador:
            prestador = User(
                email='test_prestador@example.com',
                nome='Test Prestador',
                cpf='98765432109',
                roles='prestador'
            )
            prestador.set_password('password123')
            db.session.add(prestador)
            db.session.commit()
        print(f"   Prestador created: {prestador}")
        
        # Test 3: Create a test invite
        print("\n3. Creating test invite...")
        invite = Invite(
            client_id=client.id,
            invited_phone='+5511999999999',
            service_title='Test Service',
            service_description='Test service description',
            service_category='test',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        print(f"   Invite created: {invite}")
        print(f"   Invite can be accepted: {invite.can_be_accepted}")
        print(f"   Invite has pending proposal: {invite.has_pending_proposal}")
        print(f"   Invite current value: {invite.current_value}")
        
        # Test 4: Create a proposal
        print("\n4. Creating test proposal...")
        proposal = Proposal(
            invite_id=invite.id,
            prestador_id=prestador.id,
            original_value=invite.original_value,
            proposed_value=Decimal('150.00'),
            justification='Need more materials than expected'
        )
        db.session.add(proposal)
        db.session.commit()
        print(f"   Proposal created: {proposal}")
        print(f"   Proposal is pending: {proposal.is_pending}")
        print(f"   Proposal is increase: {proposal.is_increase}")
        print(f"   Value difference: {proposal.value_difference}")
        
        # Test 5: Set proposal as active on invite
        print("\n5. Setting proposal as active...")
        invite.set_active_proposal(proposal)
        db.session.commit()
        print(f"   Invite has active proposal: {invite.has_active_proposal}")
        print(f"   Invite can be accepted: {invite.can_be_accepted}")
        print(f"   Active proposal: {invite.get_active_proposal()}")
        
        # Test 6: Accept the proposal
        print("\n6. Accepting proposal...")
        proposal.accept("Looks good, approved!")
        db.session.commit()
        print(f"   Proposal status: {proposal.status}")
        print(f"   Proposal is accepted: {proposal.is_accepted}")
        print(f"   Invite has active proposal: {invite.has_active_proposal}")
        print(f"   Invite effective value: {invite.effective_value}")
        print(f"   Invite current value: {invite.current_value}")
        print(f"   Invite can be accepted: {invite.can_be_accepted}")
        
        # Test 7: Create another proposal and reject it
        print("\n7. Creating and rejecting another proposal...")
        proposal2 = Proposal(
            invite_id=invite.id,
            prestador_id=prestador.id,
            original_value=invite.current_value,
            proposed_value=Decimal('200.00'),
            justification='Additional work required'
        )
        db.session.add(proposal2)
        db.session.commit()
        
        invite.set_active_proposal(proposal2)
        db.session.commit()
        
        proposal2.reject("Too expensive")
        db.session.commit()
        
        print(f"   Second proposal status: {proposal2.status}")
        print(f"   Second proposal is rejected: {proposal2.is_rejected}")
        print(f"   Invite has active proposal: {invite.has_active_proposal}")
        print(f"   Invite current value: {invite.current_value}")
        
        # Test 8: Test relationships
        print("\n8. Testing relationships...")
        print(f"   Invite proposals count: {invite.proposals.count()}")
        print(f"   Prestador created proposals count: {len(prestador.created_proposals)}")
        
        for p in invite.proposals:
            print(f"     Proposal {p.id}: {p.original_value} -> {p.proposed_value} ({p.status})")
        
        print("\n✓ All tests completed successfully!")
        
        return True

if __name__ == "__main__":
    try:
        test_proposal_models()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)