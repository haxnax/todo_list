# Importera nödvändiga Flask-moduler
from flask import Flask, render_template, request, redirect, url_for, flash
# Flask - huvudramverket
# render_template - för att rendera HTML-mallar
# request - för att hantera HTTP-förfrågningar
# redirect - för att omdirigera användaren
# url_for - för att generera URL:er
# flash - för att visa meddelanden till användaren

# Importera Flask-Login för användarhantering
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# LoginManager - huvudklass för inloggning
# UserMixin - grundläggande användarimplementering
# login_user - funktion för att logga in användare
# login_required - dekorator för skyddade routes
# logout_user - funktion för att logga ut
# current_user - tillgång till inloggad användare

# Importera andra nödvändiga moduler
import json  # För att arbeta med JSON-data
import os    # För filsystemoperationer
import uuid  # För att generera unika ID:n
import datetime  # För datumhantering

# Skapa Flask-applikationen
app = Flask(__name__)
# __name__ talar om för Flask var appen finns

# Konfigurera en hemlig nyckel för sessionshantering
app.secret_key = 'din_hemliga_nyckel'  # Byt ut detta i produktion!

# Skapa och initiera LoginManager
login_manager = LoginManager()  # Skapar en instans av LoginManager
login_manager.init_app(app)     # Kopplar den till vår Flask-app
login_manager.login_view = 'login'  # Anger vilken route som hanterar inloggning

# Skapa en användarklass som ärver från UserMixin
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id           # Unikt användar-ID
        self.username = username  # Användarnamn
        self.password = password  # Lösenord (i verklig app, använd hashat lösenord)

# Simulerad databas med användare (ersätt med riktig databas i produktion)
USERS = {
    'admin': {'id': '1', 'password': 'admin'},      # Admin-användare
    'user1': {'id': '2', 'password': 'password1'},  # Testanvändare 1
    'user2': {'id': '3', 'password': 'password2'}   # Testanvändare 2
}

# Funktion som laddar en användare baserat på ID (krävs av Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    # Loopa genom alla användare
    for username, user_info in USERS.items():
        # Kontrollera om ID matchar
        if user_info['id'] == user_id:
            # Returnera användarobjekt om matchning hittades
            return User(id=user_info['id'], username=username, password=user_info['password'])
    # Returnera None om ingen användare hittades
    return None

# Hjälpfunktion för att få filnamn baserat på användar-ID
def get_user_todo_filename(user_id):
    return f"todo_{user_id}.json"  # Skapar filnamn som todo_1.json etc.

# Funktion för att läsa todos för en specifik användare
def läs_todo(user_id):
    # Skapa filnamn baserat på användar-ID
    filnamn = get_user_todo_filename(user_id)
    try:
        # Kontrollera om filen finns
        if os.path.exists(filnamn):
            # Öppna filen för läsning
            with open(filnamn, "r", encoding="utf-8") as f:
                # Ladda och returnera JSON-data
                return json.load(f)
        # Returnera tom lista om filen inte finns
        return []
    except Exception as e:
        # Skriv ut felmeddelande om något går fel
        print(f"Fel vid läsning: {e}")
        # Returnera tom lista vid fel
        return []

# Funktion för att spara todos för en specifik användare
def spara_todo(todo_list, user_id):
    # Skapa filnamn baserat på användar-ID
    filnamn = get_user_todo_filename(user_id)
    # Öppna filen för skrivning
    with open(filnamn, "w", encoding="utf-8") as f:
        # Spara todo-listan som JSON
        json.dump(todo_list, f, ensure_ascii=False, indent=2)

# Route för inloggning (både GET och POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Hantera POST-förfrågan (när formulär skickas)
    if request.method == 'POST':
        # Hämta användarnamn från formuläret
        username = request.form.get('username')
        # Hämta lösenord från formuläret
        password = request.form.get('password')
        
        # Kontrollera om användarnamn finns och lösenord stämmer
        if username in USERS and USERS[username]['password'] == password:
            # Skapa användarobjekt
            user = User(id=USERS[username]['id'], username=username, password=password)
            # Logga in användaren
            login_user(user)
            # Omdirigera till startsidan
            return redirect(url_for('index'))
        else:
            # Visa felmeddelande om inloggning misslyckades
            flash('Fel användarnamn eller lösenord')
    # Rendera inloggningssidan för GET-förfrågan
    return render_template('login.html')

# Route för utloggning
@app.route('/logout')
@login_required  # Endast inloggade användare kan logga ut
def logout():
    # Logga ut användaren
    logout_user()
    # Omdirigera till inloggningssidan
    return redirect(url_for('login'))

