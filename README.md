# vktotg
Sends all your vk.com music to telegram channel

# Screenshot
<img src="https://pp.userapi.com/c840120/v840120186/389f0/fzL77Diyu3o.jpg" width="540" height="960">

# Requirements & Run

 ```bash
 pip3 install bs4 vk_api telethon request
 python3 vktotg.py
 ```

>**Hint:** If you'll use mobile phone as login when launching for the first time,
       you can just enter mobile phone and leave password empty in your next logins.
       User's info saved to vk_config.v2.json

Downloads all your music locally to folder `Music <your_id>`
You can provide specific `user_id` as argument when launching from command line to dowload audio of this user. Just be sure that you have access to them

Examle:
 `python3 vktotg.py 28452705`
