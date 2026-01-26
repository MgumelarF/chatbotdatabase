from chatbot_engine import get_response

print("Chatbot aktif. Ketik 'exit' untuk keluar.")

while True:
    user = input("Kamu: ")
    if user.lower() == "exit":
        break

    print("Bot:", get_response(user))