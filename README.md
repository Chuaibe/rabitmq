GROUPE: TAMIMOUL Chuaibe, BEN EL HADJ Brahim

1 Lancer docker  
2 Lancer le serveur rabbitmq avec la commande ci-dessous:  
- docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management  

3 Créer les utilisateurs sur rabbitmq :  
- http://localhost:15672/ 
- se connecter avec guest guest  
- aller dans admin et add user
- rajouter les permissions et les droits d'admin, car seul les admins peuvent acceder a listes des utilisateur.

4 installer les packages necessaires:
- pip install pika customtkinter requests


5 lancer les scripts log.py et client.py  

python log.py  
python client.py  
