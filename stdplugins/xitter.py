"""
*Xitter*
Replaces twitter links with fixupx links
"""
import re
from telethon import events

@borg.on(events.NewMessage(outgoing=True,
    pattern=r"^(?:https?://)?(?:www\.)?(?:x|twitter)\.com/(?P<path>[a-zA-Z0-9_]{4,15}/status/\d+)(?:\?\S*)?$"))
async def xitter(event):
    path = event.pattern_match.group(1)
    new_text = f"https://fxtwitter.com/{path}"
    await event.edit(new_text, link_preview=True)

