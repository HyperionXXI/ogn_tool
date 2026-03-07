#!/usr/bin/env python3
r"""
Quick APRS-IS server test: connect, login, read a few lines, report packet vs comment.

Usage (PowerShell):
  $env:OGN_USER="CALLSIGN"
  $env:OGN_PASS="PASSCODE"
  $env:OGN_FILTER="r/47.33/7.27/300"
  python .\scripts\test_aprs_servers.py
"""
from __future__ import annotations

import os
import socket
import time


HOSTS = [
    "glidern1.glidernet.org",
    "glidern2.glidernet.org",
    "glidern3.glidernet.org",
    "glidern4.glidernet.org",
    "glidern5.glidernet.org",
]

PORT = int(os.getenv("OGN_PORT", "14580"))
CALLSIGN = os.getenv("OGN_USER", "NOCALL")
PASSCODE = os.getenv("OGN_PASS", "-1")
FILTER = os.getenv("OGN_FILTER", "")
SOCKET_TIMEOUT_S = 20
READ_LINES = int(os.getenv("OGN_TEST_LINES", "80"))


def login_line() -> str:
    base = f"user {CALLSIGN} pass {PASSCODE} vers ogn_tool 1.1"
    if FILTER:
        base += f" filter {FILTER}"
    return base + "\r\n"


def test_host(host: str) -> None:
    print(f"\n== {host}:{PORT} ==")
    try:
        sock = socket.create_connection((host, PORT), timeout=SOCKET_TIMEOUT_S)
        sock.settimeout(SOCKET_TIMEOUT_S)
        sock.sendall(login_line().encode("ascii", "ignore"))
        f = sock.makefile("r", encoding="utf-8", newline="\n", errors="replace")

        comment = 0
        packets = 0
        non_comment_samples = []
        for _ in range(READ_LINES):
            line = f.readline()
            if not line:
                break
            if line.startswith("#"):
                comment += 1
            else:
                packets += 1
                if len(non_comment_samples) < 3:
                    non_comment_samples.append(line.strip())

        print(f"lines_read={comment+packets} packets={packets} comments={comment}")
        for s in non_comment_samples:
            print(f"sample: {s}")

        f.close()
        sock.close()
    except Exception as e:
        print(f"error: {e!r}")


def main() -> None:
    print(f"Login: user={CALLSIGN} pass={PASSCODE} filter={FILTER!r}")
    for host in HOSTS:
        test_host(host)
        time.sleep(1)


if __name__ == "__main__":
    main()
