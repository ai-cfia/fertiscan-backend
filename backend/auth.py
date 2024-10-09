import base64

class BasicAuth:
    def __init__(self, username=None, password=None, auth_string=None):
        if auth_string:
            self.username, self.password = self.parse_auth_string(auth_string)
        else:
            self.username = username
            self.password = password

    @staticmethod
    def parse_auth_string(auth_string):
        decoded_bytes = base64.b64decode(auth_string).decode('utf-8')
        username, password = decoded_bytes.split(':', 1)
        return username, password

    def __repr__(self):
        return f"BasicAuth(username={self.username}, password={'*' * len(self.password)})"