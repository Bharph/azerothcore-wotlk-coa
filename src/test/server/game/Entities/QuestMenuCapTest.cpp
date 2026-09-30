/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published by the
 * Free Software Foundation; either version 3 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for
 * more details.
 *
 * You should have received a copy of the GNU Affero General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "GossipDef.h"
#include "ObjectMgr.h"
#include "QuestDef.h"
#include "gtest/gtest.h"

// Regression for trikyn-live-ops#58: a questgiver offering more than GOSSIP_MAX_MENU_ITEMS quests
// (Jealous's Hero's Call Board carries 47 dailies) asserted the worldserver in QuestMenu::AddMenuItem.
// The cap must drop the extras instead of aborting.
class QuestMenuCapTest : public ::testing::Test
{
protected:
    static constexpr uint32 SENTINEL_QUEST_ID = 1;

    void SetUp() override
    {
        // AddMenuItem only null-checks the quest template pointer, so a non-null sentinel that is
        // never dereferenced is enough to pass its GetQuestTemplate gate without a database load.
        if (sObjectMgr->_questTemplatesFast.size() <= SENTINEL_QUEST_ID)
            sObjectMgr->_questTemplatesFast.resize(SENTINEL_QUEST_ID + 1, nullptr);

        _saved = sObjectMgr->_questTemplatesFast[SENTINEL_QUEST_ID];
        sObjectMgr->_questTemplatesFast[SENTINEL_QUEST_ID] = reinterpret_cast<Quest*>(_storage);
    }

    void TearDown() override
    {
        sObjectMgr->_questTemplatesFast[SENTINEL_QUEST_ID] = _saved;
    }

    Quest* _saved = nullptr;
    alignas(Quest) unsigned char _storage[sizeof(Quest)] = {};
};

TEST_F(QuestMenuCapTest, AddMenuItemStopsAtGossipMaxInsteadOfAsserting)
{
    QuestMenu menu;

    for (uint32 i = 0; i < uint32(GOSSIP_MAX_MENU_ITEMS); ++i)
        menu.AddMenuItem(SENTINEL_QUEST_ID, 4);

    ASSERT_EQ(uint32(menu.GetMenuItemCount()), uint32(GOSSIP_MAX_MENU_ITEMS));

    // The extra offer past the cap must be dropped, not asserted.
    menu.AddMenuItem(SENTINEL_QUEST_ID, 4);

    EXPECT_EQ(uint32(menu.GetMenuItemCount()), uint32(GOSSIP_MAX_MENU_ITEMS));
}
