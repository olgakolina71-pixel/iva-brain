"""Terminal chat with IVA's starter text module. Run: python iva_chat.py"""
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
            print("Команды: /help — помощь, /memory — показать число сохранённых реплик, /reset — очистить память, /exit — выход.")
            continue
        if message == "/memory":
            print(f"IVA: Сохранено реплик: {len(iva.memory.get('turns', []))}.")
            continue
        if message == "/reset":
            iva.reset_memory()
            print("IVA: Локальная память очищена.")
            continue
        print("IVA:", iva.reply(message))

if __name__ == "__main__":
    main()
