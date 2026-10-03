-- The MaxExpansion=2 unlock serves the Burning Crusade random dungeon (LFGDungeons 417) and its
-- specific dungeons, but the repack-aligned world data carries no Outland entrance triggers:
-- lfg_dungeon_template holds classic rows only and areatrigger_teleport has no rows for the BC
-- instance maps, so LFGMgr's areatrigger fallback fails and an assigned BC dungeon cannot
-- teleport the group ("You don't have the right teleport location"). Restore the stock
-- AzerothCore entrance triggers for the BC dungeon maps; walk-in instance entry uses the same rows.
DELETE FROM `areatrigger_teleport` WHERE `ID` IN (4151,4152,4153,4320,4321,4363,4364,4365,4404,4405,4406,4407,4467,4468,4469,4887);
INSERT INTO `areatrigger_teleport` (`ID`, `Name`, `target_map`, `target_position_x`, `target_position_y`, `target_position_z`, `target_orientation`) VALUES
(4151,'The Shattered Halls (Entrance)',540,-40.8716,-19.7538,-13.8065,1.11133),
(4152,'The Blood Furnace (Entrance)',542,-3.9967,14.6363,-44.8009,4.88748),
(4153,'Magtheridon''s Lair (Entrance)',544,187.843,35.9232,67.9252,4.79879),
(4320,'Caverns Of Time, Black Morass (Entrance)',269,-1496.24,7034.7,32.5619,1.75699),
(4321,'Caverns Of Time, Old Hillsbrad Foothills (Entrance)',560,2741.87,1315.25,14.0423,2.96016),
(4363,'The Underbog (Entrance)',546,9.71391,-16.2008,-2.75334,5.57082),
(4364,'The Steamvault (Entrance)',545,-13.8425,6.7542,-4.2586,0),
(4365,'The Slave Pens (Entrance)',547,120.101,-131.957,-0.801547,1.47574),
(4404,'Auchenai Crypts (Entrance)',558,-21.8975,0.16,-0.1206,0.0353412),
(4405,'Mana Tombs (Entrance)',557,0.0191,0.9478,-0.9543,3.03164),
(4406,'Sethekk Halls (Entrance)',556,-4.6811,-0.0930796,0.0062,0.0353424),
(4407,'Shadow Labyrinth (Entrance)',555,0.488033,-0.215935,-1.12788,3.15888),
(4467,'The Botanica (Entrance)',553,40.0395,-28.613,-1.1189,2.35856),
(4468,'The Arcatraz (Entrance)',552,-1.23165,0.0143459,-0.204293,0.0157123),
(4469,'The Mechanar (Entrance)',554,-28.906,0.680314,-1.81282,0.0345509),
(4887,'Magisters'' Terrace (Entrance)',585,7.09,-0.45,-2.8,0.05);
