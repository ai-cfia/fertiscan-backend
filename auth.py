import random

DEFAULT_HEADER = "Basic default_user:0"

class Token:
    def __init__(self, header=DEFAULT_HEADER):
        parts = header.split(" ")

        if parts[0] != "Basic":
            raise NotImplementedError("Unsupported authentitcation scheme: "+parts[0])
                
        credentials = parts[1].split(":")
        # TO-DO authenticate the user
        # check_user(user_id)
        print(credentials)

        if credentials[0] == '':
            raise NameError("The user_id is required to authentify a user")
        
        self.user_id = credentials[0]

        # Create a label_id if there's none given
        if credentials[1] == '':
            raise KeyError("The label_id is missing")
        
        self.label_id = credentials[1]

    def __str__(self) -> str:
        return self.user_id + ":" + self.label_id
    def __eq__(self, other):
        return self.label_id == other.label_id and self.user_id == other.user_id
    def __hash__(self) -> int:
        return hash(self.__str__())

def create_label_id() -> str:
    return hex(random.randint(0, 2**32 - 1))

def check_user(user_id: str):
    raise NotImplementedError()