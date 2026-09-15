"""
E2E Authentication & Data Isolation Test Suite for NarrAI.
Fully database-agnostic: automatically runs against the active engine
(Microsoft SQL Server, PostgreSQL, or SQLite).

Tests:
- Register
- Database Persistence (Direct SQL verification)
- Duplicate Prevention
- Password Hashing (bcrypt verify, no plaintext)
- Login (Username & Email)
- Wrong Password Rejection
- Protected Routes & 401 handling
- JWT & Refresh Token Lifecycle
- Server-Side Logout (Token Blacklist in DB)
- Revoked Token Rejection
- Data Isolation (User A vs User B)
- IDOR Protection
- OAuth Provider Discovery
"""
import sys
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Set stdout encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend directory is in path and load .env
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from db.models import engine, User, Story, TokenBlacklist
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8000")
API_URL = f"{BASE_URL}/api"

def run_tests():
    print("=" * 60)
    print(f"NARR AI - E2E AUTH TEST SUITE (DATABASE: {engine.dialect.name.upper()})")
    print("=" * 60)
    
    results = {}
    
    # -------------------------------------------------------------
    # SETUP: Clean up previous test users if exist in DB
    # -------------------------------------------------------------
    with SessionLocal() as db:
        test_users = db.query(User).filter(User.username.in_(["usera_test", "userb_test"])).all()
        for u in test_users:
            db.query(Story).filter(Story.user_id == u.id).delete()
            db.delete(u)
        db.query(TokenBlacklist).delete()
        db.commit()

    # -------------------------------------------------------------
    # TEST 1: Register User A
    # -------------------------------------------------------------
    user_a_payload = {
        "username": "usera_test",
        "email": "user_a@narr-ai.local",
        "password": "SecurePassword123!",
        "name": "User Alpha"
    }

    print("\n[TEST 1] Register User A...")
    r = requests.post(f"{API_URL}/register", json=user_a_payload)
    print(f"Status: {r.status_code}, Body: {r.text}")
    assert r.status_code == 200, f"Register failed: {r.text}"
    results["REGISTER"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 2: Database Persistence & Password Security Check
    # -------------------------------------------------------------
    print(f"\n[TEST 2] Verifying User A directly in {engine.dialect.name.upper()} Database...")
    with SessionLocal() as db:
        user_row = db.query(User).filter(User.username == "usera_test").first()
        assert user_row is not None, "User A not found in database!"
        print(f"User ID: {user_row.id}, Username: {user_row.username}, Email: {user_row.email}, Name: {user_row.name}")
        assert user_row.password_hash != "SecurePassword123!", "SECURITY BREACH: Plaintext password stored!"
        assert user_row.password_hash.startswith("$2"), "Password is not bcrypt hashed!"
        print(f"Password hash confirmed bcrypt ($2... length={len(user_row.password_hash)})")
    results["DATABASE_PERSISTENCE"] = "PASS"
    results["PASSWORD_SECURITY"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 3: Duplicate Registration (Same Username)
    # -------------------------------------------------------------
    print("\n[TEST 3] Duplicate Registration Test...")
    r_dupe = requests.post(f"{API_URL}/register", json=user_a_payload)
    print(f"Status: {r_dupe.status_code}, Body: {r_dupe.text}")
    assert r_dupe.status_code == 400, "Duplicate username allowed!"
    results["DUPLICATE_PREVENTION"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 4: Login with Wrong Password
    # -------------------------------------------------------------
    print("\n[TEST 4] Login with Wrong Password...")
    r_wrong = requests.post(
        f"{API_URL}/login",
        data={"username": "usera_test", "password": "WrongPassword!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"Status: {r_wrong.status_code}, Body: {r_wrong.text}")
    assert r_wrong.status_code == 400, "Wrong password was accepted!"
    results["WRONG_PASSWORD_REJECTION"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 5: Login with Username
    # -------------------------------------------------------------
    print("\n[TEST 5] Login with Username...")
    r_login = requests.post(
        f"{API_URL}/login",
        data={"username": "usera_test", "password": "SecurePassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"Status: {r_login.status_code}")
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    auth_data_a = r_login.json()
    token_a = auth_data_a["access_token"]
    refresh_a = auth_data_a["refresh_token"]
    print(f"Access Token: {token_a[:30]}... (len={len(token_a)})")
    print(f"Refresh Token: {refresh_a[:30]}... (len={len(refresh_a)})")
    results["LOGIN_BY_USERNAME"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 6: Login with Email
    # -------------------------------------------------------------
    print("\n[TEST 6] Login with Email...")
    r_login_email = requests.post(
        f"{API_URL}/login",
        data={"username": "user_a@narr-ai.local", "password": "SecurePassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"Status: {r_login_email.status_code}")
    assert r_login_email.status_code == 200, f"Login by email failed: {r_login_email.text}"
    results["LOGIN_BY_EMAIL"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 7: Protected Route /api/me with Valid Token
    # -------------------------------------------------------------
    print("\n[TEST 7] Access /api/me with Token A...")
    r_me = requests.get(f"{API_URL}/me", headers={"Authorization": f"Bearer {token_a}"})
    print(f"Status: {r_me.status_code}, Body: {r_me.text}")
    assert r_me.status_code == 200
    me_data = r_me.json()
    assert me_data["username"] == "usera_test"
    assert me_data["email"] == "user_a@narr-ai.local"
    assert "password_hash" not in me_data, "SECURITY BREACH: password_hash leaked in /api/me!"
    results["PROTECTED_ROUTE_AUTHENTICATED"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 8: Protected Route /api/me without Token & with Bad Token
    # -------------------------------------------------------------
    print("\n[TEST 8] Access /api/me Unauthenticated...")
    r_no_tok = requests.get(f"{API_URL}/me")
    assert r_no_tok.status_code == 401, f"Expected 401, got {r_no_tok.status_code}"
    
    r_bad_tok = requests.get(f"{API_URL}/me", headers={"Authorization": "Bearer forged.token.value"})
    assert r_bad_tok.status_code == 401, f"Expected 401, got {r_bad_tok.status_code}"
    print("Unauthenticated & forged tokens rejected with 401 as expected.")
    results["UNAUTHENTICATED_REJECTION"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 9: Refresh Token Flow
    # -------------------------------------------------------------
    print("\n[TEST 9] Refresh Token Flow...")
    r_refresh = requests.post(f"{API_URL}/refresh", json={"refresh_token": refresh_a})
    print(f"Status: {r_refresh.status_code}")
    assert r_refresh.status_code == 200, f"Refresh failed: {r_refresh.text}"
    refreshed_data = r_refresh.json()
    new_token_a = refreshed_data["access_token"]
    assert new_token_a != token_a, "Refreshed token is identical to old token!"
    
    # Test new token works
    r_me_new = requests.get(f"{API_URL}/me", headers={"Authorization": f"Bearer {new_token_a}"})
    assert r_me_new.status_code == 200
    print("Token refreshed and verified successfully.")
    results["REFRESH_TOKEN"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 10: Server-Side Logout & Token Blacklist
    # -------------------------------------------------------------
    print("\n[TEST 10] Server-Side Logout & Revocation...")
    r_logout = requests.post(f"{API_URL}/logout", headers={"Authorization": f"Bearer {new_token_a}"})
    print(f"Status: {r_logout.status_code}, Body: {r_logout.text}")
    assert r_logout.status_code == 200
    
    # Verify the logged-out token is now REJECTED
    r_revoked = requests.get(f"{API_URL}/me", headers={"Authorization": f"Bearer {new_token_a}"})
    print(f"Access with revoked token status: {r_revoked.status_code}")
    assert r_revoked.status_code == 401, "SECURITY BREACH: Revoked token was still accepted!"
    print("Logged-out token correctly blacklisted and rejected with 401.")
    results["SERVER_SIDE_LOGOUT"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 11: Register User B & Test Data Isolation
    # -------------------------------------------------------------
    print("\n[TEST 11] Register User B & Data Isolation Test...")
    user_b_payload = {
        "username": "userb_test",
        "email": "user_b@narr-ai.local",
        "password": "SecurePassword123!",
        "name": "User Beta"
    }
    r_reg_b = requests.post(f"{API_URL}/register", json=user_b_payload)
    assert r_reg_b.status_code == 200
    
    # Login as User A again (fresh token)
    r_login_a2 = requests.post(
        f"{API_URL}/login",
        data={"username": "usera_test", "password": "SecurePassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token_a_fresh = r_login_a2.json()["access_token"]
    
    # Login as User B
    r_login_b = requests.post(
        f"{API_URL}/login",
        data={"username": "userb_test", "password": "SecurePassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token_b = r_login_b.json()["access_token"]
    
    # Insert a test story for User A via SQLAlchemy Session
    with SessionLocal() as db:
        user_a = db.query(User).filter(User.username == "usera_test").first()
        test_story = Story(
            user_id=user_a.id,
            session_id=f"test_session_{int(datetime.utcnow().timestamp())}",
            story_content="Nội dung bí mật của User A không ai được xem.",
            word_count=12,
            created_at=datetime.utcnow()
        )
        db.add(test_story)
        db.commit()
        db.refresh(test_story)
        story_a_id = test_story.id
    
    # User A views their stories
    r_stories_a = requests.get(f"{API_URL}/stories", headers={"Authorization": f"Bearer {token_a_fresh}"})
    stories_a = r_stories_a.json().get("stories", [])
    story_ids_a = [s["id"] for s in stories_a]
    assert story_a_id in story_ids_a, "User A cannot see their own story!"
    
    # User B views their stories -> must NOT contain User A's story!
    r_stories_b = requests.get(f"{API_URL}/stories", headers={"Authorization": f"Bearer {token_b}"})
    stories_b = r_stories_b.json().get("stories", [])
    story_ids_b = [s["id"] for s in stories_b]
    assert story_a_id not in story_ids_b, "SECURITY BREACH: User B can see User A's story in list!"
    print(f"Story list isolation confirmed: User A stories={story_ids_a}, User B stories={story_ids_b}")
    results["DATA_ISOLATION_LIST"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 12: IDOR Protection Test
    # -------------------------------------------------------------
    print("\n[TEST 12] IDOR Attack Simulation: User B requests User A's story directly...")
    r_idor = requests.get(f"{API_URL}/stories/{story_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    print(f"IDOR Status: {r_idor.status_code}, Body: {r_idor.text}")
    idor_data = r_idor.json()
    assert idor_data.get("status") == "error", "SECURITY BREACH: User B was able to fetch User A's story directly!"
    print("IDOR access blocked: 'Không tìm thấy truyện hoặc không có quyền xem'")
    results["IDOR_PROTECTION"] = "PASS"
    
    # -------------------------------------------------------------
    # TEST 13: OAuth Providers Endpoint
    # -------------------------------------------------------------
    print("\n[TEST 13] OAuth Provider Discovery Endpoint...")
    r_providers = requests.get(f"{API_URL}/auth/providers")
    print(f"Status: {r_providers.status_code}, Body: {r_providers.text}")
    assert r_providers.status_code == 200
    providers = r_providers.json().get("providers", [])
    print(f"Available OAuth providers: {providers}")
    results["OAUTH_DISCOVERY"] = "PASS"

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print(f"ALL TESTS PASSED SUCCESSFULLY ON {engine.dialect.name.upper()}!")
    print("=" * 60)
    for test_name, status in results.items():
        print(f"  {test_name:30}: {status}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
