DEFAULT_HEADER = "Basic default_user:0"

class Token:
    def __init__(self, header=DEFAULT_HEADER):
        parts = header.split(" ")

        if parts[0] != "Basic":
            raise NotImplementedError("Unsupported authentitcation scheme: "+parts[0])
        
        credentials = parts[1].split(":")

        if credentials[0] == '':
            raise KeyError("The name is required to authentify a user")
        
        self.user_id = credentials[0]
        self.label_id = credentials[1]

    def __str__(self) -> str:
        return self.user_id + ":" + self.label_id
    
def check_user(user_id: str):
    raise NotImplementedError()