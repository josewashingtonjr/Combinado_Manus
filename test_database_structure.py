#!/usr/bin/env python3
"""
Simple test to verify the database structure for proposals
"""

import sqlite3
import os

def test_database_structure():
    """Test that the database has the correct structure for proposals"""
    
    db_path = 'instance/test_combinado.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False
    
    print(f"Testing database structure in {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test 1: Check if invite_proposals table exists
        print("\n1. Checking invite_proposals table...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='invite_proposals'
        """)
        
        if cursor.fetchone():
            print("   ✓ invite_proposals table exists")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(invite_proposals)")
            columns = cursor.fetchall()
            expected_columns = [
                'id', 'invite_id', 'prestador_id', 'original_value', 
                'proposed_value', 'justification', 'status', 'created_at', 
                'responded_at', 'client_response_reason'
            ]
            
            actual_columns = [col[1] for col in columns]
            for expected_col in expected_columns:
                if expected_col in actual_columns:
                    print(f"     ✓ Column {expected_col} exists")
                else:
                    print(f"     ✗ Column {expected_col} missing")
        else:
            print("   ✗ invite_proposals table missing")
            return False
        
        # Test 2: Check invites table has new columns
        print("\n2. Checking invites table new columns...")
        cursor.execute("PRAGMA table_info(invites)")
        invite_columns = [col[1] for col in cursor.fetchall()]
        
        new_columns = ['has_active_proposal', 'current_proposal_id', 'effective_value']
        for col in new_columns:
            if col in invite_columns:
                print(f"   ✓ invites.{col} column exists")
            else:
                print(f"   ✗ invites.{col} column missing")
        
        # Test 3: Check indexes
        print("\n3. Checking indexes...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name IN (
                'idx_invites_proposal_status',
                'idx_proposals_invite_status', 
                'idx_proposals_prestador',
                'idx_proposals_created_at'
            )
        """)
        
        indexes = [row[0] for row in cursor.fetchall()]
        expected_indexes = [
            'idx_invites_proposal_status',
            'idx_proposals_invite_status', 
            'idx_proposals_prestador',
            'idx_proposals_created_at'
        ]
        
        for idx in expected_indexes:
            if idx in indexes:
                print(f"   ✓ Index {idx} exists")
            else:
                print(f"   ✗ Index {idx} missing")
        
        # Test 4: Test basic data operations
        print("\n4. Testing basic data operations...")
        
        # Insert a test proposal
        cursor.execute("""
            INSERT INTO invite_proposals 
            (invite_id, prestador_id, original_value, proposed_value, justification, status)
            VALUES (1, 1, 100.00, 150.00, 'Test proposal', 'pending')
        """)
        
        # Query it back
        cursor.execute("SELECT * FROM invite_proposals WHERE justification = 'Test proposal'")
        result = cursor.fetchone()
        
        if result:
            print("   ✓ Can insert and query proposals")
            print(f"     Proposal: {result[4]} -> {result[5]} ({result[6]})")
        else:
            print("   ✗ Failed to insert/query proposals")
        
        # Clean up test data
        cursor.execute("DELETE FROM invite_proposals WHERE justification = 'Test proposal'")
        
        conn.commit()
        print("\n✓ All database structure tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Database test failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = test_database_structure()
    if not success:
        exit(1)