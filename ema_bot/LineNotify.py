import requests

class LineNotify:
    def __init__(self, notify_token):
        self.url = 'https://notify-api.line.me/api/notify'
        self.headers = {'Authorization':'Bearer '+notify_token}

    def Send_Text(self, text):
        session_post = requests.post(self.url, headers=self.headers , data = {'message':text})
        # print(session_post.text)

    def Send_Image(self, text, image_path):
        file_img = {'imageFile': open(image_path, 'rb')}
        session = requests.Session()
        session_post = session.post(self.url, headers=self.headers, files=file_img, data= {'message': text})
        # print(session_post.text)

    def Send_Sticker(self, text, stickerPackageId, stickerId):
        session_post = requests.post(self.url, headers=self.headers, data= {'message': text,'stickerPackageId': stickerPackageId, 'stickerId': stickerId})
        # print(session_post.text)

    def Send_Emoji(self, text_emoji):
        session_post = requests.post(self.url, headers=self.headers , data = {'message':text_emoji})
        # print(session_post.text)