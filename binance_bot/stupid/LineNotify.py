import config
import requests

url = 'https://notify-api.line.me/api/notify'

def Send_Text(text):
    token = config.LINE_NOTIFY_TOKEN
    LINE_HEADERS = {'Authorization':'Bearer '+token}
    session_post = requests.post(url, headers=LINE_HEADERS , data = {'message':text})
    print(session_post.text)

def Send_Image(text, image_path):
    token = config.LINE_NOTIFY_TOKEN
    file_img = {'imageFile': open(image_path, 'rb')}
    LINE_HEADERS = {'Authorization':'Bearer '+token}
    session = requests.Session()
    session_post = session.post(url, headers=LINE_HEADERS, files=file_img, data= {'message': text})
    print(session_post.text)

def Send_Sticker(text, stickerPackageId, stickerId):
    token = config.LINE_NOTIFY_TOKEN
    LINE_HEADERS = {'Authorization':'Bearer '+token}
    session_post = requests.post(url, headers=LINE_HEADERS, data= {'message': text,'stickerPackageId': stickerPackageId, 'stickerId': stickerId})
    print(session_post.text)

def Send_Emoji(text_emoji):
    token = config.LINE_NOTIFY_TOKEN
    LINE_HEADERS = {'Authorization':'Bearer '+token}
    session_post = requests.post(url, headers=LINE_HEADERS , data = {'message':text_emoji})
    print(session_post.text)