import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from essential_types import DataSample

class DatasetRepository:
    def __init__(self, db_path: str = "database.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        # IMPORTANT: enable foreign key enforcement in SQLite
        self.conn.execute("PRAGMA foreign_keys = ON;")

        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()

        # ----------------------------
        # CONFIG TEMPLATE TABLE
        # ----------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_template (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_version INTEGER NOT NULL,
            version INTEGER NOT NULL,
            label TEXT NOT NULL,
            config_hash TEXT NOT NULL UNIQUE,
            config_json TEXT NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # ----------------------------
        # DATASET RUN TABLE
        # ----------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dataset_run (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            run_index TEXT NOT NULL,
            sample_count INTEGER NOT NULL DEFAULT 0,
            seed INTEGER NOT NULL,
            label TEXT,
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (template_id)
                REFERENCES config_template(id)
                ON DELETE CASCADE
        );
        """)

        # ----------------------------
        # SAMPLES TABLE
        # ----------------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            features_json TEXT NOT NULL,
            label INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (run_id)
                REFERENCES dataset_run(id)
                ON DELETE CASCADE
        );
        """)

        # ----------------------------
        # INDEXES (CRITICAL FOR SCALE)
        # ----------------------------
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_run_template_id
        ON dataset_run(template_id);
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_samples_run_id
        ON samples(run_id);
        """)

        self.conn.commit()

    def _generate_config_hash(self, config_json: str) -> str:
        """Generate a hash for the configuration JSON."""
        return hashlib.sha256(config_json.encode()).hexdigest()

    def create_config_template(self, config_json: str, app_version: int, label: str, description: str = "") -> int:
        """
        Create a new configuration template.
        
        Args:
            config_json: JSON string of the configuration
            app_version: specific App Version Number
            label: Label of the template
            description: Optional description
            
        Returns:
            The ID of the created template
        """
        config_hash = self._generate_config_hash(config_json)
        config_version = self.get_new_template_version_number(app_version)

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO config_template (app_version, version, label, config_hash, config_json, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (app_version, config_version, label, config_hash, config_json, description))
        
        self.conn.commit()
        return cursor.lastrowid

    def get_config_template(self, template_id: int) -> Dict[str, Any]:
        """
        Retrieve a configuration template by ID.
        
        Args:
            template_id: The ID of the template to retrieve
            
        Returns:
            Dictionary with template data
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, app_version, version, label, config_hash, config_json, description, created_at
            FROM config_template
            WHERE id = ?
        """, (template_id,))
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Template with ID {template_id} not found")
        
        return {
            'id': row['id'],
            'app_version': row['app_version'],
            'version': row['version'],
            'label': row['label'],
            'config_hash': row['config_hash'],
            'config_json': json.loads(row['config_json']),
            'description': row['description'],
            'created_at': row['created_at']
        }

    def is_config_available_given_hash(self, config_hash: str) -> Optional[int]:
        """
        Check if a configuration with the given hash already exists.
        
        Args:
            config_hash: The hash to check
            
        Returns:
            Template ID if found, None otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id FROM config_template WHERE config_hash = ?
        """, (config_hash,))
        
        row = cursor.fetchone()
        return row['id'] if row else None

    def get_new_template_version_number(self, app_version):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT MAX(version) as max_version_number
            FROM config_template
            WHERE app_version = ?
        """, (app_version, ))

        row = cursor.fetchone()
        last_version_number = row['max_version_number'] if row['max_version_number'] is not None else 0

        return last_version_number + 1


    def get_new_run_version_number_given_template_id(self, template_id: int) -> int:
        """
        Get the next run index for a given template.
        
        Args:
            template_id: The template ID
            
        Returns:
            The next run index (starting from 0 if no runs exist)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as max_index
            FROM dataset_run
            WHERE template_id = ?
        """, (template_id,))
        
        row = cursor.fetchone()
        max_index = row['max_index'] if row['max_index'] is not None else 0
        return int(max_index) + 1

    def create_run(self, template_id: int, label: str, samples_count: int, 
                  seed: int, note: str = "") -> int:
        """
        Create a new dataset run.
        
        Args:
            template_id: The template ID to associate with
            label: Label for this run
            samples_count: Expected number of samples
            seed: Random seed used for this run
            note: Optional note
            
        Returns:
            The ID of the created run
        """
        config_template = self.get_config_template(template_id)
        app_version = config_template['app_version']
        template_version = config_template['version']

        # Get the next run number
        run_number = self.get_new_run_version_number_given_template_id(template_id)
        run_index = f'{app_version}.{template_version}.{run_number}'
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO dataset_run (template_id, run_index, sample_count, seed, label, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (template_id, run_index, samples_count, seed, label, note))
        
        self.conn.commit()
        return cursor.lastrowid

    def set_samples_count_for_run(self, run_id, samples_count):
        """
        Update the sample_count for a specific dataset run.
        
        Args:
            run_id (int): The ID of the dataset run to update
            samples_count (int): The new sample count value (must be non-negative)
        
        Returns:
            bool: True if update was successful, False otherwise
        
        Raises:
            ValueError: If samples_count is negative
            TypeError: If run_id or samples_count are not integers
        """
        # Input validation
        if not isinstance(run_id, int):
            raise TypeError(f"run_id must be an integer, got {type(run_id).__name__}")
        
        if not isinstance(samples_count, int):
            raise TypeError(f"samples_count must be an integer, got {type(samples_count).__name__}")
        
        if samples_count < 0:
            raise ValueError(f"samples_count must be non-negative, got {samples_count}")
        
        # If run_id doesn't exist, we can handle it gracefully or raise error
        if run_id <= 0:
            raise ValueError(f"run_id must be positive, got {run_id}")
        
        try:
            # Use parameterized query to prevent SQL injection
            cursor = self.conn.cursor()
            
            # First check if the run exists
            cursor.execute("""
                SELECT id FROM dataset_run WHERE id = ?
            """, (run_id,))
            
            if not cursor.fetchone():
                # Option 1: Log warning and return False
                print(f"Warning: Run with ID {run_id} not found")
                return False
                
                # Option 2: Raise an exception (uncomment if preferred)
                # raise ValueError(f"Run with ID {run_id} not found")
            
            # Update the sample count
            cursor.execute("""
                UPDATE dataset_run 
                SET sample_count = ?
                WHERE id = ?
            """, (samples_count, run_id))
            
            # Check if any row was actually updated
            if cursor.rowcount == 0:
                print(f"Warning: No rows updated for run_id {run_id}")
                return False
            
            # Commit the transaction
            self.conn.commit()
            
            # Verify the update (optional but good for debugging)
            cursor.execute("""
                SELECT sample_count FROM dataset_run WHERE id = ?
            """, (run_id,))
            
            updated_value = cursor.fetchone()[0]
            if updated_value == samples_count:
                print(f"Successfully updated run {run_id} sample_count to {samples_count}")
                return True
            else:
                print(f"Warning: Update may have failed. Expected {samples_count}, got {updated_value}")
                return False
                
        except sqlite3.Error as e:
            # Rollback in case of error
            self.conn.rollback()
            print(f"Database error occurred: {e}")
            return False
        
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Unexpected error occurred: {e}")
            return False

    def get_run_samples(self, run_id: int) -> List[Dict[str, Any]]:
        """
        Get all samples for a specific run.
        
        Args:
            run_id: The run ID
            
        Returns:
            List of sample dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, features_json, label, created_at
            FROM samples
            WHERE run_id = ?
            ORDER BY id
        """, (run_id,))
        
        samples = []
        for row in cursor.fetchall():
            samples.append({
                'id': row['id'],
                'features': json.loads(row['features_json']),
                'label': row['label'],
                'created_at': row['created_at']
            })
        
        return samples

    def store_sample(self, features: List[float], label: int, run_id: int) -> int:
        """
        Create a single sample.
        
        Args:
            features: Dictionary of feature names to values
            label: The label (0 or 1, or other integer)
            run_id: The run ID to associate with
            
        Returns:
            The ID of the created sample
        """
        features_json = json.dumps(features)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO samples (run_id, features_json, label)
            VALUES (?, ?, ?)
        """, (run_id, features_json, label))
        
        self.conn.commit()
        return cursor.lastrowid

    def store_samples(self, samples: List[DataSample], run_id: int) -> List[int]:
        """
        Create multiple samples in a batch.
        
        Args:
            samples: List of dictionaries, each with 'features' and 'label' keys
            run_id: The run ID to associate with
            
        Returns:
            List of created sample IDs
            
        Example:
            samples = [
                {'features': {'hp': 0.8, 'stamina': 0.6}, 'label': 1},
                {'features': {'hp': 0.3, 'stamina': 0.9}, 'label': 0},
            ]
        """
        if not samples:
            return []
        
        cursor = self.conn.cursor()
        sample_ids = []
        
        # Batch insert for efficiency
        for sample in samples:
            features_json = json.dumps(sample.features)
            label = sample.label.value
            
            cursor.execute( """
                INSERT INTO samples (run_id, features_json, label)
                VALUES (?, ?, ?)
            """, (run_id, features_json, label))
            
            sample_ids.append(cursor.lastrowid)
        
        self.conn.commit()
        return sample_ids

    def get_run_info(self, run_id: int) -> Dict[str, Any]:
        """
        Get information about a specific run.
        
        Args:
            run_id: The run ID
            
        Returns:
            Dictionary with run information
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT dr.id, dr.template_id, dr.run_index, dr.sample_count, 
                   dr.seed, dr.label, dr.note, dr.created_at,
                   ct.label as template_label
            FROM dataset_run dr
            JOIN config_template ct ON dr.template_id = ct.id
            WHERE dr.id = ?
        """, (run_id,))
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Run with ID {run_id} not found")
        
        return {
            'id': row['id'],
            'template_id': row['template_id'],
            'template_label': row['template_label'],
            'run_index': row['run_index'],
            'sample_count': row['sample_count'],
            'seed': row['seed'],
            'label': row['label'],
            'note': row['note'],
            'created_at': row['created_at']
        }

    def get_all_runs_for_template(self, template_id: int) -> List[Dict[str, Any]]:
        """
        Get all runs for a specific template.
        
        Args:
            template_id: The template ID
            
        Returns:
            List of run dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, run_index, sample_count, seed, label, note, created_at
            FROM dataset_run
            WHERE template_id = ?
            ORDER BY run_index
        """, (template_id,))
        
        runs = []
        for row in cursor.fetchall():
            runs.append({
                'id': row['id'],
                'run_index': row['run_index'],
                'sample_count': row['sample_count'],
                'seed': row['seed'],
                'label': row['label'],
                'note': row['note'],
                'created_at': row['created_at']
            })
        
        return runs

    def update_sample_count(self, run_id: int, new_count: int) -> None:
        """
        Update the sample count for a run.
        
        Args:
            run_id: The run ID
            new_count: New sample count
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE dataset_run
            SET sample_count = ?
            WHERE id = ?
        """, (new_count, run_id))
        
        self.conn.commit()

    def delete_run(self, run_id: int) -> bool:
        """
        Delete a run and all its samples (cascading delete).
        
        Args:
            run_id: The run ID
            
        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM dataset_run WHERE id = ?", (run_id,))
        deleted = cursor.rowcount > 0
        
        self.conn.commit()
        return deleted

    def get_sample_statistics(self, run_id: int) -> Dict[str, Any]:
        """
        Get statistics about samples in a run.
        
        Args:
            run_id: The run ID
            
        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()
        
        # Count samples by label
        cursor.execute("""
            SELECT label, COUNT(*) as count
            FROM samples
            WHERE run_id = ?
            GROUP BY label
        """, (run_id,))
        
        label_counts = {}
        total_samples = 0
        for row in cursor.fetchall():
            label_counts[row['label']] = row['count']
            total_samples += row['count']
        
        # Get date range
        cursor.execute("""
            SELECT MIN(created_at) as first_sample, MAX(created_at) as last_sample
            FROM samples
            WHERE run_id = ?
        """, (run_id,))
        
        date_row = cursor.fetchone()
        
        return {
            'total_samples': total_samples,
            'label_distribution': label_counts,
            'first_sample': date_row['first_sample'],
            'last_sample': date_row['last_sample']
        }

    def search_config_templates(self, label_pattern: str = None) -> List[Dict[str, Any]]:
        """
        Search for configuration templates by label.
        
        Args:
            label_pattern: SQL LIKE pattern for label search
            
        Returns:
            List of matching templates
        """
        cursor = self.conn.cursor()
        
        if label_pattern:
            cursor.execute("""
                SELECT id, label, config_hash, description, created_at
                FROM config_template
                WHERE label LIKE ?
                ORDER BY created_at DESC
            """, (f"%{label_pattern}%",))
        else:
            cursor.execute("""
                SELECT id, label, config_hash, description, created_at
                FROM config_template
                ORDER BY created_at DESC
            """)
        
        templates = []
        for row in cursor.fetchall():
            templates.append({
                'id': row['id'],
                'label': row['label'],
                'config_hash': row['config_hash'],
                'description': row['description'],
                'created_at': row['created_at']
            })
        
        return templates

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print('database connection has closed')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()