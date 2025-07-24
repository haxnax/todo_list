import json
import uuid

FILNAMN = "todo.json"

def uppdatera_todos_med_id():
    try:
        with open(FILNAMN, "r", encoding="utf-8") as f:
            todos = json.load(f)
    except Exception as e:
        print("Kunde inte läsa filen:", e)
        return

    ändrad = False
    for todo in todos:
        if "id" not in todo:
            todo["id"] = str(uuid.uuid4())
            ändrad = True

    if ändrad:
        with open(FILNAMN, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)
        print("✅ Alla todo-poster har nu unika id:n.")
    else:
        print("✔️ Alla todo-poster hade redan id:n.")

uppdatera_todos_med_id()
