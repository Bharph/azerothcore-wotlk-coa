# DPS benchmark scaffolding (for trikyn-live-ops#99)

Scaffolding for a data-backed cross-spec damage comparison, built 2026-10-02. The measurement
mechanism is validated end-to-end; a defensible roster-wide ranking is the scheduled task in
trikyn-live-ops#99 (NOT done here).

## What works (validated)

The gameplay harness records `actual` for every `snapshot` and `assert` step in each case's
`result.json` (`steps[].actual`). To **measure** a value (not just pass/fail): use an `assert`
with `relative_to` and wide bounds (`min: 0, max: huge`) — it passes and records the delta as
`actual`. A scenario must contain at least one assertion, so pure-snapshot scenarios are rejected.

Per spec: snapshot `spell_damage_total(caster, spell, target)` + `spell_damage_count` baseline,
cast the ability N times, then wide-bound-assert the deltas; also assert `spell_cast_time_ms` for a
cast-speed throughput proxy (`damage_per_landed_cast / cast_time_s`).

## The blocker this scaffolding surfaced (the scope of #99)

Under a generic template only **mana casters** cast cleanly. Non-mana CoA classes fail
`SPELL_FAILED_NO_POWER` (85): they use custom/scripted resources that core `set_power` does not
fill, and core energy/focus caps at 100 so costly abilities cannot be afforded. Some abilities also
fail `SPELL_FAILED_LINE_OF_SIGHT` (47) or need facing/range for weapon strikes. A trustworthy
ranking therefore needs, per spec: custom-resource provisioning, correct range/facing/conditions,
multi-spell rotation summation (not a single ability), and gear normalization.

## Files

- `classify_damage_abilities.py` — reads the scenario corpus, and for each class's most-cast
  spells queries the DBC (`coa-dbc-viewer record`) and keeps only spammable single-target
  direct/weapon-damage abilities (Effect in {2,30,31,121,122,123}, `EffectImplicitTargetA` single
  enemy, `RecoveryTime`/`CategoryRecoveryTime` zero, no area target). Env: `DBC`, `SCENARIOS`,
  `VIEWER`, `OUT`.
- `generate_dps_scenarios.py` — emits `dps-sig-*.json` measurement scenarios (<=8 players each)
  from a spec table. Env: `OUT`.
- `dps-sig-a.json`, `dps-sig-b.json` — example generated scenarios (the measure-via-assert pattern).

## Run notes (harness constraints)

- Scenarios cap at 1..8 players; the generator splits automatically.
- Gameplay concurrency is `--gameplay-jobs` (not `--jobs`). Prefer the simulated clock (one
  worldserver) or `--gameplay-jobs 1`; multiple real-clock servers each recreate ~2100 bot
  characters on startup and time out.
- The runner's `server_modules_dir` must be empty at start (clear staged `*.conf` first).
- `set_power` value must be `<= GetMaxPower`; mana characters spawn full, so skip it for them.

The class id to display-name map is in `src/server/shared/SharedDefines.h` (the `CLASS_*` enum with
`// TITLE <name>`); `ChrClasses.dbc` names are empty for custom classes.
