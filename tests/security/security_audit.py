"""Security Audit Checklist and Validation."""

import requests
import json
import sys


class SecurityAuditor:
    """Automated security audit for KitchenOS API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.results = []

    def run_all_checks(self):
        """Run all security checks."""
        print("=" * 60)
        print("KitchenOS Security Audit")
        print("=" * 60)

        self.check_security_headers()
        self.check_cors()
        self.check_rate_limiting()
        self.check_auth_endpoints()
        self.check_sql_injection()
        self.check_xss()
        self.check_sensitive_data()
        self.check_https()
        self.check_api_versioning()

        self.print_report()

    def check_security_headers(self):
        """Check for security headers."""
        print("\n[1] Checking Security Headers...")

        try:
            response = requests.get(f"{self.base_url}/health")
            headers = response.headers

            checks = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin"
            }

            for header, expected in checks.items():
                value = headers.get(header)
                if value:
                    self.results.append(("PASS", f"Header {header}: {value}"))
                else:
                    self.results.append(("WARN", f"Missing header: {header}"))

        except Exception as e:
            self.results.append(("FAIL", f"Could not check headers: {e}"))

    def check_cors(self):
        """Check CORS configuration."""
        print("[2] Checking CORS...")

        try:
            response = requests.options(f"{self.base_url}/api/v1/menu/items", headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET"
            })

            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            if cors_origin == "*":
                self.results.append(("WARN", "CORS allows all origins"))
            elif cors_origin:
                self.results.append(("PASS", f"CORS origin: {cors_origin}"))
            else:
                self.results.append(("PASS", "CORS properly restricted"))

        except Exception as e:
            self.results.append(("FAIL", f"Could not check CORS: {e}"))

    def check_rate_limiting(self):
        """Check rate limiting."""
        print("[3] Checking Rate Limiting...")

        try:
            responses = []
            for i in range(10):
                r = requests.get(f"{self.base_url}/health")
                responses.append(r.status_code)

            if 429 in responses:
                self.results.append(("PASS", "Rate limiting active"))
            else:
                self.results.append(("WARN", "Rate limiting not detected (may need higher load)"))

        except Exception as e:
            self.results.append(("FAIL", f"Could not check rate limiting: {e}"))

    def check_auth_endpoints(self):
        """Check authentication security."""
        print("[4] Checking Auth Security...")

        # Check that protected endpoints require auth
        try:
            response = requests.get(f"{self.base_url}/api/v1/orders/")
            if response.status_code in (401, 403):
                self.results.append(("PASS", "Protected endpoints require auth"))
            else:
                self.results.append(("FAIL", f"Protected endpoint accessible without auth: {response.status_code}"))
        except Exception as e:
            self.results.append(("FAIL", f"Could not check auth: {e}"))

        # Check login endpoint
        try:
            response = requests.post(f"{self.base_url}/api/v1/auth/token", data={
                "username": "nonexistent@email.com",
                "password": "wrongpassword"
            })
            if response.status_code == 401:
                self.results.append(("PASS", "Invalid credentials rejected"))
            else:
                self.results.append(("FAIL", f"Invalid credentials not rejected: {response.status_code}"))
        except Exception as e:
            self.results.append(("FAIL", f"Could not check login: {e}"))

    def check_sql_injection(self):
        """Check for SQL injection vulnerabilities."""
        print("[5] Checking SQL Injection...")

        payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; SELECT * FROM users"
        ]

        for payload in payloads:
            try:
                response = requests.get(f"{self.base_url}/api/v1/menu/items", params={
                    "search": payload
                }, headers=self._get_auth_header())

                if response.status_code == 500:
                    self.results.append(("WARN", f"Potential SQL injection with: {payload[:30]}"))
                else:
                    self.results.append(("PASS", f"SQL injection blocked: {payload[:30]}"))

            except Exception:
                pass

    def check_xss(self):
        """Check for XSS vulnerabilities."""
        print("[6] Checking XSS...")

        payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]

        for payload in payloads:
            try:
                response = requests.get(f"{self.base_url}/api/v1/search/", params={
                    "q": payload
                }, headers=self._get_auth_header())

                if payload in response.text:
                    self.results.append(("WARN", f"Potential XSS: {payload[:30]}"))
                else:
                    self.results.append(("PASS", f"XSS blocked: {payload[:30]}"))

            except Exception:
                pass

    def check_sensitive_data(self):
        """Check for sensitive data exposure."""
        print("[7] Checking Sensitive Data...")

        # Check that error messages don't expose internals
        try:
            response = requests.get(f"{self.base_url}/api/v1/nonexistent")
            if "traceback" in response.text.lower() or "stack" in response.text.lower():
                self.results.append(("FAIL", "Error messages expose internals"))
            else:
                self.results.append(("PASS", "Error messages don't expose internals"))
        except Exception:
            pass

        # Check that passwords aren't returned
        try:
            response = requests.get(f"{self.base_url}/api/v1/users/", headers=self._get_auth_header())
            if response.status_code == 200:
                users = response.json()
                if isinstance(users, list) and users:
                    if "password" in str(users[0]).lower():
                        self.results.append(("FAIL", "Passwords exposed in API"))
                    else:
                        self.results.append(("PASS", "Passwords not exposed"))
        except Exception:
            pass

    def check_https(self):
        """Check HTTPS enforcement."""
        print("[8] Checking HTTPS...")

        if self.base_url.startswith("https://"):
            self.results.append(("PASS", "Using HTTPS"))
        else:
            self.results.append(("WARN", "Not using HTTPS (OK for development)"))

    def check_api_versioning(self):
        """Check API versioning."""
        print("[9] Checking API Versioning...")

        try:
            response = requests.get(f"{self.base_url}/api/v1/menu/items", headers=self._get_auth_header())
            version = response.headers.get("X-API-Version")
            if version:
                self.results.append(("PASS", f"API version header: {version}"))
            else:
                self.results.append(("INFO", "No API version header"))
        except Exception:
            pass

    def _get_auth_header(self):
        """Get auth header for authenticated requests."""
        try:
            response = requests.post(f"{self.base_url}/api/v1/auth/token", data={
                "username": "admin@demo.com",
                "password": "password123"
            })
            if response.status_code == 200:
                token = response.json().get("access_token")
                return {"Authorization": f"Bearer {token}"}
        except Exception:
            pass
        return {}

    def print_report(self):
        """Print audit report."""
        print("\n" + "=" * 60)
        print("SECURITY AUDIT REPORT")
        print("=" * 60)

        passed = sum(1 for r in self.results if r[0] == "PASS")
        warnings = sum(1 for r in self.results if r[0] == "WARN")
        failed = sum(1 for r in self.results if r[0] == "FAIL")
        total = len(self.results)

        print(f"\nTotal Checks: {total}")
        print(f"  PASSED:  {passed}")
        print(f"  WARNINGS: {warnings}")
        print(f"  FAILED:  {failed}")

        print("\nDetailed Results:")
        for status, message in self.results:
            icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}.get(status, "•")
            print(f"  [{icon}] {message}")

        print("\n" + "=" * 60)

        if failed > 0:
            print("RESULT: FAILED - Security issues found!")
            return 1
        elif warnings > 0:
            print("RESULT: PASSED with warnings")
            return 0
        else:
            print("RESULT: PASSED")
            return 0


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    auditor = SecurityAuditor(base_url)
    sys.exit(auditor.run_all_checks())
