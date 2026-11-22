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
            print("/teach ТЕКСТ — научить факту или фразе")
            print("/learn ВОПРОС || ОТВЕТ — сохранить пример диалога")
            print("/generate — собрать фразу из выученных связей слов")
            print("/facts — показать факты")
            print("/memory — показать количество примеров и диалогов")
            print("/reset — очистить локальную память")
            print("/exit — выход")
            continue
        if message.startswith("/learn "):
            payload = message[len("/learn "):]
            if "||" not in payload:
                print("IVA: Формат: /learn вопрос || правильный ответ")
                continue
            user_text, iva_text = payload.split("||", 1)
            ok = iva.learn_dialogue(user_text, iva_text)
            print("IVA: " + ("Запомнила пример диалога." if ok else "Добавь вопрос и ответ."))
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
                print("IVA: Пока нет фактов. Например: /teach робот это машина")
            else:
                for fact in facts:
                    print(f"• {fact['subject']} — {fact['relation']} — {fact['object']}")
            continue
        if message == "/memory":
            print(f"IVA: Реплик: {len(iva.memory.get('turns', []))}; фраз: {len(iva.memory.get('examples', []))}; фактов: {len(iva.memory.get('facts', []))}; диалогов: {len(iva.memory.get('dialogues', []))}.")
            continue
        if message == "/reset":
            iva.reset_memory()
            print("IVA: Локальная память очищена.")
            continue
        print("IVA:", iva.reply(message))


if __name__ == "__main__":
    main()
