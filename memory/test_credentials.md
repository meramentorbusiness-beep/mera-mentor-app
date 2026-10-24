# Test credentials (preview only)

Auth is Google OAuth only — there is no password login. For automated testing,
inject a session row directly into the preview PostgreSQL database.

## Preview admin/test user
- email: test@meramentor.in
- name: Test Student
- role: admin
- user id: 11111111-1111-1111-1111-111111111111
- referral_code: TESTREF001

## Session cookie to use in curl / Playwright
- cookie name: `session_token`
- value: `preview-test-session-token-abc123`

Example: `curl -s $URL/api/auth/me -H "Cookie: session_token=preview-test-session-token-abc123"`

## Re-create if the DB is reset
```sql
INSERT INTO users (id,email,name,role,referral_code,streak,xp,status,email_verified,created_at,updated_at)
VALUES ('11111111-1111-1111-1111-111111111111','test@meramentor.in','Test Student','admin','TESTREF001',0,0,'active',true,now(),now())
ON CONFLICT (email) DO NOTHING;
INSERT INTO user_sessions (id,user_id,session_token,expires_at,created_at)
VALUES ('22222222-2222-2222-2222-222222222222','11111111-1111-1111-1111-111111111111','preview-test-session-token-abc123', now() + interval '30 days', now())
ON CONFLICT (session_token) DO NOTHING;
```

## Preview environment notes (this fork)
- `backend/.env` is gitignored and was missing after the fork. Recreated with
  `DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/meramentor` (local PG 15 cluster,
  started via `pg_ctlcluster 15 main start`). `PREVIEW_POSTGRES_DATA` must stay unset when
  using the system cluster, otherwise startup aborts.
- `frontend/.env` recreated with `REACT_APP_BACKEND_URL=https://mera-mentor-app.preview.emergentagent.com`.
