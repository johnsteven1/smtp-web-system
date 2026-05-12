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

class EmailManager:
    def __init__(self):
        self.accounts = {}
        self.settings = {}
        self.sent_logs = []
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
            with open(ACCOUNTS_FILE, 'w') as f:
                json.dump(self.accounts, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Error saving accounts: {e}")
            return False
    
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
                "max_retries": 3
            }
            self.save_settings()
    
    def save_settings(self):
        """Save settings to file"""
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
            with open(LOG_FILE, 'w') as f:
                json.dump(self.sent_logs, f, indent=4)
        except:
            pass
    
    def test_connection(self, account_id):
        """Test SMTP connection for an account"""
        if account_id not in self.accounts:
            return False, "Account not found"
        
        account = self.accounts[account_id]
        
        try:
            if account.get('use_ssl', False) or account.get('smtp_port') == 465:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                server = smtplib.SMTP_SSL(
                    account['smtp_server'],
                    account['smtp_port'],
                    timeout=10,
                    context=context
                )
            else:
                server = smtplib.SMTP(
                    account['smtp_server'],
                    account['smtp_port'],
                    timeout=10
                )
                if account.get('smtp_port') == 587:
                    server.starttls()
            
            server.ehlo()
            server.login(account['email'], account['password'])
            server.quit()
            
            return True, "Connection successful"
        
        except Exception as e:
            return False, str(e)
    
    def send_email(self, account_id, to_email, subject, plain_text, html_text=None):
        """Send email using specified account"""
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
        
        try:
            # Send email
            if account.get('use_ssl', False) or account.get('smtp_port') == 465:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                with smtplib.SMTP_SSL(account['smtp_server'], account['smtp_port'], timeout=self.settings.get('default_timeout', 10), context=context) as smtp:
                    smtp.ehlo()
                    smtp.login(account['email'], account['password'])
                    smtp.sendmail(account['email'], to_email, msg.as_string())
            else:
                with smtplib.SMTP(account['smtp_server'], account['smtp_port'], timeout=self.settings.get('default_timeout', 10)) as smtp:
                    if account.get('smtp_port') == 587:
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
                "status": "success"
            }
            self.save_log(log_entry)
            
            return True, "Email sent successfully"
        
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Send failed: {error_msg}")
            
            # Log failure
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "from_account": account['email'],
                "to_email": to_email,
                "subject": subject,
                "status": "failed",
                "error": error_msg
            }
            self.save_log(log_entry)
            
            return False, error_msg
    
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
        email_manager.save_accounts()
        return jsonify({"success": True, "message": "Account added"})
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

if __name__ == '__main__':
    print("\n" + "="*60)
    print("📧 SMTP Email Web System - 20+ Accounts Ready")
    print("="*60)
    print(f"✅ Loaded {len(email_manager.accounts)} email accounts")
    print(f"🌐 Web Interface: http://localhost:5000")
    print(f"🔑 Login Password: {ADMIN_PASSWORD}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
