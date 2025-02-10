# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Translates stuff into English
"""
import asyncio
import html
import io
import mimetypes

from telethon import helpers, types

from google.oauth2 import service_account
from google.cloud import translate_v3 as translate
from google.cloud import texttospeech

from uniborg import util


PREFERRED_LANGUAGE = "en"


mimetypes.add_type('audio/mpeg', '.borg+tts')


try:
    credentials = service_account.Credentials.from_service_account_file(
        "google_cloud_key.json")
except FileNotFoundError:
    logger.warn(
        "Google Cloud API key not found, this plugin will be unavailable."
    )
    raise util.StopImport

tl_client = translate.TranslationServiceAsyncClient(credentials=credentials)
tl_parent = f"projects/{credentials.project_id}"
tts_client = texttospeech.TextToSpeechAsyncClient(credentials=credentials)


tl_langs = {}
async def fetch_supported_languages():
    langs = (await tl_client.get_supported_languages(
        parent=tl_parent,
        display_language_code=PREFERRED_LANGUAGE
    )).languages
    global tl_langs
    tl_langs = { lang.language_code.lower(): lang for lang in langs }
    if tl_langs.get("zh-cn") is None:
        tl_langs["zh-cn"] = tl_langs["zh"]
asyncio.create_task(fetch_supported_languages())


allowed_groups = set((int(x) for x in storage.allowed_groups or []))


@borg.on(borg.admin_cmd(r"tl_allow_group"))
async def _(event):
    allowed_groups.add(event.chat_id)
    storage.allowed_groups = list(allowed_groups)
    await event.respond(f"Added {event.chat_id} to allowed groups")


@borg.on(borg.admin_cmd(r"tl_allowed_groups"))
async def _(event):
    groups = {}
    for group in allowed_groups:
        entity = await borg.get_entity(group)
        groups[group] = entity.title

    groups = [ f"`{k}`: {v}" for k, v in groups.items() ]
    await event.respond("\n".join(groups))


@borg.on(borg.cmd(r"tl", r"(?:\s+(?P<args>.*))?", "s"))
async def _(event):
    if borg.me.bot and event.chat_id not in allowed_groups:
        return

    source, target = None, None
    text = None
    argtext = False
    if args := event.pattern_match.group("args"):
        has_triple_colon = ":::" in args
        if has_triple_colon:
            langs, text = args.split(":::", 1)
        else:
            langs = args
        has_double_chevron = ">>" in langs
        if has_double_chevron:
            arg_source, arg_target = langs.split(">>", 1)
        else:
            arg_source, arg_target = langs, None

        if has_triple_colon or has_double_chevron:
            # We have an explicit language code for sure, enforce validity
            if arg_source and (source := tl_langs.get(arg_source.lower())) is None:
                await event.respond(f"Invalid language code: {arg_source}")
                return
            if arg_target and (target := tl_langs.get(arg_target.lower())) is None:
                await event.respond(f"Invalid language code: {arg_target}")
                return
        else:
            # No delimiters, must disambiguate
            if arg_source and (source := tl_langs.get(arg_source.lower())) is None:
                if event.is_reply:
                    # Assume argument is a language and enforce validity
                    await event.respond(f"Invalid language code: {arg_source}")
                    return
                else:
                    text = args

        if source:
            source = source.language_code
        if target:
            target = target.language_code

    if target is None:
        target = PREFERRED_LANGUAGE

    if text:
        argtext = True
    elif event.is_reply:
        text = (await event.get_reply_message()).raw_text
    else:
        await event.respond("No text to translate!")
        return

    translation = (await tl_client.translate_text(
        parent=tl_parent,
        contents=[html.escape(text.strip())],
        source_language_code=source,
        target_language_code=target
    )).translations[0]
    translated = translation.translated_text
    langs = (source or translation.detected_language_code, target)

    source, target = (tl_langs[l.lower()].display_name for l in langs)
    result = f"<b>{source} → {target}:</b>\n{translated}"
    await event.respond(result, parse_mode="html")


@borg.on(borg.cmd(r"tts", r"(?:\s+(?P<args>.*))?", "s"))
async def _(event):
    if borg.me.bot and event.chat_id not in allowed_groups:
        return

    lang = None
    text = None
    if args := event.pattern_match.group("args"):
        args = args.split(":::", 1)
        if args[0].lower() in tl_langs:
            lang = args[0]
        if len(args) > 1:
            text = args[1]
        elif lang is None:
            text = args[0]

    if not borg.me.bot and not text:
        await event.delete()

    if not text and event.is_reply:
        text = (await event.get_reply_message()).raw_text

    if not text:
        return

    # Attempt to detect text language
    if lang is None:
        response = await tl_client.detect_language(
            parent=tl_parent,
            content=text.strip()
        )
        lang = response.languages[0].language_code

    voices = (await tts_client.list_voices(language_code=lang)).voices
    if not voices:
        await event.respond(f"No voices for {tl_langs[lang].display_name}")
        return

    response = await tts_client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(
            language_code=lang,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3)
    )

    file = io.BytesIO(response.audio_content)
    file.name = 'a.borg+tts'
    await borg.send_file(
        event.chat_id,
        file,
        reply_to=event.reply_to_msg_id or event.id if not borg.me.bot else None,
        attributes=[types.DocumentAttributeAudio(
            duration=0,
            voice=True
        )]
    )


@borg.on(borg.cmd("langs"))
async def _(event):
    langs = "\n".join([
        "<b>Supported languages:</b>",
        *(f"{l.language_code}: {l.display_name}" for _, l in tl_langs.items())
    ])
    if borg.me.bot:
        action = event.respond
    else:
        action = event.edit
    await action(langs, parse_mode="html")
