# vktotg
Sends all your music to telegram channel

# Screenshot
![scrot](https://pp.userapi.com/c840120/v840120186/389f0/fzL77Diyu3o.jpg)

# Run

 - Windows:

 open `vktotg.exe`
 
 - Linux: 

 `pip install bs4 vk_api telethon`
 
 `python vktotg.py`


[Download](https://github.com/HaCk3Dq/vktotg/archive/master.zip)

# vktotg_local
Downloads all your music locali to folder `Music<your_id>`
You can provide specific user_id as argument when launching from command line to dowload audio of this user. Just be sure that you have access to them ;)

Examle:
 `python vktotg_local.py 28452705`
 
>**Hint:** If you'll use mobile phone as login when launching for the first time,
       you can just enter mobile phone and leave password empty in your next logins.
       User's info saved to vk_config.v2.json