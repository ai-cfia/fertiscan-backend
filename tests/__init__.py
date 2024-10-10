import requests

def curl_file(url:str, path: str): # pragma: no cover
    """
    Pull a file from an URL and save its content.
    """
    data = requests.get(url).content
    with open(path, 'wb') as handler:
        handler.write(data)
