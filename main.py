from iva_brain import IVABrain

def main():
    brain = IVABrain()
    print("IVA Brain v0.1 — опыт, не датасеты. Напиши help.")
    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nСохранено.")
            break
        if not line:
            continue
        cmd, _, arg = line.partition(" ")
        cmd = cmd.lower()
        if cmd == "quit":
            break
        elif cmd == "help":
            print("status | event <текст> | feedback <good/bad/neutral> | sleep | wake | quit")
        elif cmd == "status":
            print(brain.status())
        elif cmd == "event":
            print(brain.observe(arg))
        elif cmd == "feedback":
            print(brain.feedback(arg))
        elif cmd == "sleep":
            brain.sleep("manual")
            print("IVA ушла спать.")
        elif cmd == "wake":
            brain.wake("manual")
            print("IVA проснулась.")
        else:
            print(brain.observe(line))
    brain.close()

if __name__ == "__main__":
    main()
