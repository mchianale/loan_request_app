# Processus d’Évaluation des Demandes de Prêt

Ce TD a pour objectif d’implémenter un processus métier de gestion des demandes de prêt
immobilier en utilisant des concepts avancés de microservices, de tâches asynchrones, et de
messagerie interservices. Les étudiants devront appliquer des notions de coroutines, files de
messages, tâches en arrière-plan et événements pour assurer une exécution efficace et
distribuée du processus.

## Demo

---

## Architecture 
![global_sch](https://github.com/mchianale/loan_request_app/blob/main/docs/main_archi.png)

**1️⃣ MongoDB (Base de données) :** 
- Base de données `NoSQL` utilisée pour stocker les informations des clients (`users`) et gérer leurs demandes de prêt (`loans`).
- Utilise clients asynchrones et synchrones pour gérer les requêtes efficacement.
- Seulement accessible par l'API [`userBackEnd`](https://github.com/mchianale/loan_request_app/tree/main/userBackEnd).

---

**2️⃣ [User Backend](https://github.com/mchianale/loan_request_app/tree/main/userBackEnd) (FastAPI) :**
- API backend construite avec FastAPI pour gérer **les connexion et inscription, la gestion de compte et la création de demandes de prêt.**
- Produit des logs et des demandes de prêt vers `Kafka`.

---

**3️⃣ Zookeeper & Kafka Brokers :**
- `Zookeeper` : Coordonne les brokers Kafka.
- `Kafka Brokers` :
  1. 📨 Reçoivent des demandes de prêt du backend utilisateur.
  2. 🔄 Distribuent ces demandes aux services de traitement via topics Kafka.
  3. 📤 Produisent des logs vers ELK pour la centralisation des journaux.

---

**4️⃣ [ELK Stack](https://github.com/mchianale/loan_request_app/tree/main/logstash) (Logstash, Elasticsearch, Kibana) :**  
- Centralise et visualise les logs du système.  
- Composants principaux :
  - 📊 **Logstash** : Récupère et traite les logs de Kafka.  
  - 🔍 **Elasticsearch** : Stocke les logs pour une recherche efficace.  
  - 📈 **Kibana** : Fournit une interface de visualisation des logs et des métriques de l'application.  

---

**5️⃣ [Celery App](https://github.com/mchianale/loan_request_app/tree/main/celeryApp) (Traitement Asynchrone) :**  
- Gestion du traitement parallèle via `Celery` et `RabbitMQ`.  
- Exécute les tâches critiques de validation et d’évaluation des prêts :  
  - ✅ Évaluation de l'historique de crédit et du profil ([**creditCheckApp - FastAPI**](https://github.com/mchianale/loan_request_app/tree/main/creditCheckApp)).  
  - ✅ Évaluation du projet immobilier ([**propertyCheckApp - FastAPI**](https://github.com/mchianale/loan_request_app/tree/main/propertyCheckApp)).  
  - ✅ Génération de la décision finale et du calendrier de remboursement ([**decisionApp - FastAPI**](https://github.com/mchianale/loan_request_app/tree/main/decisionApp)).  
- Produit des logs vers `Kafka` pour centralisation et monitoring.  

---

**6️⃣ [Loan Notification App](https://github.com/mchianale/loan_request_app/tree/main/loanNotificationApp) (FastAPI + WebSockets) :**  
- Fournit une API `WebSockets` pour notifier les utilisateurs du statut de leur demande de prêt en **temps réel**.  
- Se connecte au backend Celery et à Kafka pour récupérer les mises à jour et envoyer des notifications.  

---

**7️⃣ [Streamlit Frontend](https://github.com/mchianale/loan_request_app/tree/main/stFrontEnd) :**  
- Interface utilisateur interactive permettant aux utilisateurs de :  
  - 🔑 **Se connecter et gérer leur compte**.  
  - 🏦 **Créer une nouvelle demande de prêt**.  
  - 🔎 **Suivre en temps réel l’évaluation de leur demande de prêt**.  
  - 📊 **Visualiser les décisions de crédit et l'historique des prêts**.  
  - 📡 **Recevoir des mises à jour instantanées via `WebSockets`**.  

---

## Réutilsiation 

---


# a faire 
## Test
## Kubernetes
## dashboard

## README
## rapport
### Intro
### Architecture globale 
### Gestion des uilisateurs (login / singup token de session etc.. )
### Service de demande de pret (chaque service & celeri)
### Notification en tmpes reel (websocket et celeri)
### Interac graphiqye utilisateur
### Centralisation des logs
### Cloud Kubernetes
### Test 


docker-compose up -d
docker-compose down -v
docker-compose up --build

# deleyt index
curl -X DELETE -u elastic:b2ecc628566048608451c61b6b210ee6467edc7aefa911efafe4e4c7673f17a8 "http://localhost:9200/logs"

#  create token
curl -X POST -u elastic:b2ecc628566048608451c61b6b210ee6467edc7aefa911efafe4e4c7673f17a8 "localhost:9200/_security/service/elastic/kibana/credential/token/kibana_token?pretty"

docker-compose --env-file .env up -d
docker exec -it kibana env | Select-String "ELASTICSEARCH_SERVICEACCOUNTTOKEN"

# check kafka produce
docker exec -it kafka-0 bash
cd /opt/bitnami/kafka/bin/
./kafka-console-consumer.sh --bootstrap-server kafka-0:9092 --topic logs --from-beginning

docker exec -it kafka-0 bash
kafka-consumer-groups.sh --bootstrap-server kafka-0:9092 --list
kafka-consumer-groups.sh --bootstrap-server kafka-0:9092 --group logstash --describe

# A faire 
Service des demandes de prêt (création et validation des dossiers)
• Service de vérification du crédit (évaluation des antécédents du client)
• Service d’évaluation du bien (analyse de la valeur du bien)
• Service de décision (approbation ou rejet de la demande)
• Service de notification (envoi des résultats aux clients)

 curl -X DELET-u elastic:b2ecc628566048608451c61b6b210ee6467edc7aefa911efafe4e4c7673f17a8 "http://localhost:9200/logs"

streamlit run stFrontEnd/main.py

docker exec -it krabbitmq bash      
rabbitmqctl change_password rabbitmq b2ecc628566048608451c61b6b210ee6467edc7aefa911efafe4e4c7673f17a8
Shawn901@gmail.com
