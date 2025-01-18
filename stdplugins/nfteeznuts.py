# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Deletes NFT spam
"""
import re

from telethon import events
from telethon.tl.types import MessageMediaWebPage, PeerChannel

generic_filters = [
    re.compile(r"(?i)claim your first \w+ and lets p2e"),
    # https://t.me/c/2236603077/33 `PUCU: Claim your first PUCU and lets P2E`

    re.compile(r"(?i)Ethereum Layer 2 Rollup platform"),
    # https://t.me/c/2236603077/32 `Ethereum Layer 2 Rollup platform - Metis`

    re.compile(r"(?i)Get your free \w+ Cats (?:\w+ Special Edition )?NFT today – a charming collection of unique, cute digital cat art\. Perfect for cat lovers and NFT collectors seeking something special"),
    # https://t.me/c/2236603077/20 `Get your free CATGO Cats NFT today – a charming collection of unique, cute digital cat art. Perfect for cat lovers and NFT collectors seeking something special!`
    # https://t.me/c/2236603077/21 `Get your free VUHUS Cats Christmas Special Edition NFT today – a charming collection of unique, cute digital cat art. Perfect for cat lovers and NFT collectors seeking something special!`

    re.compile(r"(?i)LUNAR NEW YEAR: Claim your Dragons and embarking on an enchanting journey into play-to-earn adventures\."),

    re.compile(r"(?i)Claim your first (?:\w+ )?NFT and Share"),
    #re.compile(r"(?i)Claim your first \w+ NFT and Share \$[\d.]+ Rewards Pool \(\d+ NFT LEFT\)"),
    # https://t.me/c/2236603077/29 `Claim your first Avufi NFT and Share $55.000 Rewards Pool (239 NFT LEFT)`

    re.compile(r"(?i)Rivalz Network"),
    # https://t.me/c/2236603077/30

    re.compile(r"(?i)LayerZero"),
    # https://t.me/c/2236603077/31

    re.compile(r"(?i)➥ CLICK HERE TO MINT! ⮨"),
    # https://t.me/c/2236603077/23 `🚨 ➥ CLICK HERE TO MINT! ⮨ ✅`
    # https://t.me/c/2236603077/24 `➥ CLICK HERE TO MINT! ⮨ ✅`

    re.compile(r"(?i)NFT .* FREE (MINT|CLAIM)"),
    # https://t.me/c/2236603077/41

    # "Trump Game"
    # https://t.me/c/2236603077/25
    # https://t.me/c/2236603077/28
    # https://t.me/c/2236603077/5

    # Bot links
    # https://t.me/c/2236603077/27

    # https://t.me/c/2236603077/90
    re.compile(r"(?i)💎.*\$TGH"),
]

dot_io_filters = [
    re.compile(r"(?i)\bairdrops?\b"),
    re.compile(r"(?i)\b(?:get|claim|free)\b.*\bnfts?\b"),
]

invisible_chars = [
    # U+206x invisible punctuation
    *(chr(c) for c in range(0x2060, 0x2070)),
]

async def is_spam(event):
    for c in invisible_chars:
        if c in event.message.raw_text:
            return True

    for f in generic_filters:
        if f.search(event.message.raw_text):
            return True

    media = event.message.media

    if isinstance(media, MessageMediaWebPage):
        webpage = media.webpage
        domain = webpage.display_url.lower().split("/")[0]

        if webpage.type in ("telegram_bot", "telegram_botapp"):
            return True

        if domain == "opensea.io":
            return True

        dot_io = domain.endswith(".io")
        for _, val in webpage.to_dict().items():
            if not isinstance(val, str):
                continue

            # Spammers are getting cute
            for c in invisible_chars:
                if c in val:
                    return True

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
    if event.message.out and event.message.saved_peer_id is None:
        return

    # Only moderate incoming channel comments
    # Comments are always replies,
    # the top of the thread is a message sent by a PeerChannel
    if not event.message.out:
        message = event.message
        if message.reply_to is None:
            return
        top_id = (
            message.reply_to.reply_to_top_id
            or message.reply_to.reply_to_msg_id
        )
        top = await borg.get_messages(event.input_chat, ids=top_id)
        if top is None:
            return
        if not isinstance(top.from_id, PeerChannel):
            return

    if await is_spam(event):
        await event.delete()