# Route för registrering av ny användare
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Hantera POST-förfrågan (när formulär skickas)
    if request.method == 'POST':
        # Hämta användarnamn från formuläret
        username = request.form.get('username')
        # Hämta lösenord från formuläret
        password = request.form.get('password')
        
        # Kontrollera om användarnamn redan finns
        if username in USERS:
            # Visa felmeddelande
            flash('Användarnamnet finns redan')
        else:
            # Skapa nytt användar-ID
            new_id = str(len(USERS) + 1)
            # Lägg till ny användare
            USERS[username] = {'id': new_id, 'password': password}
            # Visa bekräftelsemeddelande
            flash('Konto skapat! Vänligen logga in.')
            # Omdirigera till inloggningssidan
            return redirect(url_for('login'))
    # Rendera registreringssidan för GET-förfrågan
    return render_template('register.html')

# Route för startsidan (kräver inloggning)
@app.route("/")
@login_required  # Skyddad route - endast inloggade användare
def index():
    # Hämta sorteringsparameter från URL, standard är "nyast"
    sortering = request.args.get("sortering", "nyast")
    # Läs aktuell användares todos
    todo_list = läs_todo(current_user.id)

    # Hjälpfunktion för sortering
    def få_tid(todo):
        return todo.get("skapad", "")

    # Sortera baserat på val
    if sortering == "nyast":
        todo_list.sort(key=få_tid, reverse=True)  # Nyast först
    elif sortering == "äldst":
        todo_list.sort(key=få_tid)  # Äldst först
    elif sortering == "prioritet":
        # Sortera efter prioritet (hög, medel, låg)
        def prioritet_key(todo):
            prioriteter = {"hög": 1, "medel": 2, "låg": 3}
            return prioriteter.get(todo.get("prioritet", "medel"), 2)
        todo_list.sort(key=prioritet_key)

    # Rendera mallen med todos och sorteringsinfo
    return render_template("index.html", todos=todo_list, sortering=sortering)

# Route för att lägga till ny todo (kräver inloggning)
@app.route("/lägg_till", methods=["POST"])
@login_required
def lägg_till():
    # Läs aktuell användares todos
    todo_list = läs_todo(current_user.id)
    # Hämta text från formuläret
    text = request.form.get("text")
    # Hämta prioritet från formuläret, standard är "medel"
    prioritet = request.form.get("prioritet", "medel")

    # Kontrollera att text inte är tom
    if text:
        # Skapa ny todo
        ny_uppgift = {
            "id": str(uuid.uuid4()),  # Generera unikt ID
            "text": text,             # Uppgiftstext
            "klar": False,            # Ej klar från början
            "skapad": datetime.datetime.now().isoformat(),  # Nuvarande tid
            "prioritet": prioritet    # Prioritet
        }
        # Lägg till i listan
        todo_list.append(ny_uppgift)
        # Spara listan
        spara_todo(todo_list, current_user.id)
    # Omdirigera till startsidan
    return redirect("/")
 
# Route för att markera todo som klar (kräver inloggning)
@app.route("/klar/<id>")
@login_required
def markera_klar(id):
    # Läs aktuell användares todos
    todo_list = läs_todo(current_user.id)
    # Loopa genom todos
    for todo in todo_list:
        # Hitta todo med matchande ID
        if todo.get("id") == id:
            # Markera som klar
            todo["klar"] = True
            break
    # Spara ändringar
    spara_todo(todo_list, current_user.id)
    # Omdirigera till startsidan
    return redirect("/")

# Route för att ta bort todo (kräver inloggning)
@app.route("/ta_bort/<id>")
@login_required
def ta_bort(id):
    # Läs aktuell användares todos
    todo_list = läs_todo(current_user.id)
    # Skapa ny lista utan todo med matchande ID
    todo_list = [todo for todo in todo_list if todo.get("id") != id]
    # Spara ändringar
    spara_todo(todo_list, current_user.id)
    # Omdirigera till startsidan
    return redirect("/")

# Route för att redigera todo (kräver inloggning)
@app.route("/redigera/<id>")
@login_required
def redigera_sida(id):
    # Läs aktuell användares todos
    todo_list = läs_todo(current_user.id)
    # Hitta todo med matchande ID
    todo = next((t for t in todo_list if t["id"] == id), None)
    # Om inte hittad, omdirigera till startsidan
    if not todo:
        return redirect("/")
    # Rendera redigeringssidan
    return render_template("redigera.html", todo=todo)

# Route för att uppdatera todo (kräver inloggning)
@app.route("/uppdatera/<id>", methods=["POST"])
@login_required
def uppdatera_todo(id):
    # Läs aktuell användares todos
    todo_list = läs_todo(current_user.id)
    # Loopa genom todos
    for todo in todo_list:
        # Hitta todo med matchande ID
        if todo["id"] == id:
            # Hämta ny text från formuläret
            ny_text = request.form.get("text")
            # Uppdatera om text finns
            if ny_text:
                todo["text"] = ny_text
            break
    # Spara ändringar
    spara_todo(todo_list, current_user.id)
    # Omdirigera till startsidan
    return redirect("/")

# Starta applikationen om filen körs direkt
if __name__ == "__main__":
    app.run(debug=True)  # Debug-läge för utveckling
# alhamdulillah
