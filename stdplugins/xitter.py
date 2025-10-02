"""
*Xitter*
Replaces twitter links with fixupx links
"""
import re
from telethon import events

@borg.on(events.NewMessage(outgoing=True,
    pattern=re.compile(r"\b(?:https?://)?(?:www\.)?(?:x|twitter)\.com/(?P<path>[a-zA-Z0-9_]{4,15}/status/\d+)(?:\?\S*)?\b").search))
async def xitter(event):
    m = event.pattern_match.group(0)
    path = event.pattern_match.group(1)
    new_text = (event.raw_text).replace(m, f"https://fxtwitter.com/{path}")
    await event.edit(new_text, link_preview=True)

