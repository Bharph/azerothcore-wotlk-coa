-- The realm's LFGDungeons.dbc numbers its randoms 258 (Classic), 417 (Burning Crusade) and
-- 465 (Wrath), but lfg_dungeon_rewards still carries only the stock ids, so completing the
-- BC or Wrath random pays nothing: GetRandomDungeonReward finds no row and FinishDungeon
-- skips the reward (observed by the owner finishing Sethekk Halls from the 417 queue at 61).
-- Mirror the stock Burning Crusade (259) and Wrath (261) reward bands onto the realm's ids.
DELETE FROM `lfg_dungeon_rewards` WHERE `dungeonId` IN (417,465);
INSERT INTO `lfg_dungeon_rewards` (`dungeonId`, `maxLevel`, `firstQuestId`, `otherQuestId`) VALUES
(417,64,24887,24895),
(417,70,24888,24896),
(465,80,24790,24791);
