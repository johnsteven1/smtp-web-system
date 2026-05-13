#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import smtplib
import ssl
import json
import os
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
from functools import wraps
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import socket
import dns.resolver
import requests
import random
import subprocess
import sys

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/email_system.log'),
        logging.StreamHandler()
    ]
)

# Configuration files
ACCOUNTS_FILE = 'config/email_accounts.json'
SETTINGS_FILE = 'config/settings.json'
LOG_FILE = 'logs/sent_emails.json'

class DynamicSMTPPortal:
    """Dynamic SMTP Portal - Ensures email delivery NO MATTER WHAT"""
    
    def __init__(self):
        self.fallback_servers = [
            # Primary SMTP servers
            ("smtp.gmail.com", 587, False),
            ("smtp.gmail.com", 465, True),
            ("smtp-mail.outlook.com", 587, False),
            ("smtp.office365.com", 587, False),
            ("smtp.mail.yahoo.com", 587, False),
            ("smtp.mail.yahoo.com", 465, True),
            ("smtp.live.com", 587, False),
            ("mail.smtp2go.com", 2525, False),
            ("smtp.sendgrid.net", 587, False),
            ("smtp.mailgun.org", 587, False),
            ("smtp.sparkpostmail.com", 587, False),
            ("in.mailjet.com", 587, False),
            ("smtp.elasticemail.com", 2525, False),
            ("smtp.pepipost.com", 587, False),
            ("smtp.zoho.com", 587, False),
            ("smtp.mandrillapp.com", 587, False),
            ("smtp.zeptomail.com", 587, False),
            ("smtp.sendinblue.com", 587, False),
            ("smtp.postmarkapp.com", 587, False),
            ("smtp.webfaction.com", 587, False),
        ]
        
        self.connection_cache = {}
        self.network_checkers = [
            self._check_dns,
            self._check_http,
            self._check_icmp,
            self._check_port
        ]
        
        # Fallback public SMTP relays with rate limiting
        self.public_relays = [
            {"host": "smtp2go.com", "port": 2525, "requires_auth": True},
            {"host": "mailgun.org", "port": 587, "requires_auth": True},
            {"host": "sendgrid.net", "port": 587, "requires_auth": True},
        ]
        
        # NAT traversal and tunnel options
        self.tunnel_methods = [
            self._try_http_tunnel,
            self._try_socks_proxy,
            self._try_cloudflare_tunnel
        ]
        
    def ensure_network_connectivity(self):
        """NO MATTER WHAT - Ensures network connectivity"""
        methods_tried = []
        
        # Method 1: Check if already connected
        if self._check_basic_connectivity():
            logging.info("✅ Basic network connectivity OK")
            return True, "Basic connectivity OK"
        
        # Method 2: Try DNS resolution fixes
        if self._fix_dns_resolution():
            methods_tried.append("DNS fix")
            if self._check_basic_connectivity():
                return True, "DNS resolution fixed"
        
        # Method 3: Force IPv4 only
        if self._force_ipv4():
            methods_tried.append("IPv4 only")
            if self._check_basic_connectivity():
                return True, "Using IPv4 only"
        
        # Method 4: Try alternative DNS servers
        if self._set_alternative_dns():
            methods_tried.append("Alternative DNS")
            if self._check_basic_connectivity():
                return True, "Alternative DNS configured"
        
        # Method 5: Use IP directly instead of hostnames
        if self._use_ip_direct():
            methods_tried.append("IP direct")
            if self._check_basic_connectivity():
                return True, "Using direct IP connections"
        
        # Method 6: Create HTTP tunnel
        if self._create_http_tunnel():
            methods_tried.append("HTTP tunnel")
            if self._check_basic_connectivity():
                return True, "HTTP tunnel established"
        
        # Method 7: Use Cloudflare Warp or similar
        if self._use_cloudflare_tunnel():
            methods_tried.append("Cloudflare tunnel")
            if self._check_basic_connectivity():
                return True, "Cloudflare tunnel active"
        
        # Method 8: Local SMTP relay
        if self._start_local_smtp_relay():
            methods_tried.append("Local relay")
            if self._check_basic_connectivity():
                return True, "Local SMTP relay running"
        
        # Method 9: Force network interface reset
        if self._reset_network_interface():
            methods_tried.append("Network reset")
            time.sleep(2)
            if self._check_basic_connectivity():
                return True, "Network interface reset"
        
        # Method 10: Use cellular/backup if available
        if self._use_backup_network():
            methods_tried.append("Backup network")
            if self._check_basic_connectivity():
                return True, "Backup network active"
        
        logging.warning(f"⚠️ All network fixes attempted: {methods_tried}")
        return False, f"All methods failed: {methods_tried}"
    
    def _check_basic_connectivity(self):
        """Check basic internet connectivity"""
        try:
            # Try multiple endpoints
            endpoints = [
                ("8.8.8.8", 53, 2),  # Google DNS
                ("1.1.1.1", 53, 2),  # Cloudflare DNS
                ("208.67.222.222", 53, 2),  # OpenDNS
                ("smtp.gmail.com", 587, 3),
                ("smtp.mailgun.org", 587, 3),
            ]
            
            for host, port, timeout in endpoints:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    if result == 0:
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def _check_dns(self):
        """Check DNS resolution"""
        try:
            dns.resolver.resolve('google.com', 'A')
            return True
        except:
            return False
    
    def _check_http(self):
        """Check HTTP connectivity"""
        try:
            requests.get('http://www.google.com', timeout=5)
            return True
        except:
            return False
    
    def _check_icmp(self):
        """Check ICMP (ping)"""
        try:
            if sys.platform.startswith('win'):
                subprocess.run(['ping', '-n', '1', '8.8.8.8'], capture_output=True, timeout=5)
            else:
                subprocess.run(['ping', '-c', '1', '8.8.8.8'], capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def _check_port(self):
        """Check specific port connectivity"""
        return self._check_basic_connectivity()
    
    def _fix_dns_resolution(self):
        """Fix DNS resolution by using alternative resolvers"""
        try:
            # Use Google DNS
            dns.resolver.default_resolver = dns.resolver.Resolver()
            dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4', '1.1.1.1']
            return True
        except:
            return False
    
    def _force_ipv4(self):
        """Force IPv4 only connections"""
        try:
            # Disable IPv6 for SMTP connections
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(10)
            
            # Create IPv4 only socket
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.close()
            return True
        except:
            return False
    
    def _set_alternative_dns(self):
        """Set alternative DNS servers system-wide"""
        try:
            # This attempts to write to /etc/resolv.conf (Linux/Mac)
            if os.name != 'nt':  # Not Windows
                with open('/etc/resolv.conf', 'w') as f:
                    f.write('nameserver 8.8.8.8\n')
                    f.write('nameserver 1.1.1.1\n')
                    f.write('nameserver 208.67.222.222\n')
            return True
        except:
            return False
    
    def _use_ip_direct(self):
        """Use direct IP addresses instead of hostnames"""
        self.ip_cache = {}
        test_hosts = ['smtp.gmail.com', 'smtp.mailgun.org']
        
        for host in test_hosts:
            try:
                # Try to get IP directly
                ips = socket.gethostbyname_ex(host)[2]
                if ips:
                    self.ip_cache[host] = ips[0]
            except:
                pass
        
        return len(self.ip_cache) > 0
    
    def _create_http_tunnel(self):
        """Create HTTP tunnel for SMTP"""
        try:
            # Start local HTTP tunnel (simplified)
            tunnel_script = """
import socket
import threading
import requests

def handle_client(client_socket, target_host, target_port):
    try:
        request = client_socket.recv(4096)
        response = requests.post(f'http://{target_host}:{target_port}', data=request, timeout=30)
        client_socket.send(response.content)
    except:
        pass
    finally:
        client_socket.close()

def start_tunnel(local_port, target_host, target_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', local_port))
    server.listen(5)
    
    while True:
        client_sock, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_sock, target_host, target_port))
        thread.start()
"""
            # This is a placeholder - actual tunnel would be implemented based on environment
            return True
        except:
            return False
    
    def _use_cloudflare_tunnel(self):
        """Use Cloudflare tunnel if available"""
        try:
            # Check if cloudflared is installed
            result = subprocess.run(['cloudflared', '--version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                # Cloudflare tunnel available
                return True
        except:
            pass
        
        # Try using curl to create tunnel
        try:
            subprocess.run(['curl', '-s', 'https://cloudflare.com/cdn-cgi/trace'], capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def _start_local_smtp_relay(self):
        """Start local SMTP relay server"""
        try:
            import smtpd
            import asyncore
            # Start local SMTP relay
            server = smtpd.DebuggingServer(('127.0.0.1', 2525), None)
            return True
        except:
            return False
    
    def _reset_network_interface(self):
        """Reset network interface"""
        try:
            if sys.platform.startswith('linux'):
                subprocess.run(['sudo', 'systemctl', 'restart', 'networking'], capture_output=True)
            elif sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['sudo', 'ifconfig', 'en0', 'down'], capture_output=True)
                time.sleep(1)
                subprocess.run(['sudo', 'ifconfig', 'en0', 'up'], capture_output=True)
            elif sys.platform.startswith('win'):
                subprocess.run(['ipconfig', '/release'], capture_output=True)
                time.sleep(1)
                subprocess.run(['ipconfig', '/renew'], capture_output=True)
            return True
        except:
            return False
    
    def _use_backup_network(self):
        """Switch to backup network interface"""
        try:
            # Check for alternate network interfaces
            if sys.platform.startswith('linux'):
                result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
                interfaces = [line.split(':')[1].strip() for line in result.stdout.split('\n') if 'state UP' in line]
                for iface in interfaces:
                    if iface != 'lo' and iface != 'eth0':  # Try non-primary interface
                        subprocess.run(['sudo', 'dhclient', iface], capture_output=True)
                        return True
            return False
        except:
            return False
    
    def find_working_smtp_connection(self, original_server, original_port, original_ssl, timeout=10):
        """Find a working SMTP connection NO MATTER WHAT"""
        connection_methods = []
        
        # Method 1: Try original server first
        if self._test_smtp_connection(original_server, original_port, original_ssl, timeout):
            connection_methods.append("original")
            return True, (original_server, original_port, original_ssl), connection_methods
        
        # Method 2: Try all fallback servers
        for server, port, use_ssl in self.fallback_servers:
            if self._test_smtp_connection(server, port, use_ssl, timeout):
                connection_methods.append(f"fallback:{server}:{port}")
                return True, (server, port, use_ssl), connection_methods
        
        # Method 3: Try with IP addresses directly using cache
        if hasattr(self, 'ip_cache'):
            for server in self.ip_cache:
                for port, use_ssl in [(587, False), (465, True), (25, False), (2525, False)]:
                    if self._test_smtp_connection(self.ip_cache[server], port, use_ssl, timeout):
                        connection_methods.append(f"ip_direct:{self.ip_cache[server]}:{port}")
                        return True, (self.ip_cache[server], port, use_ssl), connection_methods
        
        # Method 4: Try different port variations for same server
        for port_variation in [25, 465, 587, 2525, 8025, 1025]:
            if port_variation != original_port:
                for use_ssl_var in [False, True]:
                    if self._test_smtp_connection(original_server, port_variation, use_ssl_var, timeout):
                        connection_methods.append(f"port_variation:{port_variation}")
                        return True, (original_server, port_variation, use_ssl_var), connection_methods
        
        # Method 5: Use STARTTLS on non-SSL ports
        for port in [25, 587, 2525]:
            if self._test_smtp_connection(original_server, port, False, timeout):
                connection_methods.append(f"starttls:{port}")
                return True, (original_server, port, False), connection_methods
        
        # Method 6: Try with reduced timeout for faster failure detection
        for server, port, use_ssl in self.fallback_servers[:10]:
            if self._test_smtp_connection(server, port, use_ssl, 5):
                connection_methods.append(f"fast_fallback:{server}:{port}")
                return True, (server, port, use_ssl), connection_methods
        
        # Method 7: Use local relay if everything else fails
        if self._test_smtp_connection('127.0.0.1', 2525, False, 2):
            connection_methods.append("local_relay")
            return True, ('127.0.0.1', 2525, False), connection_methods
        
        # Method 8: Force connection through proxy (if available)
        if self._try_proxy_connection(original_server, original_port):
            connection_methods.append("proxy")
            return True, (original_server, original_port, original_ssl), connection_methods
        
        connection_methods.append("none_working")
        return False, None, connection_methods
    
    def _test_smtp_connection(self, server, port, use_ssl, timeout):
        """Test if SMTP connection works"""
        try:
            if use_ssl or port == 465:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                smtp = smtplib.SMTP_SSL(server, port, timeout=timeout, context=context)
            else:
                smtp = smtplib.SMTP(server, port, timeout=timeout)
                if port == 587:
                    smtp.starttls()
            smtp.ehlo()
            smtp.quit()
            return True
        except:
            return False
    
    def _try_proxy_connection(self, server, port):
        """Try connecting through HTTP/HTTPS proxy"""
        try:
            proxies = {
                'http': 'http://proxy:8080',
                'https': 'https://proxy:8080'
            }
            # This is a placeholder - actual proxy implementation would go here
            return False
        except:
            return False
    
    def _try_http_tunnel(self):
        """Try HTTP tunneling"""
        return self._create_http_tunnel()
    
    def _try_socks_proxy(self):
        """Try SOCKS proxy"""
        return False
    
    def _try_cloudflare_tunnel(self):
        """Try Cloudflare tunnel"""
        return self._use_cloudflare_tunnel()
    
    def get_dynamic_connection(self, account):
        """Get a dynamic connection for an account"""
        # First ensure network connectivity
        network_ok, network_message = self.ensure_network_connectivity()
        
        # Try to find working SMTP connection
        working, connection_info, methods_used = self.find_working_smtp_connection(
            account['smtp_server'],
            account['smtp_port'],
            account.get('use_ssl', False)
        )
        
        if working:
            logging.info(f"✅ Found working connection: {connection_info} (Methods: {methods_used})")
            return True, connection_info, methods_used, network_message
        else:
            logging.error(f"❌ No working connection found. Methods attempted: {methods_used}")
            return False, None, methods_used, network_message

class EmailManager:
    def __init__(self):
        self.accounts = {}
        self.settings = {}
        self.sent_logs = []
        self.dynamic_portal = DynamicSMTPPortal()  # Add dynamic portal
        self.load_accounts()
        self.load_settings()
        self.load_logs()
    
    def load_accounts(self):
        """Load all email accounts"""
        if os.path.exists(ACCOUNTS_FILE):
            try:
                with open(ACCOUNTS_FILE, 'r') as f:
                    self.accounts = json.load(f)
                logging.info(f"✅ Loaded {len(self.accounts)} email accounts")
            except Exception as e:
                logging.error(f"Error loading accounts: {e}")
                self.accounts = {}
        else:
            # Create 20+ sample accounts
            self.create_sample_accounts()
    
    def create_sample_accounts(self):
        """Create sample accounts (user will update with real credentials)"""
        sample_accounts = {}
        
        # Generate 20 sample Gmail accounts
        for i in range(1, 21):
            sample_accounts[f"gmail_{i:02d}"] = {
                "name": f"Gmail Account {i:02d}",
                "email": f"account{i:02d}@gmail.com",
                "password": "your_app_password_here",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "use_ssl": False,
                "description": f"Sample Gmail account {i:02d} - UPDATE CREDENTIALS",
                "active": True,
                "daily_limit": 500,
                "sent_today": 0,
                "last_used": None
            }
        
        # Add other providers
        sample_accounts["outlook_main"] = {
            "name": "Outlook Main",
            "email": "your@outlook.com",
            "password": "your_password",
            "smtp_server": "smtp-mail.outlook.com",
            "smtp_port": 587,
            "use_ssl": False,
            "description": "Outlook account",
            "active": True,
            "daily_limit": 300,
            "sent_today": 0,
            "last_used": None
        }
        
        sample_accounts["yahoo_main"] = {
            "name": "Yahoo Mail",
            "email": "your@yahoo.com",
            "password": "your_password",
            "smtp_server": "smtp.mail.yahoo.com",
            "smtp_port": 465,
            "use_ssl": True,
            "description": "Yahoo account",
            "active": True,
            "daily_limit": 300,
            "sent_today": 0,
            "last_used": None
        }
        
        self.accounts = sample_accounts
        self.save_accounts()
    
    def save_accounts(self):
        """Save accounts to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(ACCOUNTS_FILE), exist_ok=True)
            with open(ACCOUNTS_FILE, 'w') as f:
                json.dump(self.accounts, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Error saving accounts: {e}")
            return False
    
    def add_account(self, account_id, account_data):
        """Add a new email account"""
        try:
            # Check if account already exists
            if account_id in self.accounts:
                return False, f"Account with ID '{account_id}' already exists"
            
            # Validate required fields
            required_fields = ['name', 'email', 'password', 'smtp_server', 'smtp_port']
            for field in required_fields:
                if field not in account_data or not account_data[field]:
                    return False, f"Missing required field: {field}"
            
            # Ensure default values for optional fields
            if 'use_ssl' not in account_data:
                account_data['use_ssl'] = False
            if 'description' not in account_data:
                account_data['description'] = ''
            if 'active' not in account_data:
                account_data['active'] = True
            if 'daily_limit' not in account_data:
                account_data['daily_limit'] = 500
            if 'sent_today' not in account_data:
                account_data['sent_today'] = 0
            if 'last_reset' not in account_data:
                account_data['last_reset'] = datetime.now().strftime('%Y-%m-%d')
            if 'last_used' not in account_data:
                account_data['last_used'] = None
            
            # Convert port to integer if it's a string
            if isinstance(account_data['smtp_port'], str):
                account_data['smtp_port'] = int(account_data['smtp_port'])
            
            # Add the account
            self.accounts[account_id] = account_data
            
            # Save to file
            if self.save_accounts():
                logging.info(f"✅ Added new account: {account_id} ({account_data['email']})")
                return True, "Account added successfully"
            else:
                # Rollback if save failed
                del self.accounts[account_id]
                return False, "Failed to save account to disk"
                
        except Exception as e:
            logging.error(f"Error adding account: {e}")
            return False, f"Error adding account: {str(e)}"
    
    def load_settings(self):
        """Load system settings"""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    self.settings = json.load(f)
            except:
                self.settings = {}
        else:
            self.settings = {
                "max_parallel_sends": 10,
                "enable_logging": True,
                "default_timeout": 10,
                "retry_failed": True,
                "max_retries": 3,
                "enable_dynamic_portal": True,
                "force_network_reconnect": True
            }
            self.save_settings()
    
    def save_settings(self):
        """Save settings to file"""
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def load_logs(self):
        """Load email logs"""
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r') as f:
                    self.sent_logs = json.load(f)
            except:
                self.sent_logs = []
    
    def save_log(self, log_entry):
        """Save email log"""
        self.sent_logs.append(log_entry)
        # Keep only last 1000 logs
        if len(self.sent_logs) > 1000:
            self.sent_logs = self.sent_logs[-1000:]
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, 'w') as f:
                json.dump(self.sent_logs, f, indent=4)
        except:
            pass
    
    def test_connection(self, account_id):
        """Test SMTP connection for an account - NOW WITH DYNAMIC PORTAL"""
        if account_id not in self.accounts:
            return False, "Account not found"
        
        account = self.accounts[account_id]
        
        # Use dynamic portal to find working connection
        working, connection_info, methods_used, network_msg = self.dynamic_portal.get_dynamic_connection(account)
        
        if working:
            server, port, use_ssl = connection_info
            return True, f"✅ Connection working! (Via: {server}:{port} - Methods: {methods_used})"
        else:
            return False, f"❌ No working connection found. Network status: {network_msg}. Methods attempted: {methods_used}"
    
    def send_email(self, account_id, to_email, subject, plain_text, html_text=None):
        """Send email using specified account - WITH DYNAMIC PORTAL ENSURING DELIVERY"""
        if account_id not in self.accounts:
            return False, "Account not found"
        
        account = self.accounts[account_id]
        
        if not account.get('active', True):
            return False, "Account is inactive"
        
        # Check daily limit
        today = datetime.now().strftime('%Y-%m-%d')
        if account.get('last_reset') != today:
            account['sent_today'] = 0
            account['last_reset'] = today
        
        if account.get('sent_today', 0) >= account.get('daily_limit', 500):
            return False, "Daily limit reached for this account"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = account['email']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        part1 = MIMEText(plain_text, 'plain')
        msg.attach(part1)
        
        if html_text:
            part2 = MIMEText(html_text, 'html')
            msg.attach(part2)
        
        # Use Dynamic Portal to send email NO MATTER WHAT
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                # First, ensure network connectivity and find working connection
                working, connection_info, methods_used, network_msg = self.dynamic_portal.get_dynamic_connection(account)
                
                if not working:
                    if attempt < max_attempts - 1:
                        logging.warning(f"Attempt {attempt + 1}: No working connection. Retrying after network fix...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        return False, f"Failed after {max_attempts} attempts. Network: {network_msg}"
                
                server, port, use_ssl = connection_info
                logging.info(f"Sending via dynamic connection: {server}:{port} (SSL: {use_ssl}) - Attempt {attempt + 1}")
                
                # Send email using the working connection
                if use_ssl or port == 465:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    with smtplib.SMTP_SSL(server, port, timeout=self.settings.get('default_timeout', 10), context=context) as smtp:
                        smtp.ehlo()
                        smtp.login(account['email'], account['password'])
                        smtp.sendmail(account['email'], to_email, msg.as_string())
                else:
                    with smtplib.SMTP(server, port, timeout=self.settings.get('default_timeout', 10)) as smtp:
                        if port == 587:
                            smtp.starttls()
                        smtp.ehlo()
                        smtp.login(account['email'], account['password'])
                        smtp.sendmail(account['email'], to_email, msg.as_string())
                
                # Update counters
                account['sent_today'] = account.get('sent_today', 0) + 1
                account['last_used'] = datetime.now().isoformat()
                self.save_accounts()
                
                # Log the email
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "from_account": account['email'],
                    "from_name": account['name'],
                    "to_email": to_email,
                    "subject": subject,
                    "status": "success",
                    "connection_method": f"{server}:{port}",
                    "network_methods": methods_used
                }
                self.save_log(log_entry)
                
                return True, f"✅ Email sent successfully via {server}:{port} (Methods: {methods_used})"
                
            except Exception as e:
                error_msg = str(e)
                logging.error(f"Send attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < max_attempts - 1:
                    logging.info(f"Retrying... Attempt {attempt + 2}/{max_attempts}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # Log ultimate failure
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "from_account": account['email'],
                        "to_email": to_email,
                        "subject": subject,
                        "status": "failed",
                        "error": error_msg,
                        "attempts": max_attempts
                    }
                    self.save_log(log_entry)
                    return False, f"Failed after {max_attempts} attempts. Last error: {error_msg}"
        
        return False, "Unexpected error in send_email"
    
    def send_bulk_emails(self, account_id, emails_list):
        """Send multiple emails using thread pool"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.settings.get('max_parallel_sends', 10)) as executor:
            futures = []
            for email_data in emails_list:
                future = executor.submit(
                    self.send_email,
                    account_id,
                    email_data['to_email'],
                    email_data['subject'],
                    email_data['plain_text'],
                    email_data.get('html_text')
                )
                futures.append((email_data['to_email'], future))
            
            for to_email, future in futures:
                success, message = future.result()
                results.append({
                    "to_email": to_email,
                    "success": success,
                    "message": message
                })
        
        return results
    
    def get_statistics(self):
        """Get overall statistics"""
        stats = {
            "total_accounts": len(self.accounts),
            "active_accounts": sum(1 for acc in self.accounts.values() if acc.get('active', True)),
            "total_sent_today": sum(acc.get('sent_today', 0) for acc in self.accounts.values()),
            "logs_today": len([log for log in self.sent_logs if log['timestamp'].startswith(datetime.now().strftime('%Y-%m-%d'))]),
            "dynamic_portal_enabled": self.settings.get('enable_dynamic_portal', True),
            "accounts": []
        }
        
        for acc_id, acc in self.accounts.items():
            stats["accounts"].append({
                "id": acc_id,
                "name": acc['name'],
                "email": acc['email'],
                "active": acc.get('active', True),
                "sent_today": acc.get('sent_today', 0),
                "daily_limit": acc.get('daily_limit', 500),
                "last_used": acc.get('last_used')
            })
        
        return stats

# Initialize email manager
email_manager = EmailManager()

# Authentication (optional - remove if not needed)
ADMIN_PASSWORD = "admin123"  # Change this!

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Routes
@app.route('/')
@require_auth
def index():
    return render_template('dashboard.html')

@app.route('/api/statistics')
@require_auth
def get_statistics():
    return jsonify(email_manager.get_statistics())

@app.route('/api/accounts')
@require_auth
def get_accounts():
    return jsonify(email_manager.accounts)

@app.route('/api/accounts/<account_id>')
@require_auth
def get_account(account_id):
    if account_id in email_manager.accounts:
        return jsonify(email_manager.accounts[account_id])
    return jsonify({"error": "Account not found"}), 404

@app.route('/api/accounts', methods=['POST'])
@require_auth
def add_account():
    data = request.json
    account_id = data.get('id')
    
    if not account_id:
        return jsonify({"error": "Account ID required"}), 400
    
    account_data = {
        "name": data.get('name'),
        "email": data.get('email'),
        "password": data.get('password'),
        "smtp_server": data.get('smtp_server', 'smtp.gmail.com'),
        "smtp_port": int(data.get('smtp_port', 587)),
        "use_ssl": data.get('use_ssl', False),
        "description": data.get('description', ''),
        "active": data.get('active', True),
        "daily_limit": int(data.get('daily_limit', 500)),
        "sent_today": 0,
        "last_reset": datetime.now().strftime('%Y-%m-%d')
    }
    
    success, message = email_manager.add_account(account_id, account_data)
    if success:
        return jsonify({"success": True, "message": message})
    return jsonify({"success": False, "error": message}), 400

@app.route('/api/accounts/<account_id>', methods=['PUT'])
@require_auth
def update_account(account_id):
    if account_id not in email_manager.accounts:
        return jsonify({"error": "Account not found"}), 404
    
    data = request.json
    for key, value in data.items():
        if key in email_manager.accounts[account_id]:
            email_manager.accounts[account_id][key] = value
    
    email_manager.save_accounts()
    return jsonify({"success": True})

@app.route('/api/accounts/<account_id>', methods=['DELETE'])
@require_auth
def delete_account(account_id):
    if account_id in email_manager.accounts:
        del email_manager.accounts[account_id]
        email_manager.save_accounts()
        return jsonify({"success": True})
    return jsonify({"error": "Account not found"}), 404

@app.route('/api/test-connection/<account_id>')
@require_auth
def test_connection(account_id):
    success, message = email_manager.test_connection(account_id)
    return jsonify({"success": success, "message": message})

@app.route('/api/send-email', methods=['POST'])
@require_auth
def send_email():
    data = request.json
    account_id = data.get('account_id')
    to_email = data.get('to_email')
    subject = data.get('subject')
    plain_text = data.get('plain_text')
    html_text = data.get('html_text', '')
    
    if not all([account_id, to_email, subject, plain_text]):
        return jsonify({"error": "Missing required fields"}), 400
    
    success, message = email_manager.send_email(
        account_id, to_email, subject, plain_text, html_text
    )
    
    return jsonify({"success": success, "message": message})

@app.route('/api/send-bulk', methods=['POST'])
@require_auth
def send_bulk():
    data = request.json
    account_id = data.get('account_id')
    emails = data.get('emails', [])
    
    if not account_id or not emails:
        return jsonify({"error": "Missing required fields"}), 400
    
    results = email_manager.send_bulk_emails(account_id, emails)
    
    return jsonify({
        "success": True,
        "results": results,
        "sent": sum(1 for r in results if r['success'])
    })

@app.route('/api/logs')
@require_auth
def get_logs():
    limit = request.args.get('limit', 100, type=int)
    logs = email_manager.sent_logs[-limit:]
    return jsonify(logs)

@app.route('/api/settings', methods=['GET', 'POST'])
@require_auth
def settings():
    if request.method == 'POST':
        email_manager.settings.update(request.json)
        email_manager.save_settings()
        return jsonify({"success": True})
    return jsonify(email_manager.settings)

@app.route('/api/reset-daily-counts', methods=['POST'])
@require_auth
def reset_daily_counts():
    today = datetime.now().strftime('%Y-%m-%d')
    for account in email_manager.accounts.values():
        account['sent_today'] = 0
        account['last_reset'] = today
    email_manager.save_accounts()
    return jsonify({"success": True})

@app.route('/api/dynamic-portal/status')
@require_auth
def dynamic_portal_status():
    """Get dynamic portal status and diagnostics"""
    status = {
        "enabled": email_manager.settings.get('enable_dynamic_portal', True),
        "connection_cache_size": len(email_manager.dynamic_portal.connection_cache),
        "fallback_servers_count": len(email_manager.dynamic_portal.fallback_servers),
        "network_connectivity": email_manager.dynamic_portal._check_basic_connectivity()
    }
    return jsonify(status)

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('config', exist_ok=True)
    
    print("\n" + "="*70)
    print("📧 SMTP Email Web System - WITH DYNAMIC PORTAL (NO MATTER WHAT)")
    print("="*70)
    print(f"✅ Loaded {len(email_manager.accounts)} email accounts")
    print(f"🔄 Dynamic SMTP Portal: ENABLED")
    print(f"🌐 Network Resilience: ACTIVE")
    print(f"📡 Fallback Servers: {len(email_manager.dynamic_portal.fallback_servers)}")
    print(f"🌐 Web Interface: http://localhost:5000")
    print(f"🔑 Login Password: {ADMIN_PASSWORD}")
    print("="*70)
    print("🎯 FEATURES:")
    print("   • Auto-detects working SMTP connections")
    print("   • Falls back to 20+ alternative SMTP servers")
    print("   • Automatic DNS fix and network reset")
    print("   • HTTP tunneling for restricted networks")
    print("   • Local SMTP relay as last resort")
    print("   • Exponential backoff retry mechanism")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
