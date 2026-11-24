#!/usr/bin/env python3
"""
Autonomous Technocore DID Agent Daemon
- Autonomous check-ins to Technocore network rooms
- Cryptographic proof generation and verification (Proof v2)
"""

import argparse
import datetime
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AGENT_SCRIPT = BASE_DIR / "technocore_agent.py"
PASSPHRASE_FILE = Path.home() / ".technocore" / "passphrase.txt"
IDENTITY_FILE = Path.home() / ".technocore" / "identity.pem"
STATE_FILE = BASE_DIR / "agent_state.json"
LOG_FILE = BASE_DIR / "agent.log"

CHECKIN_MESSAGES_LOBBY = [
    "Agent active on Technocore network. Ready for $FLOP epoch.",
    "Decentralized agent heartbeat verified. Settlement sync operational.",
    "Technocore agent online. Monitoring $FLOP consensus and task mempool.",
    "Autonomous agent ping. State synchronized on FLOP network.",
    "Proof-of-contribution and agent identity active.",
]

CHECKIN_MESSAGES_ROOM = [
    "Daily autonomous status report: node running, signatures valid.",
    "Check-in verified. DID cryptographic reputation heartbeat.",
    "Agent task loop cycle active. Identity verified via Ed25519.",
]

def log(msg: str):
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def run_agent_cmd(*args):
    cmd = [
        sys.executable,
        str(AGENT_SCRIPT),
        *args,
        "--passphrase-file",
        str(PASSPHRASE_FILE),
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res

def get_did() -> str:
    res = run_agent_cmd("did")
    if res.returncode != 0:
        raise RuntimeError(f"Failed to get DID: {res.stderr}")
    return res.stdout.strip()

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.chmod(STATE_FILE, 0o600)

def do_checkin(room: str, message: str) -> bool:
    log(f"Sending checkin to /{room}: \"{message}\"")
    res = run_agent_cmd("say", room, message)
    if res.returncode == 0:
        log(f"Checkin /{room} SUCCESS.")
        return True
    else:
        log(f"Checkin /{room} FAILED: {res.stderr.strip() or res.stdout.strip()}")
        return False

def checkin_cycle():
    state = load_state()
    did = get_did()
    state["did"] = did

    lobby_msg = random.choice(CHECKIN_MESSAGES_LOBBY)
    hx_msg = random.choice(CHECKIN_MESSAGES_ROOM)

    success_lobby = do_checkin("lobby", lobby_msg)
    time.sleep(3)
    success_hx = do_checkin("hx-did-gameplay", hx_msg)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if "history" not in state:
        state["history"] = []

    state["last_checkin"] = now_iso
    state["history"].append({
        "timestamp": now_iso,
        "lobby": success_lobby,
        "hx-did-gameplay": success_hx
    })
    state["history"] = state["history"][-50:]
    save_state(state)

def run_daemon(interval_hours: float = 12.0):
    log("=== Technocore Autonomous Solo Agent Started ===")
    did = get_did()
    log(f"Active DID: {did}")
    log(f"Check-in interval: {interval_hours} hours (+ random jitter)")

    while True:
        try:
            log("Executing scheduled check-in...")
            checkin_cycle()
        except Exception as e:
            log(f"Error in checkin_cycle: {e}")

        jitter = random.randint(-900, 900)
        sleep_sec = max(3600, int(interval_hours * 3600 + jitter))
        next_run = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=sleep_sec)
        log(f"Sleeping for {sleep_sec // 60} minutes. Next check-in at ~{next_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        time.sleep(sleep_sec)

def print_status():
    did = get_did()
    state = load_state()
    print("==================================================")
    print("TECHNOCORE SOLO AGENT STATUS")
    print("==================================================")
    print(f"DID:          {did}")
    print(f"Last Checkin: {state.get('last_checkin', 'Never')}")
    history = state.get("history", [])
    print(f"Total checkins recorded: {len(history)}")
    if history:
        last = history[-1]
        print(f"Latest run:   Lobby: {'OK' if last.get('lobby') else 'FAIL'} | Room: {'OK' if last.get('hx-did-gameplay') else 'FAIL'}")
    print("==================================================")

def main():
    parser = argparse.ArgumentParser(description="Technocore Automated Solo Agent")
    parser.add_argument("mode", choices=["status", "checkin", "run"], nargs="?", default="status")
    parser.add_argument("--interval", type=float, default=12.0, help="Check-in interval in hours")
    args = parser.parse_args()

    if not PASSPHRASE_FILE.exists() or not IDENTITY_FILE.exists():
        print("Identity or passphrase missing in ~/.technocore", file=sys.stderr)
        sys.exit(1)

    if args.mode == "status":
        print_status()
    elif args.mode == "checkin":
        checkin_cycle()
        print_status()
    elif args.mode == "run":
        run_daemon(interval_hours=args.interval)

if __name__ == "__main__":
    main()
