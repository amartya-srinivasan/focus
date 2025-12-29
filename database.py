import mysql.connector
from datetime import datetime, timedelta
import hashlib
import os
import time

class Database:
    def __init__(self, config=None):
        # Use provided config or default
        if config:
            self.config = config
        else:
            # Try to load from config file if exists
            config_file = "mysql_config.json"
            if os.path.exists(config_file):
                try:
                    import json
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        self.config = config
                except:
                    self.config = {
                        'host': 'localhost',
                        'user': 'root',
                        'password': '',
                        'database': 'focus_app',
                        'port': 3306,
                        'auth_plugin': 'mysql_native_password'
                    }
            else:
                self.config = {
                    'host': 'localhost',
                    'user': 'root',
                    'password': '',
                    'database': 'focus_app',
                    'port': 3306,
                    'auth_plugin': 'mysql_native_password'
                }
        
        self.connection = None
        self.connect()
        
    def connect(self):
        """Connect to MySQL database with retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"Attempting to connect to MySQL database (attempt {attempt + 1}/{max_retries})...")
                self.connection = mysql.connector.connect(**self.config)
                print("✅ Connected to local MySQL database")
                self.initialize_database()
                return True
            except mysql.connector.Error as err:
                print(f"❌ Database connection error: {err}")
                
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    # Last attempt failed, try to create database
                    print("All connection attempts failed. Trying to create database...")
                    return self.create_database()
                    
        return False
            
    def create_database(self):
        """Create database and tables if they don't exist"""
        try:
            print("Attempting to create database...")
            
            # First, try to connect without database specified
            temp_config = self.config.copy()
            if 'database' in temp_config:
                temp_config.pop('database')
            
            # Try with and without password
            temp_configs_to_try = []
            
            # Try current password
            temp_configs_to_try.append(temp_config)
            
            # Try empty password if current one isn't empty
            if temp_config.get('password', ''):
                temp_config_no_pass = temp_config.copy()
                temp_config_no_pass['password'] = ''
                temp_configs_to_try.append(temp_config_no_pass)
            
            # Try common passwords
            common_passwords = ['password', '123456', 'root', 'admin']
            for common_pass in common_passwords:
                temp_config_common = temp_config.copy()
                temp_config_common['password'] = common_pass
                temp_configs_to_try.append(temp_config_common)
            
            conn = None
            for test_config in temp_configs_to_try:
                try:
                    print(f"Trying connection with password: {'*' * len(test_config.get('password', '')) if test_config.get('password') else '(empty)'}")
                    conn = mysql.connector.connect(**test_config)
                    print(f"✅ Connected with password: {'*' * len(test_config.get('password', '')) if test_config.get('password') else '(empty)'}")
                    break
                except mysql.connector.Error:
                    continue
            
            if not conn:
                print("❌ Could not connect to MySQL with any password. Please check your MySQL installation.")
                print("\nTroubleshooting steps:")
                print("1. Make sure MySQL service is running")
                print("2. Try default MySQL installation credentials:")
                print("   - Username: root")
                print("   - Password: (empty) or 'password' or 'root'")
                print("3. If you set a custom password, edit mysql_config.json")
                return False
            
            cursor = conn.cursor()
            
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS focus_app")
            cursor.execute("USE focus_app")
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create study_sessions table (enhanced for analytics)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    duration_minutes INT,
                    focus_rating INT,  # 1-5 stars
                    subject_tag VARCHAR(50),  # What were you studying?
                    notes TEXT,
                    distractions_count INT DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create blocked_sites table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_sites (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    website VARCHAR(255) NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY unique_user_site (user_id, website)
                )
            """)
            
            # Create todos table for task management
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    task VARCHAR(500) NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create personal_records table for achievements
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personal_records (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    record_type VARCHAR(50) NOT NULL,  # 'longest_session', 'best_focus', etc.
                    record_value FLOAT NOT NULL,
                    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY unique_user_record (user_id, record_type)
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Update config with database name
            self.config['database'] = 'focus_app'
            
            # Now connect to the new database with updated config
            self.connection = mysql.connector.connect(**self.config)
            print("✅ Database and tables created successfully")
            return True
            
        except mysql.connector.Error as err:
            print(f"❌ Error creating database: {err}")
            print("\n⚠️  IMPORTANT: MySQL Setup Required")
            print("=" * 40)
            print("Please ensure MySQL is installed and running.")
            print("\nFor Windows:")
            print("1. Install MySQL from mysql.com or use XAMPP")
            print("2. Start MySQL service")
            print("3. Common default passwords: (empty), 'password', 'root'")
            print("\nThe app will create a 'mysql_config.json' file")
            print("if you need to specify custom credentials.")
            return False
    
    def initialize_database(self):
        """Initialize database by creating tables if they don't exist"""
        cursor = self.connection.cursor()
        
        try:
            # Check if study_sessions table exists
            cursor.execute("SHOW TABLES LIKE 'study_sessions'")
            if not cursor.fetchone():
                # Create all tables
                self.create_database()
            else:
                # Check if study_sessions table has focus_rating column
                cursor.execute("SHOW COLUMNS FROM study_sessions LIKE 'focus_rating'")
                if not cursor.fetchone():
                    # Add focus_rating column if it doesn't exist
                    try:
                        cursor.execute("ALTER TABLE study_sessions ADD COLUMN focus_rating INT")
                        cursor.execute("ALTER TABLE study_sessions ADD COLUMN subject_tag VARCHAR(50)")
                        cursor.execute("ALTER TABLE study_sessions ADD COLUMN distractions_count INT DEFAULT 0")
                        self.connection.commit()
                        print("✅ Added analytics columns to study_sessions table")
                    except mysql.connector.Error as err:
                        print(f"Note: Could not add columns (might already exist): {err}")
                        
        except mysql.connector.Error as err:
            print(f"Error checking tables: {err}")
            # Try to create database
            self.create_database()
            
        cursor.close()
    
    def hash_password(self, password):
        """Hash password for storage"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password):
        """Create a new user"""
        try:
            cursor = self.connection.cursor()
            password_hash = self.hash_password(password)
            
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash)
            )
            self.connection.commit()
            user_id = cursor.lastrowid
            cursor.close()
            return user_id
        except mysql.connector.Error as err:
            print(f"Error creating user: {err}")
            return None
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            password_hash = self.hash_password(password)
            
            cursor.execute(
                "SELECT id, username FROM users WHERE username = %s AND password_hash = %s",
                (username, password_hash)
            )
            user = cursor.fetchone()
            cursor.close()
            return user
        except mysql.connector.Error as err:
            print(f"Error verifying user: {err}")
            return None
    
    def get_user_by_username(self, username):
        """Get user by username"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, username, created_at FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            cursor.close()
            return user
        except mysql.connector.Error as err:
            print(f"Error getting user: {err}")
            return None
    
    def get_all_users(self):
        """Get all users (for login screen)"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id, username FROM users ORDER BY username")
            users = cursor.fetchall()
            cursor.close()
            return users
        except mysql.connector.Error as err:
            print(f"Error getting users: {err}")
            return []
    
    def update_username(self, user_id, new_username):
        """Update username"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE users SET username = %s WHERE id = %s",
                (new_username, user_id)
            )
            self.connection.commit()
            cursor.close()
            return cursor.rowcount > 0
        except mysql.connector.Error as err:
            print(f"Error updating username: {err}")
            return False
    
    def update_password(self, user_id, new_password):
        """Update password"""
        try:
            cursor = self.connection.cursor()
            password_hash = self.hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (password_hash, user_id)
            )
            self.connection.commit()
            cursor.close()
            return cursor.rowcount > 0
        except mysql.connector.Error as err:
            print(f"Error updating password: {err}")
            return False
    
    def delete_user(self, user_id):
        """Delete user and all their data"""
        try:
            cursor = self.connection.cursor()
            
            # Delete in correct order (due to foreign keys)
            cursor.execute("DELETE FROM blocked_sites WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM study_sessions WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM personal_records WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as err:
            print(f"Error deleting user: {err}")
            return False
    
    # Blocked sites management
    def add_blocked_site(self, user_id, website):
        """Add a website to block list"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO blocked_sites (user_id, website) VALUES (%s, %s)",
                (user_id, website)
            )
            self.connection.commit()
            cursor.close()
            return True
        except mysql.connector.Error as err:
            print(f"Error adding blocked site: {err}")
            return False
    
    def get_blocked_sites(self, user_id):
        """Get all blocked sites for a user"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT website FROM blocked_sites WHERE user_id = %s ORDER BY website",
                (user_id,)
            )
            sites = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return sites
        except mysql.connector.Error as err:
            print(f"Error getting blocked sites: {err}")
            return []
    
    def remove_blocked_site(self, user_id, website):
        """Remove a website from block list"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "DELETE FROM blocked_sites WHERE user_id = %s AND website = %s",
                (user_id, website)
            )
            self.connection.commit()
            cursor.close()
            return cursor.rowcount > 0
        except mysql.connector.Error as err:
            print(f"Error removing blocked site: {err}")
            return False
    
    # Study sessions management (enhanced for analytics)
    def record_study_session(self, user_id, duration_minutes, focus_rating=None, subject_tag=None, distractions_count=0, notes=None):
        """Record a study session with analytics data"""
        try:
            cursor = self.connection.cursor()
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            cursor.execute("""
                INSERT INTO study_sessions 
                (user_id, start_time, end_time, duration_minutes, focus_rating, subject_tag, distractions_count, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, start_time, end_time, duration_minutes, focus_rating, subject_tag, distractions_count, notes))
            
            self.connection.commit()
            session_id = cursor.lastrowid
            
            # Update personal records
            self._update_personal_records(user_id, duration_minutes, focus_rating)
            
            cursor.close()
            return session_id
        except mysql.connector.Error as err:
            print(f"Error recording study session: {err}")
            return None
    
    def _update_personal_records(self, user_id, duration_minutes, focus_rating):
        """Update personal records for achievements"""
        try:
            cursor = self.connection.cursor()
            
            # Check for longest session record
            cursor.execute("""
                SELECT record_value FROM personal_records 
                WHERE user_id = %s AND record_type = 'longest_session'
            """, (user_id,))
            result = cursor.fetchone()
            
            if not result or duration_minutes > result[0]:
                # New longest session!
                cursor.execute("""
                    INSERT INTO personal_records (user_id, record_type, record_value)
                    VALUES (%s, 'longest_session', %s)
                    ON DUPLICATE KEY UPDATE record_value = VALUES(record_value)
                """, (user_id, duration_minutes))
            
            # Check for best focus record
            if focus_rating:
                cursor.execute("""
                    SELECT record_value FROM personal_records 
                    WHERE user_id = %s AND record_type = 'best_focus'
                """, (user_id,))
                result = cursor.fetchone()
                
                if not result or focus_rating > result[0]:
                    # New best focus!
                    cursor.execute("""
                        INSERT INTO personal_records (user_id, record_type, record_value)
                        VALUES (%s, 'best_focus', %s)
                        ON DUPLICATE KEY UPDATE record_value = VALUES(record_value)
                    """, (user_id, focus_rating))
            
            self.connection.commit()
            cursor.close()
            
        except mysql.connector.Error as err:
            print(f"Error updating records: {err}")
    
    # Analytics functions (for AnalyticsDashboard.py)
    def get_study_analytics(self, user_id):
        """Get comprehensive study analytics for dashboard"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            analytics = {}
            
            # Today's date and 30 days ago
            today = datetime.now().date()
            thirty_days_ago = today - timedelta(days=30)
            
            # Weekly study time (last 4 weeks)
            cursor.execute("""
                SELECT 
                    YEAR(start_time) as year,
                    WEEK(start_time) as week,
                    SUM(duration_minutes) as total_minutes,
                    COUNT(*) as session_count,
                    AVG(focus_rating) as avg_focus
                FROM study_sessions 
                WHERE user_id = %s 
                GROUP BY YEAR(start_time), WEEK(start_time)
                ORDER BY year DESC, week DESC
                LIMIT 4
            """, (user_id,))
            analytics['weekly_data'] = cursor.fetchall()
            
            # Daily study time for last 7 days
            cursor.execute("""
                SELECT 
                    DATE(start_time) as date,
                    SUM(duration_minutes) as daily_minutes,
                    COUNT(*) as sessions,
                    AVG(focus_rating) as avg_focus
                FROM study_sessions 
                WHERE user_id = %s AND DATE(start_time) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(start_time)
                ORDER BY date DESC
            """, (user_id,))
            analytics['daily_data'] = cursor.fetchall()
            
            # Personal records
            cursor.execute("""
                SELECT 
                    MAX(duration_minutes) as longest_session,
                    AVG(duration_minutes) as avg_session_length,
                    SUM(duration_minutes) as total_study_time,
                    COUNT(*) as total_sessions,
                    MAX(focus_rating) as best_focus,
                    AVG(focus_rating) as avg_focus_lifetime
                FROM study_sessions 
                WHERE user_id = %s
            """, (user_id,))
            analytics['records'] = cursor.fetchone()
            
            # Most productive day of week
            cursor.execute("""
                SELECT 
                    DAYNAME(start_time) as day_name,
                    AVG(duration_minutes) as avg_minutes,
                    COUNT(*) as session_count
                FROM study_sessions 
                WHERE user_id = %s
                GROUP BY DAYNAME(start_time)
                ORDER BY avg_minutes DESC
                LIMIT 1
            """, (user_id,))
            analytics['best_day'] = cursor.fetchone()
            
            # Subject/tag analysis
            cursor.execute("""
                SELECT 
                    subject_tag,
                    SUM(duration_minutes) as total_time,
                    COUNT(*) as session_count,
                    AVG(focus_rating) as avg_focus
                FROM study_sessions 
                WHERE user_id = %s AND subject_tag IS NOT NULL AND subject_tag != ''
                GROUP BY subject_tag
                ORDER BY total_time DESC
                LIMIT 5
            """, (user_id,))
            analytics['subjects'] = cursor.fetchall()
            
            # Get actual personal records from personal_records table
            cursor.execute("""
                SELECT record_type, record_value, achieved_at 
                FROM personal_records 
                WHERE user_id = %s
            """, (user_id,))
            analytics['personal_records'] = cursor.fetchall()
            
            cursor.close()
            return analytics
            
        except mysql.connector.Error as err:
            print(f"Error getting analytics: {err}")
            return None
    
    def get_recent_sessions(self, user_id, limit=10):
        """Get recent study sessions"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    start_time, duration_minutes, focus_rating, subject_tag, notes
                FROM study_sessions 
                WHERE user_id = %s 
                ORDER BY start_time DESC 
                LIMIT %s
            """, (user_id, limit))
            sessions = cursor.fetchall()
            cursor.close()
            return sessions
        except mysql.connector.Error as err:
            print(f"Error getting recent sessions: {err}")
            return []
    
    def get_study_time_by_period(self, user_id, days=30):
        """Get study time for a specific period"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT SUM(duration_minutes) 
                FROM study_sessions 
                WHERE user_id = %s AND start_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (user_id, days))
            result = cursor.fetchone()
            cursor.close()
            return result[0] or 0
        except mysql.connector.Error as err:
            print(f"Error getting study time: {err}")
            return 0


    def get_todos(self, user_id):
        """Get all todos for a user"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, task, completed 
                FROM todos 
                WHERE user_id = %s 
                ORDER BY created_at ASC
            """, (user_id,))
            todos = cursor.fetchall()
            cursor.close()
            return todos
        except Exception as err:
            print(f"Error getting todos: {err}")
            return []
    
    def save_todos(self, user_id, todos):
        """Save todos for a user (replaces all existing todos)"""
        try:
            cursor = self.connection.cursor()
            
            # Delete existing todos for this user
            cursor.execute("DELETE FROM todos WHERE user_id = %s", (user_id,))
            
            # Insert new todos
            for task, completed in todos:
                cursor.execute("""
                    INSERT INTO todos (user_id, task, completed) 
                    VALUES (%s, %s, %s)
                """, (user_id, task, completed))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except Exception as err:
            print(f"Error saving todos: {err}")
            self.connection.rollback()
            return False
