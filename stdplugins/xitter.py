"""
*Xitter*
Replaces twitter links with fixupx links
"""
import re
from telethon import events

@borg.on(events.NewMessage(outgoing=True, pattern=re.compile(r"\b(twitter|x)\.com(?=\/\S+)").search))
async def xitter(event):
    m = event.pattern_match.group(1)
    new_text = (event.raw_text).replace(m, "fixupx")
    await event.edit(new_text, link_preview=True)

