# Progress

## Status
In Progress — Issue #181 (User-data minimization) complete. Deployed to main.

## Tasks

### Completed (this session)
- **#181** — User-data minimization: encrypt email at rest (Fernet), scrub from logs, owner-only API echo. 12 new privacy tests + updated 12 route tests. 402 total tests green.

### Completed (prior sessions)
- **#150** — DepositFlow stepper modal: 3-step USDC.approve → vault.deposit → setTargetAllocations
- **#174** — `/api/health/amm` endpoint + agent_runner VaultFactory poll
- **#172** — WelcomeProfileModal + personalized header
- **#167** — Generate page single input + backend auto-route
- **#177** — Nginx security headers
- **#178** — CORS lockdown
- **#166** — Landing sidebar parity + CTA differentiation
- **#169** — Corpus default Catalog tab + plain-English labels
- **#170** — Reasoning verify arcscan enhancement
- **#171** — Portfolio traces honesty
- **#173** — Agents subpackage refactor

## Files Changed (this session — Issue #181)
- `backend/archimedes/services/email_crypto.py` — NEW: Fernet-based email encrypt/decrypt (env-var key)
- `backend/archimedes/services/log_scrubber.py` — NEW: PII field scrubber for log output
- `backend/archimedes/api/user_routes.py` — Owner-only echo via X-Wallet-Address header; encrypt on write, decrypt on owner read; log scrubbing
- `backend/archimedes/api/limiter.py` — Disabled in TESTING mode
- `backend/archimedes/models/user_profile.py` — Updated docstring noting encryption
- `backend/tests/conftest.py` — Set TESTING=1 before imports
- `backend/tests/test_user_routes.py` — Rewritten: unique wallets, owner/anonymous assertions
- `backend/archimedes/tests/test_user_profile_privacy.py` — NEW: 12 tests for encryption, scrubbing, owner-only echo

## Validation
- Backend tests: 402 passed, 0 failed, 2 skipped (pre-existing Redis flakes)
- Email encryption: round-trip verified (Fernet tokens differ from plaintext, decrypt back correctly)
- Log scrubbing: grep confirms 0 raw email/display_name in log output
- Owner-only: anonymous GET returns email=None, display_name=None; owner GET returns decrypted values
- Rate limiter: properly disabled in test mode via TESTING env var

## Open items
- Issues still assigned to t2o2: #179 (rate limiting), #180 (dependabot), #176 (SSM secrets), #175 (E2E smoke), #165–#153 (Track C/E intelligence)
