"""Terminal chat with IVA Language. Run: python iva_chat.py"""
from iva_language import IVaLanguage


def main() -> None:
    iva = IVaLanguage()
    print("IVA: Привет! Я IVA. Напиши /help для команд, /exit для выхода.")
    while True:
        try:
            message = input("Ты: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nIVA: До встречи!")
            break
        if message == "/exit":
            print("IVA: До встречи!")
            break
        if message == "/help":
            print("Команды:")
            print("/teach ТЕКСТ — явно обучить меня примеру")
            print("/generate — собрать новую фразу из выученных связей слов")
            print("/memory — показать объём локальной памяти")
            print("/reset — удалить историю и обучающие примеры")
            print("/exit — выход")
            continue
        if message.startswith("/teach "):
            count = iva.teach(message[len("/teach "):])
            print("IVA: " + (f"Пример добавлен: {count} слов/знаков." if count else "Нужно хотя бы три слова для примера."))
            continue
        if message == "/generate":
            print("IVA:", iva.generate())
            continue
        if message == "/memory":
            print(f"IVA: Диалоговых реплик: {len(iva.memory.get('turns', []))}; обучающих примеров: {len(iva.memory.get('examples', []))}.")
            continue
        if message == "/reset":
            iva.reset_memory()
            print("IVA: История и обучающие примеры удалены.")
            continue
        print("IVA:", iva.reply(message))


if __name__ == "__main__":
    main()
