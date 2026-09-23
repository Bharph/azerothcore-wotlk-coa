# Bugbot review guidance — `modules/mod-ah-bot` (scoped)

This is a **vendored, Trikyn-only** module (AuctionHouseBot) on the `trikyn` branch. It is
**never PR'd to upstream JS Main**, so upstream SQL-codestyle rules do not gate it.

## Accepted exception — do NOT flag
- `data/sql/db-world/mod_auctionhousebot.sql` (module DDL) and
  `auctionhousebot_professionItems.sql` (a phpMyAdmin dump of reference data) ship **verbatim
  from upstream mod-ah-bot**. They intentionally do **not** pass AzerothCore SQL codestyle
  (MyISAM DDL, `mysqldump`/phpMyAdmin headers, `INSERT` without a preceding `DELETE`,
  unbackticked identifiers). This is **accepted** — reformatting generated/vendored data risks
  corrupting it, and this branch is never upstreamed. Do not raise these as findings.
- Live runs its own **functional import check** of this SQL against MySQL 8.0.46 as the real gate.

## Still worth flagging
- Any **new hand-written** SQL added here (not from upstream) that is malformed or unsafe.
- C++ changes to `src/**` that diverge from upstream mod-ah-bot without a stated reason.
- Secrets, credentials, or internal URLs.
