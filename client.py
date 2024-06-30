import threading
import pika
from tkinter import *
import customtkinter
import json
import datetime
import pika.delivery_mode
import requests

# pip install requests customtkinter pika 

class Messagerie:
    def __init__(self):
        self.connected_user = []
        self.AllUser = []
        self.current_discussion = "all" 
        self.current_user = "all"
        self.discussion_list = {}
        self.users = {}
        self.init_graphique()
        self.root.mainloop()
    
    def init_graphique(self):
        # Interface graphique
        self.root = customtkinter.CTk()
        self.root.title("Projet messagerie")
        self.root.geometry("500x800")

        self.message_bienvenue = customtkinter.CTkLabel(self.root, text="Veuillez vous connecter pour commencer à discuter")
        self.message_bienvenue.pack()

        self.label_utilisateur = customtkinter.CTkLabel(self.root, text="Utilisateur")
        self.label_utilisateur.pack()
        self.input_utilisateur = customtkinter.CTkEntry(self.root)
        self.input_utilisateur.pack()

        self.label_mot_de_passe = customtkinter.CTkLabel(self.root, text="Mot de passe")
        self.label_mot_de_passe.pack()
        self.input_mot_de_passe = customtkinter.CTkEntry(self.root, show="*")
        self.input_mot_de_passe.pack()

        self.btn_connexion = customtkinter.CTkButton(self.root, text="Connexion", command=self.logging,
                                                    width=150, height=40, fg_color="blue")
        self.btn_connexion.pack()

        # Champs d'envoi de message, masqués au début
        self.textbox = customtkinter.CTkTextbox(self.root, width=300, height=400, state="disabled")
        self.entry = customtkinter.CTkEntry(self.root)
        self.button1 = customtkinter.CTkButton(self.root, text="Envoyer", command=self.envoie,
                                            width=100, height=30, fg_color="green")

        # Boutons de monitoring
        self.btn_monitor_queues = customtkinter.CTkButton(self.root, text="Monitor Queues", command=self.monitor_queues,
                                                        width=150, height=40, fg_color="purple")
        self.btn_monitor_exchanges = customtkinter.CTkButton(self.root, text="Monitor Exchanges", command=self.monitor_exchanges,
                                                            width=150, height=40, fg_color="purple")
        self.btn_get_connected_users = customtkinter.CTkButton(self.root, text="Get Connected Users", command=self.get_connected_users,
                                                            width=150, height=40, fg_color="purple")
        self.btn_monitor_queues.pack()
        self.btn_monitor_exchanges.pack()
        self.btn_get_connected_users.pack()


    def afficher_champs_messagerie(self):
        self.message_bienvenue.configure(text="Bienvenue, vous êtes connecté en tant que " + self.input_utilisateur.get())
        self.textbox.pack()
        self.entry.pack()
        self.button1.pack()

        self.users["all"] = customtkinter.CTkButton(self.root, text="General",
                                                    width=100, height=50,
                                                    fg_color="orange",
                                                    command=lambda: self.switch_discussion("all"))
        self.users["all"].pack()

        self.getAllUser()
        threading.Thread(target=self.reception, daemon=True).start()

        for user in self.AllUser:
            self.users[user] = customtkinter.CTkButton(self.root, text=user,
                                                       width=100, height=50,
                                                       fg_color="green",
                                                       command=lambda user=user: self.switch_discussion(user))
            self.users[user].pack()
            discussion = self.getDiscussion(user)
            threading.Thread(target=self.reception, args=(discussion,), daemon=True).start()

    def create_connection(self, utilisateur, mot_de_passe):
        credentials = pika.PlainCredentials(utilisateur, mot_de_passe)
        connection_params = pika.ConnectionParameters("localhost", credentials=credentials)
        try:
            return pika.BlockingConnection(connection_params)
        except pika.exceptions.AMQPConnectionError:
            print("Erreur de connexion à RabbitMQ")
            return None
            
    def envoie(self):
        # Crée une nouvelle connexion pour l'envoi
        connection = self.create_connection(self.input_utilisateur.get(), self.input_mot_de_passe.get())
        if not connection:
            return
        channel = connection.channel()
        channel.exchange_declare(exchange="direct", exchange_type="topic")
        
        message = json.dumps({"utilisateur": self.input_utilisateur.get(), "message": self.entry.get()})
        self.entry.delete(0, "end")  # Efface le message de la zone de texte
        channel.basic_publish(exchange="direct", routing_key=self.current_discussion, body=message,
                              properties=pika.BasicProperties(
                                  delivery_mode=pika.DeliveryMode.Persistent,
                              ))
        connection.close()  # Ferme la connexion après l'envoi

    def reception(self, discussion="all"):
        connection = self.create_connection(self.input_utilisateur.get(), self.input_mot_de_passe.get())
        channel = connection.channel()
        channel.exchange_declare(exchange="direct", exchange_type="topic")
        
        result = channel.queue_declare(queue="")
        queue_name = result.method.queue
        channel.queue_bind(exchange="direct", queue=queue_name, routing_key=discussion)

        def callback(ch, method, properties, body):
            message = json.loads(body.decode())
            utilisateur = message["utilisateur"]
            message_data = message["message"]
            date = datetime.datetime.now().strftime("%H:%M:%S")
            message_display = f"{date} - {utilisateur}: {message_data}"
            self.root.after(0, self.add_message, discussion, message_display) 

        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()

    def add_message(self, discussion, message):
        # Ajoute le message au dictionnaire de la discussion
        if discussion not in self.discussion_list:
            self.discussion_list[discussion] = []
        self.discussion_list[discussion].append(message)

        # Vérifie si la discussion actuelle est celle reçue et met à jour la textbox
        if discussion == self.current_discussion:
            self.print_message(message)
        
    def print_message(self, message):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", f"{message}\n")
        self.textbox.configure(state="disabled")

    def switch_discussion(self, user):
        self.users[self.current_user].configure(fg_color="green")
        self.current_discussion = self.getDiscussion(user)
        self.current_user = user
        self.users[user].configure(fg_color="orange")
        self.refresh_discussion()
    
    def refresh_discussion(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")  # Supprime le contenu actuel
        for message in self.discussion_list.get(self.current_discussion, []):
            self.textbox.insert("end", f"{message}\n")
        self.textbox.configure(state="disabled")

    def getDiscussion(self, user):
        la_users = sorted([user, self.input_utilisateur.get()], key=str.lower)
        new_discussion = f"{la_users[0]}_{la_users[1]}"
        if user == "all":
            new_discussion = "all"
        return new_discussion
        
    def logging(self):
        if self.create_connection(self.input_utilisateur.get(), self.input_mot_de_passe.get()):
            print("Connexion réussie")
            self.label_utilisateur.pack_forget()
            self.input_utilisateur.pack_forget()
            self.label_mot_de_passe.pack_forget()
            self.input_mot_de_passe.pack_forget()
            self.btn_connexion.pack_forget()
            self.afficher_champs_messagerie()
        else:
            print("Connexion échouée")
            self.input_mot_de_passe.delete(0, "end")
            self.input_utilisateur.delete(0, "end")
            self.message_bienvenue.configure(text="Connexion échouée, veuillez réessayer")
    
    def getAllUser(self):
        api_url = "http://localhost:15672/api/users/"
        response = requests.get(api_url, auth=(self.input_utilisateur.get(), self.input_mot_de_passe.get()))
        for user in response.json():
            self.AllUser.append(str(user["name"]))
        self.AllUser.remove(self.input_utilisateur.get())
        return response.json()
    
    def get_connected_users(self):
        api_url = "http://localhost:15672/api/connections/"
        response = requests.get(api_url, auth=(self.input_utilisateur.get(), self.input_mot_de_passe.get()))
        connected_users = []
        for user in response.json():
            connected_users.append(str(user["user"]))
        connected_users = list(set(connected_users))
        print(connected_users)
        return connected_users

    def monitor_queues(self):
        api_url = "http://localhost:15672/api/queues/"
        response = requests.get(api_url, auth=(self.input_utilisateur.get(), self.input_mot_de_passe.get()))
        queues_info = response.json()
        for queue in queues_info:
            print(f"Queue: {queue['name']}, Messages: {queue['messages']}, Consumers: {queue['consumers']}")

    def monitor_exchanges(self):
        api_url = "http://localhost:15672/api/exchanges/"
        response = requests.get(api_url, auth=(self.input_utilisateur.get(), self.input_mot_de_passe.get()))
        exchanges_info = response.json()
        for exchange in exchanges_info:
            print(f"Exchange: {exchange['name']}, Type: {exchange['type']}")

app = Messagerie()
