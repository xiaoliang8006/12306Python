import requests
import random
#import config


class TicketRob:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
        })
        self.index_url = 'https://kyfw.12306.cn/otn/login/init'
        self.captcha_url = 'https://kyfw.12306.cn/passport/captcha/captcha-image'
        self.login_url = 'https://kyfw.12306.cn/passport/web/login'
        self.check_captcha_url = 'https://kyfw.12306.cn/passport/captcha/captcha-check'
        self.uamtk_url = 'https://kyfw.12306.cn/passport/web/auth/uamtk'
        self.auth_url = 'https://kyfw.12306.cn/otn/uamauthclient'


        self.point = {
            '1': '35,43',
            '2': '108,43',
            '3': '185,43',
            '4': '254,43',
            '5': '34,117',
            '6': '108,117',
            '7': '180,117',
            '8': '258,117',
        }
        self.dict = {}

    def get_point(self, nums):
        nums = nums.split(',')
        # print(nums)
        temp = []
        for item in nums:  # ['3', '6']
            temp.append(self.point[item])
        return ','.join(temp)

    # 检查用户名密码
    def main(self):
        data = {
            'username': 'xiaoliangfuhuai8006',
            'password': '7655289LFH',
            'appid': 'otn'
        }
        self.session.get(self.index_url)  # 1
        self.get_captcha()  # 2
        check_res = self.check_captcha()  # 3
        if check_res:
            response = self.session.post(self.login_url, data=data)  # 4
            if response.json()['result_code'] == 0:
                tk = self.get_tk()  # 5
                auth_res = self.get_auth(tk)  # 6

        # 获取验证码
    def get_captcha(self):
        data = {
            'login_site': 'E',
            'module': 'login',
            'rand': 'sjrand',
            str(random.random()): ''
        }
        response = self.session.get(self.captcha_url, params=data)
        with open('captcha.jpg', 'wb') as f:
            f.write(response.content)

    # 校验验证码
    def check_captcha(self):
        data = {
            'answer': self.get_point(input('请输入正确的图片序号>>>:')),
            'login_site': 'E',
            'rand': 'sjrand'
        }
        response = self.session.post(self.check_captcha_url, data=data)
        if response.json()['result_code'] == '4':
            return True
        else:
            print('验证码选择错误，请重新选择')
        return False

    # 获取权限token
    def get_tk(self):
        uamtk_data = {
            'appid': 'otn'
        }
        response = self.session.post(self.uamtk_url, data=uamtk_data)
        return response.json()['newapptk']

    # 获取权限
    def get_auth(self, tk):
        auth_data = {
            'tk': tk
        }
        response = self.session.post(self.auth_url, data=auth_data)
        if response.json()['result_code'] == 0:
            print(response.text)
            return True
        return False

if __name__ == '__main__':
    ticket = TicketRob()
    ticket.main()