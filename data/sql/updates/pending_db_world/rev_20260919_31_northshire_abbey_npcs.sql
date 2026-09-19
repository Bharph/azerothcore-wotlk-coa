-- Ascension's Northshire Abbey quest givers.
-- Name, subname, creature type, model and health modifier come from the Ascension creature cache. The
-- display IDs 652000-652002 exist only in the Ascension client data. Level, faction and NPC flags are not
-- in the archive and are assumptions: level matches the Abbey quests, faction 12 is Stormwind and 35 is
-- friendly to all. There are no spawns yet, so the NPCs do not appear in game.
REPLACE INTO `creature_template` (`entry`, `name`, `subname`, `minlevel`, `maxlevel`, `faction`, `npcflag`, `unit_flags`, `unit_flags2`, `type`, `HealthModifier`, `flags_extra`) VALUES
(161700, 'Bianca Spada', NULL, 6, 6, 12, 2, 768, 2048, 7, 0.96, 2),
(161701, 'Moroi Spada', 'Seminarian of Northshire Abbey', 6, 6, 12, 2, 768, 2048, 7, 0.98, 2),
(161702, 'Sister Alma', 'Ancient Priestess of Northshire', 6, 6, 35, 2, 768, 2048, 6, 1, 2);

REPLACE INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(161700, 0, 652000, 1, 1, 0),
(161701, 0, 652001, 1, 1, 0),
(161702, 0, 652002, 1, 1, 0);
