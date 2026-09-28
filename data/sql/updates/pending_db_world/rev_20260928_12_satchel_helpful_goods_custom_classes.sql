-- Satchel of Helpful Goods rolls empty for every CoA custom class (trikyn-live-ops#28).
--
-- The satchel item is granted by the random-dungeon reward quest regardless of class, but its
-- contents come from reference loot templates 10036-10061, each gated by a CONDITION_CLASS (15)
-- mask that enumerates core classes 1-11 only. Custom classes 12-32 match no armor group in any
-- bracket, so every loot group fails and the satchel opens empty.
--
-- Each mask mirrors core-class armor progression; custom classes are folded into the mask whose
-- core members share their armor profile, derived from src/server/coa/AscensionCustomClassData.h
-- ClassProficiencies (750 Plate > 8737 Mail > 9077 Leather > 9078 Cloth, highest wins):
--   cloth   16,22,23,24                -> 14712832
--   leather 12,14,20,21,32             -> 2149066752
--   mail    13,15,19,28,29             -> 402935808
--   plate   17,18,25,26,27,30,31       -> 1728249856

SET @SOHG_CLOTH   := 14712832;
SET @SOHG_LEATHER := 2149066752;
SET @SOHG_MAIL    := 402935808;
SET @SOHG_PLATE   := 1728249856;

-- cloth bracket (priest+mage+warlock)
UPDATE `conditions` SET `ConditionValue1` = `ConditionValue1` | @SOHG_CLOTH
WHERE `SourceTypeOrReferenceId` = 10 AND `SourceGroup` BETWEEN 10036 AND 10061
  AND `ConditionTypeOrReference` = 15 AND `ConditionValue1` = 400;

-- low bracket leather (druid+rogue+shaman+hunter): leather users and mail users, who wear leather early
UPDATE `conditions` SET `ConditionValue1` = `ConditionValue1` | (@SOHG_LEATHER | @SOHG_MAIL)
WHERE `SourceTypeOrReferenceId` = 10 AND `SourceGroup` BETWEEN 10036 AND 10061
  AND `ConditionTypeOrReference` = 15 AND `ConditionValue1` = 1100;

-- high bracket leather (druid+rogue)
UPDATE `conditions` SET `ConditionValue1` = `ConditionValue1` | @SOHG_LEATHER
WHERE `SourceTypeOrReferenceId` = 10 AND `SourceGroup` BETWEEN 10036 AND 10061
  AND `ConditionTypeOrReference` = 15 AND `ConditionValue1` = 1032;

-- high bracket mail (shaman+hunter)
UPDATE `conditions` SET `ConditionValue1` = `ConditionValue1` | @SOHG_MAIL
WHERE `SourceTypeOrReferenceId` = 10 AND `SourceGroup` BETWEEN 10036 AND 10061
  AND `ConditionTypeOrReference` = 15 AND `ConditionValue1` = 68;

-- low bracket mail (warrior+paladin): plate users, who wear mail early
UPDATE `conditions` SET `ConditionValue1` = `ConditionValue1` | @SOHG_PLATE
WHERE `SourceTypeOrReferenceId` = 10 AND `SourceGroup` BETWEEN 10036 AND 10061
  AND `ConditionTypeOrReference` = 15 AND `ConditionValue1` = 3;

-- high bracket plate (warrior+paladin+death knight)
UPDATE `conditions` SET `ConditionValue1` = `ConditionValue1` | @SOHG_PLATE
WHERE `SourceTypeOrReferenceId` = 10 AND `SourceGroup` BETWEEN 10036 AND 10061
  AND `ConditionTypeOrReference` = 15 AND `ConditionValue1` = 35;
