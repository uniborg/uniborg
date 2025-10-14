# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Retry the slot machine emoji until you win!
"""

from telethon import types

WINNERS = range(1, 65, 0b010101)

@borg.on(borg.cmd("gamblecore"))
async def _(event):
    await event.respond("Let's go gambling!")
    while True:
        res = await event.respond(file=types.InputMediaDice("🎰"))
        if res.dice.value in WINNERS:
            break
        await res.delete()
