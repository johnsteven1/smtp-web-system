#!/usr/bin/env python3
import json
import getpass

def update_credentials():
    """Helper to update email credentials quickly"""
    
    with open('config/email_accounts.json', 'r') as f:
        accounts = json.load(f)
    
    print(f"Found {len(accounts)} email accounts")
    print("="*50)
    
    for acc_id, acc in accounts.items():
        print(f"\nAccount: {acc['name']} ({acc_id})")
        print(f"Current email: {acc['email']}")
        
        update = input(f"Update {acc['name']}? (y/n): ").lower()
        if update == 'y':
            new_email = input(f"New email for {acc['name']}: ").strip()
            if new_email:
                acc['email'] = new_email
            
            new_password = getpass.getpass(f"New password for {acc['name']}: ")
            if new_password:
                acc['password'] = new_password
            
            print(f"✅ Updated {acc['name']}")
    
    with open('config/email_accounts.json', 'w') as f:
        json.dump(accounts, f, indent=4)
    
    print(f"\n✅ All accounts saved to config/email_accounts.json")

if __name__ == "__main__":
    update_credentials()
