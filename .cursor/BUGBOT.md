# Bugbot review guidance — `trikyn` branch (Trikyn build/ship source)

You are reviewing pull requests on the **Bharph fork** of AzerothCore-WotLK-CoA.
This repo runs a two-branch model:

- **`main`** — a pristine mirror of upstream JS Main (`jealous-sound/azerothcore-wotlk-coa`).
  Refreshed by an external process; **not** hand-edited here.
- **`trikyn`** — `main` **plus a clean stack of Trikyn-only patches**. This is the
  branch PTR builds and ships to the Live realm from. It is **never PR'd upstream**.

You are an **independent second reviewer**. PTR-Claude performs the rebase and opens
PRs; it also resolves conflicts. You do **not** open PRs or resolve conflicts — you
review and comment.

## Scope your review to Trikyn-touched files

Concentrate on the delta between `main` and `trikyn` (the patch stack), typically:

- `modules/mod-ah-bot/**` — vendored AuctionHouseBot (compiled module).
- `.gitignore` — the per-module un-ignore lines (`!/modules/mod-*/`).
- `.cursor/**` — this guidance.
- **(future)** `env/dist/etc/**` `.conf` overrides migrated onto the branch
  (vanity / AutoProgression / AllowRemoteClients set), and future compiled
  modules / core C++ patches.

Do not re-litigate unmodified upstream `main` code — that is JS Main's concern.

## What to flag hard

1. **Clash-alarm PRs** (title contains "clash alarm", branch `sync/trikyn-rebase-conflict-*`):
   these contain committed conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`, diff3).
   Verify every marker is resolved before the resolution lands, that the **Trikyn
   intent is preserved** (the Trikyn patch is not silently dropped in favor of the
   upstream side), and that no marker text survives in shipped source/SQL/conf.

2. **Layer leakage** — these must **NOT** appear on `trikyn` (they live in deploy-time
   layers, not the branch):
   - Trikyn deploy SQL data (the Live `sql/` overlay).
   - Env overrides / `docker-compose.override.yml`.
   - `patch-C.MPQ` or any client-side launcher files.
   A vendored module's **own** bundled `data/sql/**` (schema/reference data it ships)
   is part of the module and is allowed.

3. **Module wiring** — vendored modules must build via AzerothCore's `modules/*/src`
   glob. Flag a new module dir that is un-ignored but ships no `src/`, or a `.gitignore`
   un-ignore that does not match an actual vendored directory.

4. **Secrets** — never any `.env`, tokens, private keys, DB passwords, or internal
   GitHub URLs in a diff.

## Notes / lower priority

- The vendored `mod-ah-bot` SQL (`mod_auctionhousebot.sql` DDL, the
  `auctionhousebot_professionItems.sql` phpMyAdmin dump) does **not** pass
  AzerothCore SQL codestyle (MyISAM, dump headers, INSERT-without-DELETE). This is
  **accepted** — it is faithful upstream module data on a branch that is never
  upstreamed. Do not raise it as a blocker.
- C++ style: 4-space indent, ≤120 cols, LF, UTF-8 (`.editorconfig`).
