/*
 * Copyright (C) 2016+ AzerothCore <www.azerothcore.org>, released under GNU AGPL v3 license, you may redistribute it
 * and/or modify it under version 3 of the License, or (at your option), any later version.
 */

#include "CoaBotNames.h"

#include "CharacterCache.h"
#include "DatabaseEnv.h"
#include "Log.h"
#include "ObjectGuid.h"
#include "PlayerbotAIConfig.h"

#include <unordered_set>
#include <vector>

namespace
{
// Conquest of Azeroth names take two words, a first name and a surname (client revision 8): the
// surname tells a bot from a player at a glance, on its nameplate, in chat and in /who.
constexpr char const* Surname = " Bot";

bool HasSurname(std::string const& name)
{
    std::string const suffix(Surname);
    return name.size() > suffix.size() && name.compare(name.size() - suffix.size(), suffix.size(), suffix) == 0;
}
}  // namespace

std::string CoaBotName(std::string const& firstName)
{
    if (!sPlayerbotAIConfig.coaBotSurname || firstName.find(' ') != std::string::npos)
        return firstName;
    return firstName + Surname;
}

void ApplyCoaBotSurnames()
{
    // At startup only: a config reload runs this again with the bots online, whose names would
    // then differ from the ones the database and the name cache hold.
    static bool applied = false;
    if (applied)
        return;
    applied = true;

    bool const wanted = sPlayerbotAIConfig.coaBotSurname;

    std::unordered_set<uint32> accounts;
    if (QueryResult result = LoginDatabase.Query("SELECT id FROM account WHERE username LIKE '{}%'",
                                                 sPlayerbotAIConfig.randomBotAccountPrefix))
        do
            accounts.insert(result->Fetch()[0].Get<uint32>());
        while (result->NextRow());
    if (accounts.empty())
        return;

    struct Row { uint32 guid; uint32 account; std::string name; };
    std::vector<Row> rows;
    std::unordered_set<std::string> names;
    if (QueryResult result = CharacterDatabase.Query("SELECT guid, account, name FROM characters"))
        do
        {
            Field* fields = result->Fetch();
            rows.push_back({ fields[0].Get<uint32>(), fields[1].Get<uint32>(), fields[2].Get<std::string>() });
            names.insert(rows.back().name);
        } while (result->NextRow());

    uint32 renamed = 0, skipped = 0;
    CharacterDatabaseTransaction trans = CharacterDatabase.BeginTransaction();
    for (Row const& row : rows)
    {
        if (!accounts.count(row.account))
            continue;

        bool const has = HasSurname(row.name);
        if (has == wanted || (wanted && row.name.find(' ') != std::string::npos))
            continue;

        std::string renamedTo = wanted ? row.name + Surname : row.name.substr(0, row.name.size() - std::string(Surname).size());
        // A player may hold the name already: that bot keeps its own.
        if (names.count(renamedTo))
        {
            ++skipped;
            continue;
        }

        names.erase(row.name);
        names.insert(renamedTo);
        sCharacterCache->UpdateCharacterData(ObjectGuid::Create<HighGuid::Player>(row.guid), renamedTo);
        CharacterDatabase.EscapeString(renamedTo);
        trans->Append("UPDATE characters SET name = '{}' WHERE guid = {}", renamedTo, row.guid);
        ++renamed;
    }
    CharacterDatabase.CommitTransaction(trans);

    if (renamed || skipped)
        LOG_INFO("server.loading", ">> {} the surname \"Bot\" for {} random bots ({} names already taken)",
                 wanted ? "Gave" : "Took back", renamed, skipped);
}
