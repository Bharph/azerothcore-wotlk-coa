/*
 * Copyright (C) 2016+ AzerothCore <www.azerothcore.org>, released under GNU AGPL v3 license, you may redistribute it
 * and/or modify it under version 3 of the License, or (at your option), any later version.
 */

#ifndef _PLAYERBOT_COABOTNAMES_H
#define _PLAYERBOT_COABOTNAMES_H

#include <string>

// The surname random bots carry when AiPlayerbot.CoaBotSurname is on: "Kegarink Bot".
std::string CoaBotName(std::string const& firstName);

// Gives every random bot the surname, or takes it back when the setting is off. Run at startup,
// once the random bots exist and before any of them logs in.
void ApplyCoaBotSurnames();

#endif
