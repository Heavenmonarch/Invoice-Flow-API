import pytest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
import uuid


def test_hash_password_returns_string():
    hashed = hash_password("Test@1234")
    assert isinstance(hashed, str)
    

def test_hash_password_is_not_plain_text():
    password= "Test@1234"
    hashed = hash_password(password)
    assert hashed != password
    

def test_verify_password_correct():
    password = "Test@!234"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    
    
def test_verify_password_wrong():
    hashed = hash_password("Test@1234")
    assert verify_password("Test@12345", hashed) is False
    

def test_hash_same_password_produces_different_hashes():
    hashed1 = hash_password("Test@1234")
    hashed2 = hash_password("Test@1234")
    assert hashed1 != hashed2


def test_create_access_token_returns_string():
    token = create_access_token(subject=uuid.uuid4())
    assert isinstance(token, str)
    
    
def test_create_access_token_with_claims():
    user_id = uuid.uuid4()
    token = create_access_token(
        subject=user_id,
        extra_claims={
            "role": "admin",
            "org_id": str(uuid.uuid4()),
        },
    )
    payload = decode_token(token)
    assert payload["role"] == "admin"
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    
    
def test_create_refresh_token():
    token = create_refresh_token(subject=uuid.uuid4)
    payload = decode_token(token)
    assert payload["type"] == "refresh"
    
    
def test_decode_token_invalid_raises():
    with pytest.raises(ValueError, match="Invalid token"):
        decode_token("this.is.not.a.valid.token")


def test_decode_token_tampered_raises():
    token = create_access_token(subject=uuid.uuid4())
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(ValueError):
        decode_token(tampered)
    
    