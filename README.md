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
### **Le fichier `.env`** 
```
# Mongodb
MONGO_INITDB_ROOT_USERNAME=myuser
MONGO_INITDB_ROOT_PASSWORD=mypassword
DATABASE_NAME=user_db
# token bearer
JWT_SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ACCESS_TOKEN_EXPIRE_MINUTES=30
# ELK
ELASTIC_USERNAME=elastic
ELASTIC_PASSWORD=b2ecc628566048608451c61b6b210ee6467edc7aefa911efafe4e4c7673f17a8
ELASTICSEARCH_SERVICEACCOUNTTOKEN=<generate_after>
# Kafka kafka-0:9092,kafka-1:9092,kafka-2:9092
KAFKA_BROKERS=kafka-0:9092,kafka-1:9092,kafka-2:9092
# Celery
REDIS_HOST=kredis
REDIS_PORT=6379
REDIS_PASSWORD=b2ecc628566048608451c61b6b210ee6467edc7aefa911efafe4e4c7673f17a8
REDIS_CELERY_DB_INDEX=10
RABBITMQ_HOST=krabbitmq
RABBITMQ_USERNAME=rabbitmq
RABBITMQ_PASSWORD=b2ecc628566048608451c61b6b210ee6467edc7aefa911efafe4e4c7673f17a8  
RABBITMQ_PORT=5672
LOAN_TOPIC=loan_topic
CREDIT_CHECK_URL=http://credit-check-app-service:8001/evaluate_credit
PROPERTY_CHECK_URL=http://property-check-app-service:8002/evaluate_property
DECISION_URL=http://decision-app-service:8003/loan_decision
NOTIFICATION_URL=http://loan-notification-service:8004/notify
UPDATE_LOAN_URL=http://user-backend-service:8000/update_loan_request
# ADMIN_PASSWORD to notify using LoanNotifyApp
ADMIN_PASSWORD=admin_password_for_notification_security
```

### Premier lancement
1. Lancer une première fois `docker-compose`:
```bash
docker-compose up -d
```

2. Créer un token `Elastic-search` pour `Kibana`:
```bash
curl -X POST -u elastic:<your_password> "localhost:9200/_security/service/elastic/kibana/credential/token/kibana_token?pretty"
```

3. Modifier ensuite le fichier `.env`:
```
ELASTICSEARCH_SERVICEACCOUNTTOKEN=<le toke retourné>
```

4. Relancer `docker-compose` avec la mise à jour:
```
docker-compose --env-file .env up -d
```
Si tout fonctionne, accédez à [kibana](http://localhost:5601/app/home#/).

### Lancer le front
```bash
streamlit run stFrontEnd/main.py
```

### Réinitialiser les logs
Supprimer l'index `logs` d'`Elastic-search`:
```bash
curl -X DELETE -u elastic:<your_password>  "http://localhost:9200/logs"
```

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
