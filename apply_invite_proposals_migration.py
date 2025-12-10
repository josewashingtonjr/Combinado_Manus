#!/usr/bin/env python3
"""
Migration script for invite proposals system
Applies the database changes needed for the proposal alteration system
"""

import sqlite3
import os
from datetime import datetime

def apply_migration():
    """Apply the invite proposals migration to the database"""
    
    # Database paths to update
    db_paths = [
        'instance/sistema_combinado.db',
        'instance/test_combinado.db'
    ]
    
    migration_sql = """
    -- Create invite_proposals table
    CREATE TABLE IF NOT EXISTS invite_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invite_id INTEGER NOT NULL,
        prestador_id INTEGER NOT NULL,
        original_value DECIMAL(10,2) NOT NULL,
        proposed_value DECIMAL(10,2) NOT NULL,
        justification TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        responded_at TIMESTAMP NULL,
        client_response_reason TEXT NULL,
        FOREIGN KEY (invite_id) REFERENCES invites(id) ON DELETE CASCADE,
        FOREIGN KEY (prestador_id) REFERENCES users(id) ON DELETE CASCADE
    );
    
    -- Create indexes for performance optimization
    CREATE INDEX IF NOT EXISTS idx_invites_proposal_status ON invites(has_active_proposal, status);
    CREATE INDEX IF NOT EXISTS idx_proposals_invite_status ON invite_proposals(invite_id, status);
    CREATE INDEX IF NOT EXISTS idx_proposals_prestador ON invite_proposals(prestador_id);
    CREATE INDEX IF NOT EXISTS idx_proposals_created_at ON invite_proposals(created_at);
    """
    
    # SQL to add columns to invites table (SQLite safe approach)
    add_columns_sql = [
        "ALTER TABLE invites ADD COLUMN has_active_proposal BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE invites ADD COLUMN current_proposal_id INTEGER NULL;",
        "ALTER TABLE invites ADD COLUMN effective_value DECIMAL(10,2) NULL;"
    ]
    
    for db_path in db_paths:
        if not os.path.exists(db_path):
            print(f"Database {db_path} not found, skipping...")
            continue
            
        print(f"Applying migration to {db_path}...")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if invite_proposals table already exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='invite_proposals'
            """)
            
            if cursor.fetchone() is None:
                print("  Creating invite_proposals table...")
                cursor.executescript(migration_sql)
            else:
                print("  invite_proposals table already exists, skipping creation...")
            
            # Add columns to invites table if they don't exist
            cursor.execute("PRAGMA table_info(invites)")
            existing_columns = [column[1] for column in cursor.fetchall()]
            
            columns_to_add = [
                ('has_active_proposal', "ALTER TABLE invites ADD COLUMN has_active_proposal BOOLEAN DEFAULT FALSE;"),
                ('current_proposal_id', "ALTER TABLE invites ADD COLUMN current_proposal_id INTEGER NULL;"),
                ('effective_value', "ALTER TABLE invites ADD COLUMN effective_value DECIMAL(10,2) NULL;")
            ]
            
            for column_name, sql in columns_to_add:
                if column_name not in existing_columns:
                    print(f"  Adding column {column_name} to invites table...")
                    try:
                        cursor.execute(sql)
                    except Exception as e:
                        print(f"    Error adding column {column_name}: {e}")
                else:
                    print(f"  Column {column_name} already exists in invites table, skipping...")
            
            # Create indexes (IF NOT EXISTS handles duplicates)
            print("  Creating indexes...")
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_invites_proposal_status ON invites(has_active_proposal, status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposals_invite_status ON invite_proposals(invite_id, status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposals_prestador ON invite_proposals(prestador_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposals_created_at ON invite_proposals(created_at);")
            except Exception as e:
                print(f"    Error creating indexes: {e}")
            
            conn.commit()
            print(f"  Migration applied successfully to {db_path}")
            
        except Exception as e:
            print(f"  Error applying migration to {db_path}: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'conn' in locals():
                conn.close()

def verify_migration():
    """Verify that the migration was applied correctly"""
    
    db_paths = [
        'instance/sistema_combinado.db',
        'instance/test_combinado.db'
    ]
    
    for db_path in db_paths:
        if not os.path.exists(db_path):
            continue
            
        print(f"\nVerifying migration in {db_path}...")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if invite_proposals table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='invite_proposals'
            """)
            
            if cursor.fetchone():
                print("  ✓ invite_proposals table exists")
                
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
                        print(f"    ✓ Column {expected_col} exists")
                    else:
                        print(f"    ✗ Column {expected_col} missing")
            else:
                print("  ✗ invite_proposals table missing")
            
            # Check invites table columns
            cursor.execute("PRAGMA table_info(invites)")
            invite_columns = [col[1] for col in cursor.fetchall()]
            
            new_columns = ['has_active_proposal', 'current_proposal_id', 'effective_value']
            for col in new_columns:
                if col in invite_columns:
                    print(f"  ✓ invites.{col} column exists")
                else:
                    print(f"  ✗ invites.{col} column missing")
            
            # Check indexes
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
                    print(f"  ✓ Index {idx} exists")
                else:
                    print(f"  ✗ Index {idx} missing")
                    
        except Exception as e:
            print(f"  Error verifying {db_path}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

if __name__ == "__main__":
    print("Starting invite proposals migration...")
    print("=" * 50)
    
    apply_migration()
    
    print("\n" + "=" * 50)
    print("Migration completed. Verifying results...")
    
    verify_migration()
    
    print("\n" + "=" * 50)
    print("Migration process finished.")