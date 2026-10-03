-- Blackrock Caverns (map 645) is Cataclysm content mis-tagged expansion 1 / levels 58-70 in
-- LFGDungeons.dbc, so the Burning Crusade random can assign it: the map has no entrance trigger
-- (LFG teleport fails) and its door is Cataclysm-gated ("You must be level 68 to enter").
-- Remove it from the Dungeon Finder with the LFG map disable; the other 27 entrance-less
-- custom maps from the startup scan are catalogued separately (trikyn-live-ops).
DELETE FROM `disables` WHERE `sourceType` = 8 AND `entry` = 645;
INSERT INTO `disables` (`sourceType`, `entry`, `flags`, `params_0`, `params_1`, `comment`) VALUES
(8, 645, 0, '', '', 'Blackrock Caverns: Cataclysm map mis-tagged into the BC random pool, no entrance trigger');
