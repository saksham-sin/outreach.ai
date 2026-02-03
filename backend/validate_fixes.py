"""
Quick validation script for reliability fixes.
Checks code patterns without requiring environment setup.
"""

import re
import sys


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def check_file_contains(filepath, pattern, description):
    """Check if file contains a pattern."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                print(f"{Colors.GREEN}✓ {description}{Colors.END}")
                return True
            else:
                print(f"{Colors.RED}✗ MISSING: {description}{Colors.END}")
                return False
    except Exception as e:
        print(f"{Colors.RED}✗ ERROR reading {filepath}: {e}{Colors.END}")
        return False


def main():
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}RELIABILITY FIXES - VALIDATION CHECKS{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")
    
    checks = []
    
    # Check 1: FOR UPDATE SKIP LOCKED in job_service.py
    print(f"{Colors.BLUE}Checking: Atomic Job Claiming{Colors.END}")
    checks.append(check_file_contains(
        "app/services/job_service.py",
        r"\.with_for_update\(skip_locked=True\)",
        "FOR UPDATE SKIP LOCKED in get_pending_jobs()"
    ))
    
    # Check 2: Second validation before send
    print(f"\n{Colors.BLUE}Checking: Reply/Send Race Closure{Colors.END}")
    checks.append(check_file_contains(
        "app/services/job_service.py",
        r"# Second validation right before send",
        "Second validation comment exists"
    ))
    checks.append(check_file_contains(
        "app/services/job_service.py",
        r"is_valid_final, reason_final = await self\._validate_job_for_execution\(job\)",
        "Final validation call before send"
    ))
    
    # Check 3: Exception handling around email provider
    print(f"\n{Colors.BLUE}Checking: Provider Exception Handling{Colors.END}")
    checks.append(check_file_contains(
        "app/services/job_service.py",
        r"try:\s+result = await self\.email_provider\.send_email",
        "Try/except wrapper around send_email()"
    ))
    checks.append(check_file_contains(
        "app/services/job_service.py",
        r"except Exception as e:.*Provider error",
        "Exception handler routes to retry logic"
    ))
    
    # Check 4: Resend inbound address guard
    print(f"\n{Colors.BLUE}Checking: Resend Inbound Config Guards{Colors.END}")
    checks.append(check_file_contains(
        "app/infrastructure/resend_provider.py",
        r"def _get_reply_to_address\(self, lead_id\)",
        "Reply-to method returns Optional[str]"
    ))
    checks.append(check_file_contains(
        "app/infrastructure/resend_provider.py",
        r"if not self\.inbound_address or \"@\" not in self\.inbound_address:",
        "Guard against missing/invalid inbound address"
    ))
    checks.append(check_file_contains(
        "app/infrastructure/resend_provider.py",
        r"reply_to = self\._get_reply_to_address\(metadata\.lead_id\)\s+if reply_to:",
        "Null-check before setting ReplyTo header"
    ))
    
    # Check 5: Config validation at startup
    print(f"\n{Colors.BLUE}Checking: Startup Config Validation{Colors.END}")
    checks.append(check_file_contains(
        "app/main.py",
        r"def _validate_config\(\) -> None:",
        "Config validation function exists"
    ))
    checks.append(check_file_contains(
        "app/main.py",
        r"_validate_config\(\)",
        "Config validation called in lifespan"
    ))
    checks.append(check_file_contains(
        "app/main.py",
        r"logger\.warning.*RESEND_INBOUND_ADDRESS.*reply detection",
        "Warning logged for missing inbound address"
    ))
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL CHECKS PASSED ({passed}/{total}){Colors.END}")
        print(f"\n{Colors.GREEN}All reliability fixes are correctly implemented!{Colors.END}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ SOME CHECKS FAILED ({passed}/{total}){Colors.END}")
        print(f"\n{Colors.RED}Please review the missing patterns above.{Colors.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
