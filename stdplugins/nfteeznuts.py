# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Deletes NFT spam
"""
import re

from telethon import events
from telethon.tl.types import MessageMediaWebPage

generic_filters = [
    re.compile(r"(?i)claim your first \w+ and lets p2e"),
    re.compile(r"(?i)Ethereum Layer 2 Rollup platform"),
    re.compile(r"(?i)Get your free \w+ Cats (?:\w+ Special Edition )?NFT today – a charming collection of unique, cute digital cat art\. Perfect for cat lovers and NFT collectors seeking something special"),
    re.compile(r"(?i)LUNAR NEW YEAR: Claim your Dragons and embarking on an enchanting journey into play-to-earn adventures\."),
    re.compile(r"(?i)Claim your first NFT and Share"),
    re.compile(r"(?i)Rivalz Network"),
    re.compile(r"(?i)LayerZero"),
]

dot_io_filters = [
    re.compile(r"(?i)\bairdrops?\b"),
    re.compile(r"(?i)\b(?:get|claim|free)\b.*\bnfts?\b"),
]

async def is_spam(event):
    media = event.message.media

    if isinstance(media, MessageMediaWebPage):
        webpage = media.webpage
        domain = webpage.display_url.lower().split("/")[0]

        if domain == "opensea.io":
            return True

        dot_io = domain.endswith(".io")
        for _, val in webpage.to_dict().items():
            if not isinstance(val, str):
                continue

            for f in generic_filters:
                if f.search(val):
                    return True

            if dot_io:
                for f in dot_io_filters:
                    if f.search(val):
                        return True

    return False

@borg.on(events.NewMessage())
async def _(event):
    if await is_spam(event):
        await event.delete()
