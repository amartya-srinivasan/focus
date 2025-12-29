import hashlib
from tkinter import simpledialog, messagebox, Tk
from database import db

USER_FILE = "user_data.txt"  # We'll keep this for migration

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_account(root):
    """Create new account in MySQL database"""
    while True:
        username = simpledialog.askstring("Create Account", "Choose a username:", parent=root)
        if not username:
            return None
            
        # Check if username already exists
        if db.user_exists(username):
            messagebox.showerror("Error", "Username already exists. Choose a different one.", parent=root)
            continue
            
        pwd1 = simpledialog.askstring("Create Password", "Enter a new password:", show='*', parent=root)
        if not pwd1:
            return None
            
        pwd2 = simpledialog.askstring("Confirm Password", "Confirm your password:", show='*', parent=root)
        if pwd1 != pwd2:
            messagebox.showerror("Error", "Passwords do not match. Try again.", parent=root)
        else:
            # Create user in database
            user_id = db.create_user(username, pwd1)
            if user_id:
                messagebox.showinfo("Success", "Account created successfully!", parent=root)
                return {"id": user_id, "username": username}
            else:
                messagebox.showerror("Error", "Failed to create account. Please try again.", parent=root)
                return None

def verify_password(root):
    """Verify user against MySQL database"""
    # First, check if we need to migrate from file-based system
    migrate_from_file()
    
    # Check if any users exist in database
    if not db.user_exists():
        return create_account(root)

    username = simpledialog.askstring("Login", "Enter your username:", parent=root)
    if not username:
        return None
        
    password = simpledialog.askstring("Login", "Enter your password:", show='*', parent=root)
    if not password:
        return None
        
    user_data = db.verify_user(username, password)
    if user_data:
        return user_data
    else:
        messagebox.showerror("Error", "Invalid username or password!", parent=root)
        return None

def migrate_from_file():
    """Migrate from file-based authentication to database"""
    import os
    import json
    
    if os.path.exists(USER_FILE) and not db.user_exists():
        try:
            with open(USER_FILE, 'r') as f:
                content = f.read().strip()
                
            # Try to parse as JSON (new format)
            try:
                user_data = json.loads(content)
                username = user_data.get('username', 'User')
                password_hash = user_data.get('password_hash', '')
                
                # Create user in database
                if username and password_hash:
                    # We can't recover the password, so create with default password
                    db.create_user(username, "password123")
                    print("✅ Migrated user from file to database")
                    
            except json.JSONDecodeError:
                # Old format - just the password hash
                password_hash = content
                db.create_user("User", "password123")
                print("✅ Migrated user from old file format to database")
                
            # Backup the old file
            os.rename(USER_FILE, USER_FILE + ".backup")
            
        except Exception as e:
            print(f"❌ Error migrating from file: {e}")
