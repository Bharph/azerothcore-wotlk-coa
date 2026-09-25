-- Tracks the welcome warchest mail sent per character (item 2977351)
CREATE TABLE IF NOT EXISTS `coa_character_warchest` (
  `guid` INT UNSIGNED NOT NULL,
  `claimed_at` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`guid`)
);
