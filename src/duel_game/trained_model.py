import sqlite3
import json
from typing import List, Optional, Tuple
from enum import IntEnum
import numpy as np
from sklearn.linear_model import LogisticRegression
from datetime import datetime

from essential_types import Action


class ModelRepository:
    def __init__(self, db_path: str = "../../data/database.sqlite"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database with models table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create models table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                weights_json TEXT NOT NULL,
                accuracy REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (run_id)
                    REFERENCES dataset_run(id)
                    ON DELETE CASCADE
            );
            """)
            
            # Add unique constraint to prevent multiple models per run
            cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_models_run_id 
            ON models(run_id);
            """)
            
            conn.commit()
    
    def save_model(self, run_id: int, weights: List[float], accuracy: Optional[float] = None) -> int:
        """
        Save model weights to database
        Returns the model ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Convert weights to JSON string
            weights_json = json.dumps([float(w) for w in weights])
            
            # Insert or replace (to update existing model for this run)
            cursor.execute("""
            INSERT OR REPLACE INTO models 
            (id, run_id, weights_json, accuracy, created_at)
            VALUES (
                COALESCE((SELECT id FROM models WHERE run_id = ?), NULL),
                ?, ?, ?, CURRENT_TIMESTAMP
            )
            """, (run_id, run_id, weights_json, accuracy))
            
            model_id = cursor.lastrowid
            
            # If updating, we need to get the existing ID
            if model_id is None:
                cursor.execute("SELECT id FROM models WHERE run_id = ?", (run_id,))
                model_id = cursor.fetchone()[0]
            
            conn.commit()
            return model_id
    
    def get_model(self, run_id: int) -> Optional[dict]:
        """Retrieve model by run_id"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT id, run_id, weights_json, accuracy, created_at
            FROM models WHERE run_id = ?
            """, (run_id,))
            
            row = cursor.fetchone()
            if row:
                weights = json.loads(row['weights_json'])
                return {
                    'id': row['id'],
                    'run_id': row['run_id'],
                    'weights': weights,
                    'accuracy': row['accuracy'],
                    'created_at': row['created_at']
                }
            return None
    
    def get_all_models(self) -> List[dict]:
        """Get all models in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT id, run_id, weights_json, accuracy, created_at
            FROM models ORDER BY created_at DESC
            """)
            
            models = []
            for row in cursor.fetchall():
                models.append({
                    'id': row['id'],
                    'run_id': row['run_id'],
                    'weights': json.loads(row['weights_json']),
                    'accuracy': row['accuracy'],
                    'created_at': row['created_at']
                })
            return models
    
    def delete_model(self, run_id: int) -> bool:
        """Delete model by run_id"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM models WHERE run_id = ?", (run_id,))
            conn.commit()
            return cursor.rowcount > 0
        