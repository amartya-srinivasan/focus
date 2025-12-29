import os
import subprocess
import tempfile
import ctypes
import sys
import time

class WebsiteBlocker:
    def __init__(self):
        self.hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        self.blocked_file = "blocked_sites.txt"
        self.redirect_ip = "0.0.0.0"
        self.is_admin = self.check_admin()
        print(f"🔧 WebsiteBlocker initialized - Admin: {self.is_admin}")
        
    def check_admin(self):
        """Check if running as administrator"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def request_admin(self):
        """Request administrator privileges"""
        if not self.is_admin:
            print("🛑 Administrator privileges required for website blocking")
            print("💡 Please run the program as Administrator")
            return False
        return True
    
    def write_to_hosts_file(self, content):
        """Write content to hosts file with admin privileges"""
        try:
            print(f"📝 Attempting to write to hosts file: {self.hosts_path}")
            
            # Method 1: Direct write with admin rights
            try:
                with open(self.hosts_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("✅ Successfully wrote to hosts file directly")
                return True
            except PermissionError:
                print("❌ Direct write failed - no permission")
            
            # Method 2: Use subprocess with admin rights
            try:
                # Create temporary file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                
                print(f"📄 Created temp file: {temp_path}")
                
                # Use subprocess to copy with admin rights
                copy_cmd = ['cmd', '/c', 'copy', temp_path, self.hosts_path, '/Y']
                result = subprocess.run(copy_cmd, capture_output=True, text=True, timeout=10)
                
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
                if result.returncode == 0:
                    print("✅ Successfully copied to hosts file")
                    return True
                else:
                    print(f"❌ Copy failed: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"❌ Subprocess copy failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error writing to hosts file: {e}")
            return False
    
    def get_blocked_sites(self):
        """Get list of sites to block"""
        print(f"📁 Looking for blocked_sites.txt in: {os.getcwd()}")
        print(f"📁 File exists: {os.path.exists(self.blocked_file)}")
        
        if not os.path.exists(self.blocked_file):
            print("❌ blocked_sites.txt not found!")
            return []
        
        try:
            with open(self.blocked_file, 'r') as f:
                sites = [line.strip() for line in f.readlines() if line.strip()]
            print(f"📋 Read {len(sites)} sites from blocked_sites.txt: {sites}")
            return sites
        except Exception as e:
            print(f"❌ Error reading blocked sites: {e}")
            return []
    
    def get_comprehensive_blocks(self, site):
        """Get comprehensive blocking entries for a site"""
        blocks = []
        
        # Base domains
        base_domains = [
            site,
            f"www.{site}",
            f"m.{site}",
            f"mobile.{site}",
        ]
        
        for domain in base_domains:
            blocks.append(f"{self.redirect_ip} {domain}")
        
        # YouTube-specific blocks (most common issue)
        if "youtube" in site.lower():
            youtube_domains = [
                "youtube.com", "www.youtube.com", "m.youtube.com",
                "youtu.be", "www.youtu.be",
                "googlevideo.com", "www.googlevideo.com",  # Video hosting
                "ytimg.com", "www.ytimg.com",  # Thumbnails
                "google.com", "www.google.com",  # Sometimes needed
                "gstatic.com",  # Google static content
                "ggpht.com",  # Google photos
            ]
            for domain in youtube_domains:
                blocks.append(f"{self.redirect_ip} {domain}")
        
        # Other common sites
        elif "netflix" in site.lower():
            netflix_domains = ["netflix.com", "www.netflix.com", "nflxso.net", "nflxext.com"]
            for domain in netflix_domains:
                blocks.append(f"{self.redirect_ip} {domain}")
        
        elif "facebook" in site.lower():
            facebook_domains = ["facebook.com", "www.facebook.com", "fb.com", "fbcdn.net"]
            for domain in facebook_domains:
                blocks.append(f"{self.redirect_ip} {domain}")
        
        return blocks

    def disable_dns_over_https(self):
        """Disable DNS over HTTPS in Windows"""
        try:
            print("🛑 Disabling DNS over HTTPS...")
            
            # Disable DoH via registry
            reg_commands = [
                'reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Dnscache\\Parameters" /v EnableAutoDoh /t REG_DWORD /d 0 /f',
                'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" /v DoHPolicy /t REG_DWORD /d 0 /f',
            ]
            
            for cmd in reg_commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Registry command executed: {cmd}")
                else:
                    print(f"⚠️ Registry command failed (may not exist): {cmd}")
                    
        except Exception as e:
            print(f"❌ Error disabling DoH: {e}")

    def flush_dns_comprehensive(self):
        """Comprehensive DNS flushing"""
        try:
            print("🔄 Performing comprehensive DNS flush...")
            
            # Stop DNS client service
            subprocess.run(["net", "stop", "dnscache"], capture_output=True)
            time.sleep(2)
            
            # Start DNS client service  
            subprocess.run(["net", "start", "dnscache"], capture_output=True)
            time.sleep(1)
            
            # Flush DNS
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
            
            # Additional DNS cache clearing
            subprocess.run(["nbtstat", "-R"], capture_output=True)
            subprocess.run(["nbtstat", "-RR"], capture_output=True)
            
            print("✅ Comprehensive DNS flush completed")
            
        except Exception as e:
            print(f"❌ DNS flush error: {e}")

    def disable_browser_doh(self):
        """Disable DNS over HTTPS in major browsers"""
        print("🛑 Disabling DNS over HTTPS in browsers...")
        
        try:
            # Chrome/Edge - disable DoH via registry
            chrome_doh_disable = [
                'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Google\\Chrome" /v DnsOverHttpsMode /t REG_SZ /d "off" /f',
                'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Edge" /v DnsOverHttpsMode /t REG_SZ /d "off" /f',
            ]
            
            for cmd in chrome_doh_disable:
                subprocess.run(cmd, shell=True, capture_output=True)
            
            print("✅ Browser DoH disabled")
            
        except Exception as e:
            print(f"⚠️ Could not disable browser DoH: {e}")

    def test_blocking(self):
        """Test if blocking is actually working"""
        print("🧪 Testing if blocking is working...")
        
        # Test DNS resolution
        test_sites = ["youtube.com", "www.youtube.com"]
        
        for site in test_sites:
            try:
                result = subprocess.run(
                    ["nslookup", site], 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                
                if "0.0.0.0" in result.stdout:
                    print(f"✅ {site} is correctly blocked (resolves to 0.0.0.0)")
                else:
                    print(f"❌ {site} is NOT blocked - resolves to actual IP")
                    print(f"   Output: {result.stdout}")
                    
            except Exception as e:
                print(f"❌ Error testing {site}: {e}")

    def block_websites(self):
        """Block all websites in the list"""
        print("🚀 WEBSITE BLOCKER: Starting comprehensive blocking...")
        
        if not self.request_admin():
            return False
        
        sites = self.get_blocked_sites()
        if not sites:
            return True
        
        try:
            # Disable DNS over HTTPS first
            self.disable_dns_over_https()
            
            # Read current hosts file
            current_content = ""
            if os.path.exists(self.hosts_path):
                with open(self.hosts_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
            
            # Create comprehensive blocking entries
            blocking_entries = []
            blocking_entries.append("\n# Focus Timer Blocked Sites - DO NOT EDIT")
            
            for site in sites:
                # Add comprehensive blocking for each site
                site_blocks = self.get_comprehensive_blocks(site)
                blocking_entries.extend(site_blocks)
            
            blocking_entries.append("# End Focus Timer Blocked Sites\n")
            
            # Remove existing block section
            lines = current_content.splitlines()
            new_lines = []
            in_block_section = False
            
            for line in lines:
                if "# Focus Timer Blocked Sites - DO NOT EDIT" in line:
                    in_block_section = True
                    continue
                if "# End Focus Timer Blocked Sites" in line:
                    in_block_section = False
                    continue
                if not in_block_section and line.strip():
                    new_lines.append(line)
            
            # Build new content
            new_content = "\n".join(new_lines).strip()
            if new_content:
                new_content += "\n"
            new_content += "\n".join(blocking_entries)
            
            # Write to hosts file
            success = self.write_to_hosts_file(new_content)
            
            if success:
                self.flush_dns_comprehensive()
                self.disable_browser_doh()  # NEW: Disable DoH in browsers
                self.test_blocking()  # Test if it's working
                print("✅ Comprehensive website blocking activated!")
                return True
            else:
                print("❌ Failed to block websites")
                return False
                
        except Exception as e:
            print(f"❌ Blocking error: {e}")
            return False

    def unblock_websites(self):
        """Remove all blocking entries"""
        print("🚀 Starting website unblocking...")
        
        if not self.request_admin():
            return False
        
        try:
            if not os.path.exists(self.hosts_path):
                print("ℹ️ Hosts file doesn't exist, nothing to unblock")
                return True
            
            # Read current hosts
            with open(self.hosts_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Remove Focus Timer block section
            new_lines = []
            in_block_section = False
            removed_section = False
            
            for line in lines:
                if "# Focus Timer Blocked Sites - DO NOT EDIT" in line:
                    in_block_section = True
                    removed_section = True
                    continue
                if "# End Focus Timer Blocked Sites" in line:
                    in_block_section = False
                    continue
                if not in_block_section:
                    new_lines.append(line)
            
            new_content = "".join(new_lines).strip()
            
            print("📄 Writing cleaned hosts file...")
            success = self.write_to_hosts_file(new_content)
            
            if success:
                self.flush_dns_comprehensive()
                if removed_section:
                    print("✅ Websites unblocked successfully!")
                else:
                    print("ℹ️ No blocking section found to remove")
                return True
            else:
                print("❌ Failed to unblock websites")
                return False
                
        except Exception as e:
            print(f"❌ Unblocking error: {e}")
            return False

# Create global instance
blocker = WebsiteBlocker()

# Module-level functions for easy import
def block_websites():
    return blocker.block_websites()

def unblock_websites():
    return blocker.unblock_websites()

def test_blocking():
    return blocker.test_blocking()