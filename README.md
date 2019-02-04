# vktotg
Sends all your vk.com music to telegram channel

# Screenshot
<img src="https://pp.userapi.com/c840120/v840120186/389f0/fzL77Diyu3o.jpg" width="50%" height="50%">

# Requirements

`sudo pip install bs4 vk_api telethon requests`

# Run

`python vktotg.py`

Downloads all your music locally to folder `Music <your_id>`

You can provide specific `user_id` as argument when launching from command line to dowload audio of this user. Just be sure that you have access to them

Examle:
 `python vktotg.py 28452705`
