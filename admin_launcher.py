import os
import sys
import ctypes
import subprocess

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relaunch the script with administrator privileges."""
    try:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        
        # Use ShellExecute to run as admin
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        return True
    except Exception as e:
        print(f"Failed to run as admin: {e}")
        return False

def main():
    """Main launcher that ensures admin rights"""
    if not is_admin():
        print("Not running as administrator. Requesting admin privileges...")
        if run_as_admin():
            print("Relaunching with admin rights...")
            sys.exit(0)
        else:
            print("Failed to get admin rights. Some features may not work.")
            # Continue anyway but show warning
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "Admin Rights Required",
                "Website blocking requires administrator privileges.\n\n"
                "The application will continue, but website blocking may not work.\n"
                "To enable blocking, please run as Administrator."
            )
            root.destroy()
    
    # Run main.py as subprocess (includes login at startup!)
    try:
        import subprocess
        subprocess.run([sys.executable, "main.py"])
    except Exception as e:
        print(f"Error launching main application: {e}")
        input("Press Enter to exit...")
    finally:
        # Cleanup session files when app truly exits
        import os
        if os.path.exists("session_active.flag"):
            os.remove("session_active.flag")
            print("✓ App closed - cleaned up session")
        if os.path.exists("current_user.txt"):
            os.remove("current_user.txt")
            print("✓ Logged out")

if __name__ == "__main__":
    main()