"""
Multi-Factor Authentication (MFA) Implementation
Control ID: MFA-001
Frameworks: SOC 2 (CC6.1), HIPAA (§164.312(d)), PCI-DSS (Req 8.3), GDPR (Art 32)

TOTP (Time-based One-Time Password) implementation for application-level MFA.

Dependencies:
    pip install pyotp qrcode pillow

Usage:
    from mfa_implementation import MFAService

    # Setup MFA for user
    secret = MFAService.generate_secret()
    uri = MFAService.get_provisioning_uri(secret, user_email, issuer="MyApp")
    qr_code = MFAService.generate_qr_code(uri)

    # Verify token
    is_valid = MFAService.verify_token(secret, user_provided_token)
"""

import pyotp
import qrcode
from io import BytesIO
from typing import List, Optional


class MFAService:
    """Multi-Factor Authentication service using TOTP"""

    @staticmethod
    def generate_secret() -> str:
        """
        Generate a random base32 secret for TOTP

        Returns:
            32-character base32 string
        """
        return pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(secret: str, user_email: str, issuer: str) -> str:
        """
        Generate provisioning URI for QR code

        Args:
            secret: TOTP secret key
            user_email: User's email address
            issuer: Application name

        Returns:
            otpauth:// URI for authenticator apps
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user_email, issuer_name=issuer)

    @staticmethod
    def generate_qr_code(provisioning_uri: str) -> bytes:
        """
        Generate QR code image from provisioning URI

        Args:
            provisioning_uri: otpauth:// URI

        Returns:
            PNG image bytes
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def verify_token(secret: str, token: str, window: int = 1) -> bool:
        """
        Verify TOTP token. Caller must reject a token already used in its
        time step (replay) and rate-limit attempts.

        Args:
            secret: User's TOTP secret
            token: 6-digit token from authenticator app
            window: Time window for validity (default 1 = ±30 seconds)

        Returns:
            True if token is valid, False otherwise
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)

    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """
        Generate one-time backup codes for account recovery. Show once;
        store only salted hashes; invalidate each code on use.

        Args:
            count: Number of backup codes to generate

        Returns:
            List of backup codes (8 characters each)
        """
        import secrets

        return [secrets.token_hex(4).upper() for _ in range(count)]


# Example usage
if __name__ == "__main__":
    # Setup MFA for a new user
    user_email = "user@example.com"
    issuer = "MyApp"

    # Generate secret
    secret = MFAService.generate_secret()
    print(f"Secret generated ({len(secret)} chars)")
    print("Store it encrypted at rest (KMS); never log it.")

    # Generate provisioning URI (embeds the secret; demo only, never log in production)
    uri = MFAService.get_provisioning_uri(secret, user_email, issuer)
    print(f"\nProvisioning URI (add to authenticator): {uri}")

    # Generate QR code
    qr_bytes = MFAService.generate_qr_code(uri)
    print(f"\nQR code generated ({len(qr_bytes)} bytes)")
    print("Display this QR code to the user for scanning")

    # Generate backup codes (show to user once, persist only hashes)
    backup_codes = MFAService.generate_backup_codes()
    print(f"\n{len(backup_codes)} backup codes generated (masked):")
    for i, code in enumerate(backup_codes, 1):
        print(f"  {i}. ****{code[-2:]}")

    # Verify token (example)
    test_token = input("\nEnter 6-digit token from authenticator app: ")
    is_valid = MFAService.verify_token(secret, test_token)

    if is_valid:
        print("✅ Token is valid!")
    else:
        print("❌ Token is invalid")
