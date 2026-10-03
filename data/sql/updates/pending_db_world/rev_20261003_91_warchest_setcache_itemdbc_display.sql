-- trikyn-live-ops#111: stream the warchest set-cache chest model (DisplayInfoID 812) to the native client.
-- item_template already carries 812 for the stock item-query/WDB path; the CoA item-patch stream
-- (AscensionCompat BuildItemPatchRows -> LoadItemPatchRows) sources from item_dbc, not item_template,
-- so the 26 set-caches need matching item_dbc rows to reach the native client's patched Item.dbc.
DELETE FROM `item_dbc` WHERE `ID` IN (195806,195820,203876,259256,274381,279176,279189,281589,283884,291843,303603,331102,331103,393473,398730,398732,398737,399259,399425,487319,525418,558230,734365,734385,1006524,8210184);
INSERT INTO `item_dbc` (`ID`, `ClassID`, `SubclassID`, `Sound_Override_Subclassid`, `Material`, `DisplayInfoID`, `InventoryType`, `SheatheType`) VALUES
(195806, 15, 0, -1, 2, 812, 0, 0),
(195820, 15, 0, -1, 2, 812, 0, 0),
(203876, 15, 0, -1, 2, 812, 0, 0),
(259256, 15, 0, -1, 2, 812, 0, 0),
(274381, 15, 0, -1, 2, 812, 0, 0),
(279176, 15, 0, -1, 2, 812, 0, 0),
(279189, 15, 0, -1, 2, 812, 0, 0),
(281589, 15, 0, -1, 2, 812, 0, 0),
(283884, 15, 0, -1, 2, 812, 0, 0),
(291843, 15, 0, -1, 2, 812, 0, 0),
(303603, 15, 0, -1, 2, 812, 0, 0),
(331102, 15, 0, -1, 2, 812, 0, 0),
(331103, 15, 0, -1, 2, 812, 0, 0),
(393473, 15, 0, -1, 2, 812, 0, 0),
(398730, 15, 0, -1, 2, 812, 0, 0),
(398732, 15, 0, -1, 2, 812, 0, 0),
(398737, 15, 0, -1, 2, 812, 0, 0),
(399259, 15, 0, -1, 2, 812, 0, 0),
(399425, 15, 0, -1, 2, 812, 0, 0),
(487319, 15, 0, -1, 2, 812, 0, 0),
(525418, 15, 0, -1, 2, 812, 0, 0),
(558230, 15, 0, -1, 2, 812, 0, 0),
(734365, 15, 0, -1, 2, 812, 0, 0),
(734385, 15, 0, -1, 2, 812, 0, 0),
(1006524, 15, 0, -1, 2, 812, 0, 0),
(8210184, 15, 0, -1, 2, 812, 0, 0);
