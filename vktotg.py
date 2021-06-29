#!/usr/bin/python3

import os
import sys
import ssl
import shutil
import requests
import webbrowser
import vk_api
from getpass import getpass
from vk_api.audio import VkAudio
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import CreateChannelRequest, EditPhotoRequest
from telethon.tl.types import (
    DocumentAttributeAudio, DocumentAttributeFilename, Channel, InputChannel, InputChatUploadedPhoto
)

folderName = 'Music '
channelName = 'VKMusic'


def captcha_handler(captcha):
    url = captcha.get_url()
    key = input("Enter captcha code {0}: ".format(url)).strip()
    webbrowser.open(url, new=2, autoraise=True)
    return captcha.try_again(key)


def auth_handler():
    key = input("Enter authentication code: ")
    remember_device = True
    return key, remember_device


def reporthook(sent_bytes, total):
    sys.stdout.write(
        f'\r{round(sent_bytes / total * 100, 1)}% {round(sent_bytes / 1024 / 1024, 1)}/{round(total / 1024 / 1024, 1)} MB'
    )
    sys.stdout.flush()


def save(url, filename):
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response


def send_file(client, entity, file, dur, title, artist, caption):
    attr_dict = {
        DocumentAttributeFilename:
        DocumentAttributeFilename(caption),
        DocumentAttributeAudio:
        DocumentAttributeAudio(int(dur), title=title, performer=artist)
    }
    client.send_file(
        entity, file,
        progress_callback=reporthook,
        attributes=list(attr_dict.values())
    )


def auth_vk():
    print('First, log in to vk.com')

    vk_session = vk_api.VkApi(
        input('Enter login: '),
        getpass('Enter password: '),
        captcha_handler=captcha_handler,
        auth_handler=auth_handler
    )

    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        exit()

    user_id = vk_session.get_api().users.get()[0]['id']
    try:
        user_id = str(sys.argv[1])
        print(f'Downloading audios from {user_id}')
    except:
        pass
    if not os.path.exists(folderName + str(user_id)):
        os.mkdir(folderName + str(user_id))
    return VkAudio(vk_session), user_id


def auth_tg():
    print('\nNow, log in to telegram')
    client = TelegramClient('MusicSaver', 184825, '7fd2ade01360bdd6cbc1de0f0120092c').start()
    client.connect()
    if not client.is_user_authorized():
        try:
            client.sign_in(phone=input('Enter full phone number: '))
            client.sign_in(code=input('Enter code that you received: '))
        except SessionPasswordNeededError:
            client.sign_in(password=input('Two step verification is enabled. Please enter your password: '))
    return client

def get_last_readable_track_in_channel(telegramMessagesList, vkAudioList):
    offset = 0
    local_progress = 0
    iterator = len(telegramMessagesList)
    while iterator > 0:
        last_file = telegramMessagesList[offset].document
        if last_file:
            lastAudioName = last_file.attributes[1].file_name
        else:
            offset = offset + 1
            iterator = iterator - 1
            continue
        try:
            local_progress = vkAudioList.index(lastAudioName)
        except ValueError:
            print("Vk audio list does not contain value: " + lastAudioName)
        if local_progress > 0:
            return local_progress+offset
        else:
            offset = offset + 1
            iterator = iterator - 1
    return 0

def main():
    store_local = input('Do you want to leave the local files? [N/y] ') in ['y', 'yes']

    vkaudio, user_id = auth_vk()
    with auth_tg() as client:

        VKMusicChannel = None
        last_file = None
        progress = 0

        dialogs = client.get_dialogs(limit=None)
        for chat in dialogs:
            if type(chat.entity) == Channel and chat.title == channelName:
                VKMusicChannel = chat

        if VKMusicChannel is None:
            VKMusicChannel = client(CreateChannelRequest(
                title=channelName, about='made with https://github.com/HaCk3Dq/vktotg')).chats[0]
            client(EditPhotoRequest(
                InputChannel(VKMusicChannel.id, VKMusicChannel.access_hash), InputChatUploadedPhoto(
                    client.upload_file('music.jpg'))
            ))
            client.delete_messages(client.get_entity(VKMusicChannel), 2)
        else:
            last_file = client.get_messages(VKMusicChannel, limit=None)[0].document
            if last_file:
                last_file = last_file.attributes[1].file_name

        audios = vkaudio.get(user_id)
        total = len(audios)
        if last_file:
            vkAudioList = [track['artist'] + ' - ' + track['title'] for track in audios[::-1]]
            # try get offset by last saved track
            try:
                progress = vkAudioList.index(last_file)
            except ValueError:
                print("Vk audio list does not contain value: " + last_file)
            if progress:
                progress = progress + 1
            else:
                # try get offset from last readable track
                telegramMessagesList = client.get_messages(VKMusicChannel, limit=None)
                progress = get_last_readable_track_in_channel(telegramMessagesList, vkAudioList)+1
            if progress == total:
                print(f'[Done] Found {progress}/{total} tracks')
                exit()
            else:
                print(f'\nFound {progress}/{total} tracks, continue downloading...')
        print()

        progress += 1
        for i, track in enumerate(audios[::-1]):
            if progress and i < progress - 1:
                continue
            filename = track['artist'] + ' - ' + track['title']
            escaped_filename = filename.replace("/", "_")
            escaped_filename  = ''.join(e for e in escaped_filename if e.isalnum() or e == '_' or e == ' ')
            file_path = folderName + str(user_id) + '/' + escaped_filename + '.mp3'

            print(f'Downloading [{i + 1}/{total}]')
            print(filename)
            try:
                save(track['url'], file_path)
            except ssl.SSLError:
                print(f'SSL ERROR: {escaped_filename}, launching again...')
                try:
                    save(track['url'], escaped_filename + '.mp3')
                except:
                    print(f'Failed to save track after 2 tries [{i + 1}/{total}]')
                    exit()

            print('\nUploading...')
            sys.stdout.flush()
            send_file(
                client, client.get_entity(VKMusicChannel),
                file_path,
                track['duration'], track['title'],
                track['artist'], filename
            )

            if not store_local:
                os.remove(file_path)
            print()
            sys.stdout.flush()


if __name__ == '__main__':
    main()
    print('[Done] Finished uploading all the tracks')
