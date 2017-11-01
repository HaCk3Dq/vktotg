# pip install bs4 vk_api telethon

import collections, os, sys, time
from urllib.request import urlretrieve
import webbrowser
import vk_api
from vk_api.audio import VkAudio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import CreateChannelRequest, EditPhotoRequest
from telethon.tl.functions.messages import SendMediaRequest, DeleteMessagesRequest
from telethon.tl.types import (
  DocumentAttributeAudio, DocumentAttributeFilename, 
  Channel, InputMediaUploadedDocument, InputChannel,
  InputChatUploadedPhoto
)

def captcha_handler(captcha):
  url = captcha.get_url()
  key = input("Enter captcha code {0}: ".format(url)).strip()
  webbrowser.open(url, new=2, autoraise=True)
  return captcha.try_again(key)

def auth_handler():
  key = input("Enter authentication code: ")
  remember_device = True
  return key, remember_device

def get(self, owner_id, offset=0):
  response = self._vk.http.get(
    'https://m.vk.com/audios{}'.format(owner_id),
    params={'offset': offset},
    allow_redirects=False
  )
  if not response.text:
    raise AccessDenied('You don\'t have permissions to browse {}\'s audio'.format(owner_id))
  return scrap_data(response.text)

def scrap_data(html):
  soup = BeautifulSoup(html, 'html.parser')
  tracks = []
  for audio in soup.find_all('div', {'class': 'audio_item ai_has_btn'}):
    ai_artist = audio.select('.ai_artist')
    artist = ai_artist[0].text
    link = audio.select('.ai_body')[0].input['value']
    if 'audio_api_unavailable' in link: link = decode_audio_url(link)
    tracks.append({
      'artist': artist,
      'title': audio.select('.ai_title')[0].text,
      'dur': audio.select('.ai_dur')[0]['data-dur'],
      'url': link
    })
  return tracks

def reporthook(count, block_size, total_size):
  global start_time
  if count == 0:
    start_time = time.time()
    return
  duration = time.time() - start_time
  progress_size = int(count * block_size)
  if duration != 0: speed = int(progress_size / (1024 * duration))
  else: speed = 1
  percent = min(int(count * block_size * 100 / total_size), 100)
  sys.stdout.write("\r%d%%, %d MB, %d KB/s" % (percent, progress_size / (1024 * 1024), speed))
  sys.stdout.flush()

def save(url, filename):
  urlretrieve(url, filename, reporthook)

def send_file(client, entity, file, dur, title, artist, caption):
  file_hash = hash(file)
  if file_hash in client._upload_cache: file_handle = client._upload_cache[file_hash]
  else: client._upload_cache[file_hash] = file_handle = client.upload_file(file)

  attr_dict = {
    DocumentAttributeFilename:
    DocumentAttributeFilename(caption),
    DocumentAttributeAudio:
    DocumentAttributeAudio(int(dur), title=title, performer=artist)
  }

  media = InputMediaUploadedDocument(
    file=file_handle,
    mime_type='audio/mpeg',
    attributes=list(attr_dict.values()),
    caption=''
  )

  client(SendMediaRequest(
    peer=client.get_input_entity(entity),
    media=media,
    reply_to_msg_id=None
  ))

def main():
  print('First, log in to vk.com')
  login = input('Enter login: ')
  password = input('Enter password: ')

  vk_session = vk_api.VkApi(
    login, password,
    captcha_handler=captcha_handler,
    auth_handler=auth_handler
  )

  try:
    vk_session.auth()
  except vk_api.AuthError as error_msg:
    print(error_msg)
    return

  user_id = vk_session.get_api().users.get()[0]['id']
  vkaudio = VkAudio(vk_session)

  api_id = 184825
  api_hash = '7fd2ade01360bdd6cbc1de0f0120092c'

  client = TelegramClient('MusicSaver', api_id, api_hash)
  client.connect()
  print('\nNow, log in to telegram')
  if not client.is_user_authorized():
    try:
      client.sign_in(phone=input('Enter full phone number: '))
      client.sign_in(code=input('Enter code that you received: '))
    except SessionPasswordNeededError:
      client.sign_in(password=input('Two step verification is enabled. Please enter your password: '))
    

  VKMusicChannel = client(CreateChannelRequest(title='VKMusic', about='made with https://github.com/HaCk3Dq/vktotg')).chats[0]
  client(EditPhotoRequest(
    InputChannel(VKMusicChannel.id, VKMusicChannel.access_hash), InputChatUploadedPhoto(client.upload_file('music.jpg'))
  ))
  client.delete_messages(client.get_entity(VKMusicChannel), 2)

  offset = 0
  audios = []
  last_chunk = []
  chunk = None
  while chunk != last_chunk:
    last_chunk = chunk
    chunk = vkaudio.get(user_id, offset)
    audios.extend(chunk)
    offset += 50
  total = len(audios)

  print()
  for i, track in enumerate(audios[::-1]):
    filename = track['artist'] + ' - ' + track['title']
    print('Downloading [' + str(i+1) + '/' + str(total) + ']')
    save(track['url'], str(i)+'.mp3')
    print('\nUploading...')
    sys.stdout.flush()
    send_file(
      client, client.get_entity(VKMusicChannel), 
      str(i)+'.mp3', track['dur'], track['title'],
      track['artist'], filename
    )
    os.remove(str(i)+'.mp3')
    print()
    sys.stdout.flush()

  client.disconnect()

if __name__ == '__main__': main()
