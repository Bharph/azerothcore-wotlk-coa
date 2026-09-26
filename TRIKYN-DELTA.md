# TRIKYN-DELTA

Trikyn-only changes that live on the `trikyn` branch and must **survive every JS Main sync**.
`trikyn` is `main` (a pristine mirror of upstream JS Main) plus a patch stack; anything recorded
here is ours, is not upstream, and can be silently reverted or clobbered when JS Main advances a
file we also touch. On every sync, conflict-watch each entry below and re-apply it if it was lost.

This file tracks the deltas that are easy to lose against a moving upstream — overlays inside
JS-Main-owned files. It is not a full changelog of the patch stack (see `git log main..trikyn`
for the discrete commits).

## Module source-code overlays

These edit files owned by JS Main modules. A future upstream change to the same module can conflict
with or overwrite them, and a module re-vendor drops them entirely, so they are the highest-risk
deltas to lose.

### mod-dynamic-xp — party bots inherit the group leader's `.xp` rate

- **File:** `modules/mod-dynamic-xp/src/dynamicxp.cpp` (the `OnGiveXP` path:
  `BotsInheritLeader()`, `RecipientPreset()`, and the `RecipientPreset(player)` call in
  `OnPlayerGiveXP`).
- **Config:** `modules/mod-dynamic-xp/conf/dynamicxp.conf.dist` adds
  `Dynamic.XP.Bots.InheritLeader = 1` (default on). The Live/PTR runtime `dynamicxp.conf` gets the
  same key appended by `apply_trikyn_module_conf.sh` so a promotion does not log a "Missing
  property" warning.
- **What it does:** when a bot (`GetSession()->IsBot()`) gains XP while in a party or raid, it uses
  the group leader's effective preset (the leader's own `.xp` choice if set, else the realm rate)
  instead of its own. The band curve still reads the bot's own level. Gated behind both
  `Dynamic.XP.Preset.PlayerChoice` and `Dynamic.XP.Bots.InheritLeader`; live-editable via
  `.reload config`. Real players are never affected; solo bots, bots in a bot-led group, and bots
  whose leader is offline fall through to the stock per-character behaviour.
- **What breaks if lost:** party bots stop matching the leader's `.xp` — a player who set `.xp 7`
  levels far ahead of their summoned party, which gains at the realm default band curve again.
- **Conflict-watch:** on **every** JS Main sync, watch `mod-dynamic-xp` for upstream changes to
  `dynamicxp.cpp` or the conf, and after any `mod-dynamic-xp` re-vendor. If the overlay is
  clobbered, re-apply it from the `trikyn-overlay(dynamic-xp)` commit.
