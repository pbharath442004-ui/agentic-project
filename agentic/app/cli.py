from .db import init_db
from .agent import chat

def main():
    init_db()
    print("Invoice Agent v3. Type 'exit' to quit.")
    while True:
        msg=input("> ").strip()
        if msg.lower() in {"exit","quit"}: break
        print(chat(msg)["message"])

if __name__=="__main__":
    main()
