# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Reuploads story media
Just send a story to saved messages
"""

from telethon import events
from telethon.tl import types, functions
from telethon.tl.functions import stories

async def reupload_media(story, file_name=None):
    f = await borg.download_media(story.media, bytes)
    return await borg.upload_file(f, file_name=file_name)

@borg.on(events.NewMessage())
async def _(event):
    if event.message.saved_peer_id is None:
        return

    media = event.message.media
    if not isinstance(media, types.MessageMediaStory):
        return

    res = await borg(stories.GetStoriesByIDRequest(peer=media.peer, id=[media.id]))
    story = res.stories[0]

    if isinstance(story.media, types.MessageMediaDocument):
        loading = await event.reply(file="loading.jpg")
        uploaded = await reupload_media(story)
        file = types.InputMediaUploadedDocument(
            uploaded,
            mime_type=story.media.document.mime_type,
            attributes=[],
            spoiler=story.media.spoiler,
        )
        await loading.delete()
    elif isinstance(story.media, types.MessageMediaPhoto):
        uploaded = await reupload_media(story, file_name="fuckdurov.jpg")
        file = types.InputMediaUploadedPhoto(
            uploaded,
            spoiler=story.media.spoiler,
        )
    else:
        await event.reply(f"Unsupported media type: {type(story.media)}")
        return

    await event.reply(file=file)
