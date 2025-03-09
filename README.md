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
- **Celery Broker** : `RabbitMQ`
- **Celery Backend** : `Redis`

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

## Cycle de vie d'une demande
![global_sch](https://github.com/mchianale/loan_request_app/blob/main/docs/loan_life.png)

Lorsqu'un utilisateur est connecté, il peut créer une nouvelle demande de prêt. Si la création est réussie, la demande est enregistrée dans la base de données `MongoDB` et est annotée comme `Pending`.

Simultanément, un message `Kafka` est produit vers le topic `loan_topic`. L'application `Celery`, qui fonctionne en continu, consomme ces messages `Kafka`. Lorsqu'une nouvelle demande est détectée, un groupe de tâches est lancé.

**Étapes du traitement :**
- **Évaluation en parallèle :**
  1. L'évaluation du profil et du crédit (via `creditCheckApp - FastAPI`).
  2. 'évaluation du projet immobilier (via `propertyCheckApp - FastAPI`).
  3. Ces évaluations sont effectuées simultanément.
- **Validation des évaluations :**
  1. Si l'une des deux tâches échoue ou si la demande est refusée, le processus est arrêté immédiatement, et la demande de prêt est mise à jour en base de données avec le statut Denied ou Cancelled.
- **Validation finale :**
  1. Si les deux évaluations sont approuvées, une dernière tâche est exécutée pour retourner la décision finale et générer un plan de remboursement (via `decisionApp - FastAPI`).
  2. La demande de prêt est alors mise à jour avec le statut final : `Denied` ou `Approved`.
- **Notification en temps réel :**
  1. Chaque tâche envoie des notifications en temps réel via WebSockets à l'application LoanDecisionApp, permettant aux utilisateurs d'être informés en direct de l'état de l'évaluation de leur demande.

---

## Réutilsiation 
### Le fichier `.env`
Créer un fichier `.env`:
```
# Mongodb
MONGO_INITDB_ROOT_USERNAME=myuser
MONGO_INITDB_ROOT_PASSWORD=<set_a_password>
DATABASE_NAME=user_db
# token bearer
JWT_SECRET_KEY=<secret_key_for_decrypt_session_token>
ACCESS_TOKEN_EXPIRE_MINUTES=30
# ELK
ELASTIC_USERNAME=elastic
ELASTIC_PASSWORD=<set_a_password>
ELASTICSEARCH_SERVICEACCOUNTTOKEN=<token_for_elastic_search>
# Kafka kafka-0:9092,kafka-1:9092,kafka-2:9092
KAFKA_BROKERS=kafka-0:9092,kafka-1:9092,kafka-2:9092
# Celery
REDIS_HOST=kredis
REDIS_PORT=6379
REDIS_PASSWORD=<set_a_password>
REDIS_CELERY_DB_INDEX=10
RABBITMQ_HOST=krabbitmq
RABBITMQ_USERNAME=rabbitmq
RABBITMQ_PASSWORD=<set_a_password>  
RABBITMQ_PORT=5672
LOAN_TOPIC=loan_topic
CREDIT_CHECK_URL=http://credit-check-app-service:8001/evaluate_credit
PROPERTY_CHECK_URL=http://property-check-app-service:8002/evaluate_property
DECISION_URL=http://decision-app-service:8003/loan_decision
NOTIFICATION_URL=http://loan-notification-service:8004/notify
UPDATE_LOAN_URL=http://user-backend-service:8000/update_loan_request
# ADMIN_PASSWORD to notify using LoanNotifyApp
ADMIN_PASSWORD=<admin_password_for_notification_security>
```

### Config de `RabbitMQ`
Créer `rabbitmq.conf`:
```conf
default_user=rabbitmq
default_pass=<set_a_password>  
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
ELASTICSEARCH_SERVICEACCOUNTTOKEN=<le token retourné>
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

## Kibana Dashboard

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



