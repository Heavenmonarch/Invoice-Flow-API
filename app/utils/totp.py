import pyotp
import qrcode
import io
import json
import secrets
import hashlib
import base64
import logging

logger = logging.getLogger(__name__)

RECOVERY_CODE_COUNT = 8
ISSUER_NAME = "CommissionTrack"


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str, organization_name: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=email,
        issuer_name=f"{ISSUER_NAME} ({organization_name})",
    )


def generate_qr_code(uri: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def verify_totp_code(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def generate_recovery_codes() -> tuple[list[str], list[str]]:
    plain_codes = []
    hashed_codes = []

    for _ in range(RECOVERY_CODE_COUNT):
      
        code = "-".join([
            secrets.token_hex(2).upper()
            for _ in range(3)
        ])
        plain_codes.append(code)
        hashed_codes.append(
            hashlib.sha256(code.encode()).hexdigest()
        )

    return plain_codes, hashed_codes


def verify_recovery_code(
    stored_hashed_codes: str,
    submitted_code: str,
) -> tuple[bool, str]:
    try:
        hashed_list = json.loads(stored_hashed_codes)
    except (json.JSONDecodeError, TypeError):
        return False, stored_hashed_codes

    submitted_hash = hashlib.sha256(
        submitted_code.strip().upper().encode()
    ).hexdigest()

    if submitted_hash in hashed_list:
        hashed_list.remove(submitted_hash)
        return True, json.dumps(hashed_list)

    return False, stored_hashed_codes