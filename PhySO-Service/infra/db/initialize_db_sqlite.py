#!/usr/bin/env python3
"""
SQLite версия инициализации базы данных для быстрого тестирования
"""
import sqlite3
import os
import sys
import json

# Добавляем путь к проекту
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Путь к базе данных SQLite
DB_PATH = os.path.join(project_root, "physo_billing.db")

def initialize_sqlite_database():
    """Инициализация SQLite базы данных"""
    print(f"Создание SQLite базы данных: {DB_PATH}")
    
    # Удаляем старую базу если есть
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Старая база данных удалена")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Создание таблиц...")
        
        # users table
        cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            telegram_id TEXT UNIQUE,
            balance REAL DEFAULT 0.0 NOT NULL,
            password_hash TEXT,
            api_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Создана таблица 'users'")
        
        # models table (PhySO configurations)
        cursor.execute("""
        CREATE TABLE models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            base_price REAL NOT NULL DEFAULT 0.0,
            epoch_price REAL NOT NULL DEFAULT 0.0,
            is_active BOOLEAN DEFAULT 1
        );
        """)
        print("Создана таблица 'models'")
        
        # predictions table (PhySO predictions)
        cursor.execute("""
        CREATE TABLE predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            model_id INTEGER NOT NULL,
            -- Input data and parameters
            input_data TEXT NOT NULL,
            y_name TEXT DEFAULT 'y',
            x_names TEXT,  -- JSON array as text
            epochs INTEGER DEFAULT 50,
            op_names TEXT,  -- JSON array as text
            free_consts_names TEXT,  -- JSON array as text
            run_config TEXT DEFAULT 'config0',
            stop_reward REAL DEFAULT 0.999,
            parallel_mode BOOLEAN DEFAULT 0,
            -- Results
            best_formula TEXT,
            best_r2 REAL,
            pareto_count INTEGER DEFAULT 0,
            metadata TEXT,  -- JSON as text
            total_cost REAL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            queue_time INTEGER,
            process_time INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE RESTRICT
        );
        """)
        print("Создана таблица 'predictions'")
        
        # transactions table
        cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            prediction_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE SET NULL
        );
        """)
        print("Создана таблица 'transactions'")
        
        # Создание индексов
        print("Создание индексов...")
        cursor.execute("CREATE INDEX idx_users_telegram_id ON users(telegram_id);")
        cursor.execute("CREATE INDEX idx_users_api_key ON users(api_key);")
        cursor.execute("CREATE INDEX idx_models_name ON models(name);")
        cursor.execute("CREATE INDEX idx_predictions_uuid ON predictions(uuid);")
        cursor.execute("CREATE INDEX idx_predictions_user_id ON predictions(user_id);")
        cursor.execute("CREATE INDEX idx_transactions_user_id ON transactions(user_id);")
        print("Индексы созданы")
        
        # Добавление PhySO конфигураций
        print("Добавление PhySO конфигураций...")
        physo_configs = [
            ('config0', 'Basic PhySO configuration', 0.01, 0.001),
            ('config1', 'Extended PhySO configuration', 0.02, 0.002),
            ('config2', 'Advanced PhySO configuration', 0.03, 0.003)
        ]
        
        for name, description, base_price, epoch_price in physo_configs:
            cursor.execute("""
                INSERT INTO models (name, description, base_price, epoch_price, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (name, description, base_price, epoch_price))
            print(f"Добавлена конфигурация '{name}'")
        
        # Добавление тестового пользователя
        print("Добавление тестового пользователя...")
        cursor.execute("""
            INSERT INTO users (name, balance, api_key)
            VALUES ('admin', 10.0, 'test-api-key-123')
        """)
        print("Добавлен пользователь 'admin' с балансом $10.00 и API ключом 'test-api-key-123'")
        
        conn.commit()
        print("✅ SQLite база данных успешно инициализирована!")
        print(f"📍 Путь к базе: {DB_PATH}")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_sqlite_connection():
    """Получение подключения к SQLite базе"""
    return sqlite3.connect(DB_PATH)

if __name__ == "__main__":
    initialize_sqlite_database()
