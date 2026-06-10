# Merge Handoff — AUDIT_2026-06-10 Remediation PRs

> For the agent/human merging the 18 PRs that remediate `AUDIT_2026-06-10.md`.
> Assumes no prior session context. Written 2026-06-10.

## Context

18 PRs remediate a 5-domain security audit on **`hackagora/archimedes-arcadia`**
(gh resolves PRs/issues under `a-apin/archimedes`). All authored by Önder;
branches `onder/<name>`; all base `main`.

**Repo merge rules (from CLAUDE.md — non-negotiable):**

- **Merge commits ONLY.** Squash + rebase-merge are disabled in repo settings.
  Use `gh pr merge <n> --merge` (or the UI "Create a merge commit").
- **`main` moves continuously and every merge auto-deploys** (build-on-deploy →
  live EC2 via `deploy.yml`). Merge in small batches; rebase a branch onto
  `main` right before merging it and confirm CI green.
- **Never force-push `main`.** Force-pushing a *feature* branch (to rebase) is
  fine. Delete each branch after merge.
- **No branch protection exists yet** (audit finding #10 → issue #519), so
  merges aren't gated automatically. Enforce the convention manually:
  **1 approving review for normal changes, 2 (incl. Chuan) for contract
  changes.**

**CI:** `quality-gate.yml` hard-blocks on `pytest -m "not integration"` +
ruff format/critical-rules. It *also* posts an **informational** ruff count
(~22) and eslint count (~1) that are the **pre-existing repo-wide baseline, not
introduced by these PRs** — do not block on them (see the clarifying comment on
PR #498). `complexity-gate.yml` is informational only.

## Merge order

### Batch 1 — Quant rigor (Önder's lane; lowest risk; unit-tested locally). Reviewer: Dan.

| PR | Branch | Touches |
| --- | --- | --- |
| #499 | `onder/stockbench-dsr-tuple` | adapter.py + test (1-line tuple swap) |
| #503 | `onder/walkforward-docstring-honesty` | rigor_evaluator.py (docstring) |
| #504 | `onder/pbo-coupling-limitation` | rigor_evaluator.py (docstring) |
| #498 | `onder/rigor-generate-deflation` | generation_pipeline.py + tests |
| #500 | `onder/fusion-gate-oos-trials` | fusion_evaluator.py + tests |
| #502 | `onder/dsr-effective-n-correlation` | rigor_evaluator.py (effective-N math) + tests |
| #501 | `onder/oos-cliff-denominator` | selection_bias_routes.py + tests |

**Conflict coupling (verified disjoint — rebase the second of each pair):**

- **#502, #503, #504 all touch `rigor_evaluator.py`** but in *different
  functions* (`_dsr_from_stats`/`compute_average_pairwise_correlation` docstring
  vs `compute_oos_sharpe`/module docstring vs `compute_pbo` docstring). Auto-merge;
  rebase the later ones onto `main` and re-confirm green.
- **#501 and #502 both touch `selection_bias_routes.py`** — #501 the gate loop
  (~L159-182), #502 a one-line comment (~L133-135). Far apart → auto-merge;
  rebase the second.

Verify each on a cold checkout: `PYTHONPATH=backend pytest <test file from the PR body> -q`.

### Batch 2 — Backend + Auth. Reviewers: Daniel R. (backend), Marten (UI half of #512).

| PR | Branch | Note |
| --- | --- | --- |
| #518 | `onder/chat-async-offload` | `chat_routes.py` only — isolated, safe |
| #512 | `onder/siwe-ui-and-message-binding` | `auth_siwe.py` + tests + `WalletConnect.jsx`. Force-pushed during self-audit (mandatory domain/chain/expiry binding); current HEAD correct, 29 auth tests pass |
| #511 | `onder/siwe-gate-vault-endpoints` | `vaults_routes.py` + test. Funds-adjacent |

**Soft dependency:** #511 adds SIWE gates to vault endpoints; #512 makes SIWE
actually run in the UI. Land **#512 before or with #511** so the gates aren't
stranded (no UI user could authenticate otherwise). Not a hard merge dependency.

### Batch 3 — Frontend.

| PR | Branch | Note |
| --- | --- | --- |
| #516 | `onder/frontend-deposit-input-hardening` | `VaultDetail.jsx` + `DepositFlow.jsx`. **Not built/linted locally (no node toolchain).** Require CI `npm run lint` green + Marten to click through the deposit flow before merge |

### Batch 4 — Infra (REQUIRES CHUAN; merging ≠ applying). Operator: Chuan.

| PR | Branch | What merging does |
| --- | --- | --- |
| #513 | `onder/dockerignore` | Takes effect on next deploy (image rebuild). Low risk |
| #517 | `onder/nginx-security-headers-http` | Takes effect on next deploy. **Not `nginx -t`'d locally** — Chuan validates |
| #514 | `onder/close-ssh-port-22` | **Merging does NOT apply it** — Chuan must `terraform plan && apply` |
| #515 | `onder/rotate-hardcoded-db-password` | **Merging does NOT apply it.** `user-data.sh` only runs on a *new* instance boot; Chuan must `terraform apply` **and rotate the live DB password out-of-band** (`ALTER USER` — the running Postgres volume still holds the old password). Force-pushed during self-audit to fix a Terraform `templatefile()` escaping bug; current HEAD correct |

`deploy.yml` rebuilds the docker stack on push to `main` but does **not** run
`terraform apply`. So #513/#517 self-apply on the next deploy; #514/#515 need
Chuan's manual terraform/instance action.

### Batch 5 — Contract (LAST; hard gate). Reviewers: Chuan + 1, two approvals.

| PR | Branch | Gate |
| --- | --- | --- |
| #505 | `onder/vault-withdraw-allowance` | `Vault.sol` + `Vault.t.sol`. **DO NOT MERGE** until Chuan reviews, `cd contracts && forge test --match-contract VaultTest` passes (**not compiled locally** — no forge/OZ libs in author env), and a redeploy plan exists (the deployed Vault must be replaced; re-cache ABIs in `contracts/abis/` after) |

## Per-PR checklist

1. Confirm CI hard-gates green.
2. If not mergeable, rebase the branch onto `origin/main` and re-push (force-push
   the *feature* branch only).
3. Get the required review(s).
4. `gh pr merge <n> --merge --delete-branch`.
5. Quant batch: after each merge, rebase the remaining
   rigor_evaluator/selection_bias_routes branches and re-confirm green.

## Do NOT

- Do not add `!minor`/`!version-release` to PR titles — these are security
  fixes/bugfixes and correctly default to patch bumps.
- Do not action the 11 companion **issues** (#506–#510, #519–#524) — follow-up
  work for owners.
- Do not merge the contract or terraform-apply items without Chuan.

## After all merges

- **Flag to Chuan:** live DB password rotation (#515), `terraform apply` for
  #514/#515, contract redeploy for #505.
- 11 issues remain open for the team.
- `AUDIT_2026-06-10.md` is untracked and intentionally not part of any PR.
