/*
 * This file is part of the mod-playerbots module for AzerothCore. See AUTHORS file for Copyright
 * information; released under GNU GPL v2 license, redistribute/modify under version 2 of the License,
 * or (at your option) any later version.
 */

#ifndef _PLAYERBOT_COAQUESTMENU_H
#define _PLAYERBOT_COAQUESTMENU_H

#include "GossipDef.h"
#include "ObjectGuid.h"
#include "ObjectMgr.h"

#include <iterator>

// Whether Player::PrepareQuestMenu can list every quest of that quest giver. The core asserts once a
// quest menu holds more than GOSSIP_MAX_MENU_ITEMS: the Stormwind and Orgrimmar Call Boards of Jealous's
// mod-hero-call-board carry 47 dailies, and a bot looking them over for a quest crashed the server
// (28/09). A player never gets there - the module shows the board by category - so bots leave them be.
inline bool CoaQuestMenuFits(ObjectGuid guid)
{
    std::size_t quests = 0;
    if (guid.IsAnyTypeCreature())
    {
        auto const starts = sObjectMgr->GetCreatureQuestRelationBounds(guid.GetEntry());
        auto const ends = sObjectMgr->GetCreatureQuestInvolvedRelationBounds(guid.GetEntry());
        quests = std::distance(starts.first, starts.second) + std::distance(ends.first, ends.second);
    }
    else if (guid.IsGameObject())
    {
        auto const starts = sObjectMgr->GetGOQuestRelationBounds(guid.GetEntry());
        auto const ends = sObjectMgr->GetGOQuestInvolvedRelationBounds(guid.GetEntry());
        quests = std::distance(starts.first, starts.second) + std::distance(ends.first, ends.second);
    }
    return quests <= GOSSIP_MAX_MENU_ITEMS;
}

#endif
