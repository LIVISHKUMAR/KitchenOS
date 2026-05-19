"""Advanced security features."""

import time
from typing import Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import threading


class BruteForceProtection:
    """Protect against brute force attacks."""

    def __init__(self, max_attempts: int = 5, lockout_minutes: int = 15):
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        self._attempts: Dict[str, list] = defaultdict(list)
        self._lockouts: Dict[str, datetime] = {}
        self._lock = threading.Lock()

    def record_attempt(self, key: str, success: bool):
        """Record a login attempt."""
        with self._lock:
            now = datetime.utcnow()

            if success:
                # Clear attempts on success
                self._attempts.pop(key, None)
                self._lockouts.pop(key, None)
                return

            # Check if locked out
            if key in self._lockouts:
                if now < self._lockouts[key]:
                    return  # Still locked out
                else:
                    # Lockout expired
                    del self._lockouts[key]
                    self._attempts.pop(key, None)

            # Record failed attempt
            self._attempts[key].append(now)

            # Remove old attempts (outside window)
            window_start = now - timedelta(minutes=self.lockout_minutes)
            self._attempts[key] = [
                t for t in self._attempts[key] if t > window_start
            ]

            # Check if should lock out
            if len(self._attempts[key]) >= self.max_attempts:
                self._lockouts[key] = now + timedelta(minutes=self.lockout_minutes)
                self._attempts.pop(key, None)

    def is_locked_out(self, key: str) -> bool:
        """Check if a key is locked out."""
        with self._lock:
            if key in self._lockouts:
                if datetime.utcnow() < self._lockouts[key]:
                    return True
                else:
                    del self._lockouts[key]
            return False

    def get_remaining_lockout(self, key: str) -> Optional[int]:
        """Get remaining lockout time in seconds."""
        with self._lock:
            if key in self._lockouts:
                remaining = (self._lockouts[key] - datetime.utcnow()).total_seconds()
                if remaining > 0:
                    return int(remaining)
                else:
                    del self._lockouts[key]
            return None

    def get_status(self) -> dict:
        """Get brute force protection status."""
        return {
            "active_lockouts": len(self._lockouts),
            "tracked_keys": len(self._attempts)
        }


class IPAllowlist:
    """IP allowlist for API access."""

    def __init__(self):
        self._allowed_ips: set = set()
        self._blocked_ips: set = set()

    def add_allowed(self, ip: str):
        """Add IP to allowlist."""
        self._allowed_ips.add(ip)

    def remove_allowed(self, ip: str):
        """Remove IP from allowlist."""
        self._allowed_ips.discard(ip)

    def block_ip(self, ip: str):
        """Block an IP."""
        self._blocked_ips.add(ip)

    def unblock_ip(self, ip: str):
        """Unblock an IP."""
        self._blocked_ips.discard(ip)

    def is_allowed(self, ip: str) -> bool:
        """Check if an IP is allowed."""
        if ip in self._blocked_ips:
            return False
        if self._allowed_ips and ip not in self._allowed_ips:
            return False
        return True

    def get_status(self) -> dict:
        """Get IP allowlist status."""
        return {
            "allowed_ips": list(self._allowed_ips),
            "blocked_ips": list(self._blocked_ips)
        }


class SuspiciousActivityDetector:
    """Detect suspicious activity patterns."""

    def __init__(self):
        self._events: Dict[str, list] = defaultdict(list)
        self._alerts: list = []

    def record_event(self, user_id: str, event_type: str, ip: str = None):
        """Record a security event."""
        now = datetime.utcnow()
        self._events[user_id].append({
            "type": event_type,
            "ip": ip,
            "timestamp": now
        })

        # Keep only last 100 events per user
        if len(self._events[user_id]) > 100:
            self._events[user_id] = self._events[user_id][-100:]

        # Check for suspicious patterns
        self._check_patterns(user_id, event_type, ip)

    def _check_patterns(self, user_id: str, event_type: str, ip: str):
        """Check for suspicious activity patterns."""
        events = self._events[user_id]
        now = datetime.utcnow()
        recent = [e for e in events if (now - e["timestamp"]).seconds < 300]  # Last 5 minutes

        # Multiple failed logins
        failed_logins = [e for e in recent if e["type"] == "login_failed"]
        if len(failed_logins) >= 5:
            self._add_alert(user_id, "multiple_failed_logins", ip)

        # Multiple IPs
        recent_ips = set(e["ip"] for e in recent if e["ip"])
        if len(recent_ips) >= 3:
            self._add_alert(user_id, "multiple_ips", ip)

        # Rapid API calls
        api_calls = [e for e in recent if e["type"] == "api_call"]
        if len(api_calls) >= 100:
            self._add_alert(user_id, "rapid_api_calls", ip)

    def _add_alert(self, user_id: str, alert_type: str, ip: str):
        """Add a security alert."""
        alert = {
            "user_id": user_id,
            "type": alert_type,
            "ip": ip,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._alerts.append(alert)

        # Keep only last 1000 alerts
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]

    def get_alerts(self, limit: int = 50) -> list:
        """Get recent security alerts."""
        return self._alerts[-limit:]


# Global instances
brute_force = BruteForceProtection()
ip_allowlist = IPAllowlist()
activity_detector = SuspiciousActivityDetector()
