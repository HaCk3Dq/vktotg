# pip install bs4 vk_api
# if you need auios of specific user, just provide id as argument

import os, sys, time
from urllib.request import urlretrieve
from urllib.error import HTTPError
import webbrowser
import ssl
import vk_api
from vk_api.audio import VkAudio

folderName = "Music"


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
    if duration != 0:
        speed = int(progress_size / (1024 * duration))
    else:
        speed = 1
    percent = min(int(count * block_size * 100 / total_size), 100)
    sys.stdout.write("\r%d%%, %d MB, %d KB/s" % (percent, progress_size / (1024 * 1024), speed))
    sys.stdout.flush()


def save(url, filename, user_id):
    urlretrieve(url, folderName + user_id + '/' + filename, reporthook)


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

    user_id = str(vk_session.get_api().users.get()[0]['id'])
    tmp_id = str(sys.argv[1])
    if not tmp_id == "":
        user_id = tmp_id
    print('Fetching audios for ' + user_id)

    vkaudio = VkAudio(vk_session)

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
    if not os.path.exists(folderName + user_id):
        os.mkdir(folderName + user_id)

    downloaded = 0
    for i, track in enumerate(audios[::-1]):
        filename = track['artist'] + ' - ' + track['title']
        # remove bad characters
        filename = filename.replace('?', '')
        filename = filename.replace('|', '')
        filename = filename.replace('*', '')
        filename = filename.replace('[', '')
        filename = filename.replace(']', '')
        filename = filename.replace('"', '')
        filename = filename.replace('/', '')
        filename = filename.replace('\\', '')
        filename = filename.replace('<', '')
        filename = filename.replace('>', '')
        filename = filename.replace(':', '')

        # quickly jump if error occured
        # if i < 830:
        #    continue
        if os.path.isfile(folderName + user_id + '/' + filename + '.mp3'):
            print('Skipping [' + filename + ' ' + str(i + 1) + '/' + str(total) + ']')
            downloaded += 1
            continue

        print('Downloading [' + filename + ' ' + str(i + 1) + '/' + str(total) + ']')
        try:
            save(track['url'], filename + '.mp3', user_id)
            downloaded += 1
        except HTTPError as err:
            if err.code == 404:
                print('NOT FOUND: ' + filename)
            else:
                print('ERROR: ' + filename)
        except ssl.SSLError:
            print('SSL ERROR: ' + filename + ' try launching again')
        sys.stdout.flush()

        print()
        print('Done! Downloaded ' + str(downloaded) + '/' + str(total))
        if downloaded < total:
            print('Try to launch again to to download missing')
        sys.stdout.flush()


if __name__ == '__main__': main()
