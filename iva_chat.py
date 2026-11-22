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
            print("/teach ТЕКСТ — обучить меня примеру или простому факту")
            print("/generate — собрать фразу из выученных связей слов")
            print("/facts — показать сохранённые понятия и связи")
            print("/memory — показать объём локальной памяти")
            print("/reset — удалить историю, примеры и факты")
            print("/exit — выход")
            continue
        if message.startswith("/teach "):
            count = iva.teach(message[len("/teach "):])
            print("IVA: " + (f"Пример добавлен: {count} слов/знаков." if count else "Нужно хотя бы три слова для примера."))
            continue
        if message == "/generate":
            print("IVA:", iva.generate())
            continue
        if message == "/facts":
            facts = iva.memory.get("facts", [])
            if not facts:
                print("IVA: Пока нет фактов. Попробуй /teach робот это машина.")
            else:
                for fact in facts:
                    print(f"• {fact['subject']} — {fact['relation']} — {fact['object']}")
            continue
        if message == "/memory":
            print(f"IVA: Реплик: {len(iva.memory.get('turns', []))}; примеров: {len(iva.memory.get('examples', []))}; фактов: {len(iva.memory.get('facts', []))}.")
            continue
        if message == "/reset":
            iva.reset_memory()
            print("IVA: История, примеры и факты удалены.")
            continue
        print("IVA:", iva.reply(message))


if __name__ == "__main__":
    main()
