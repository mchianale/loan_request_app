
from celery.signals import worker_ready
from celery import group, chain
import requests
import json
from confluent_kafka import Consumer, KafkaException
from datetime import datetime, timedelta, timezone
import uuid
import asyncio

from celery_app import app, LOAN_TOPIC, CREDIT_CHECK_URL, PROPERTY_CHECK_URL, DECISION_URL, NOTIFICATION_URL, UPDATE_LOAN_URL, ADMIN_PASSWORD
from kafkaClient import LogEntry, KAFKA_BROKERS, send_log_sync
from notifier import notify
from updater import update_loan_request


# constants
GROUP_ID = "celery-group"
CONSUMER_CONFIG = {
    "bootstrap.servers": KAFKA_BROKERS,
    "group.id": GROUP_ID,
    "auto.offset.reset": "earliest",
}
SUBSCRIBED_TOPICS = [LOAN_TOPIC]
# countdown for eahc task
CREDIT_CHECK_COUNTDOWN = 10
PROPERTY_CHECK_COUNTDOWN = 10
DECISION_COUNTDOWN = 10
# utils
def get_current_date()->datetime:
    return datetime.now(timezone(timedelta(hours=1))) 

@app.task
def kafka_consumer_process():
    """Runs Kafka consumer as a separate process."""
    # init consumer
    consumer = Consumer(CONSUMER_CONFIG)
    consumer.subscribe(SUBSCRIBED_TOPICS)
    print(f"🚀 Kafka Consumer Subscribed to topics: {SUBSCRIBED_TOPICS}")
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Kafka error: {msg.error()}")
                continue
            
            topic_name = msg.topic()
            topic_data = json.loads(msg.value().decode("utf-8"))
            print(f"✅ Received message from topic '{topic_name}': {topic_data}")

            # create id for all tasks
            evaluate_credit_id = str(uuid.uuid4())
            evaluate_property_id = str(uuid.uuid4())
            # evaluate credit and property parallele way
            evaluate_credit_params = topic_data['credit_check_entry'] | {
                'loan_id' : topic_data['loan']['loan_id'],
                'user_id' : topic_data['loan']['user_id'],
                'countdown' : CREDIT_CHECK_COUNTDOWN, 
                'url' : CREDIT_CHECK_URL,
                'other_task_ids' : [evaluate_property_id]
            }
            evaluate_property_params = topic_data['property_check_entry'] | {
                'loan_id' : topic_data['loan']['loan_id'],
                'user_id' : topic_data['loan']['user_id'],
                'countdown' : PROPERTY_CHECK_COUNTDOWN, 
                'url' : PROPERTY_CHECK_URL,
                'other_task_ids' : [evaluate_credit_id]
            }   
            save_id_params = {
                'loan_id' : topic_data['loan']['loan_id'],
                'user_id' : topic_data['loan']['user_id']
            }
            # task b (for test)
            parallel_tasks = group([
                evaluate_credit.s(
                    **evaluate_credit_params
                ).set(task_id=evaluate_credit_id),
                evaluate_property.s(
                    **evaluate_property_params
                ).set(task_id=evaluate_property_id),
                save_id.s(**save_id_params)
            ])
            # 🔥 Execute the workflow (this starts execution!)
            workflow = chain(parallel_tasks | loan_decision.s()).apply_async()
            print(f"🆔 Chord Execution ID: {workflow.id}")            

    except KafkaException as e:
        print(f"Kafka Consumer Error: {e}")
    finally:
        print("Closing Kafka consumer")
        consumer.close()


@worker_ready.connect
def at_startup(sender, **kwargs):
    """Run this when the worker starts"""
    print("🚀 Celery Worker Ready: Running startup task...")
    kafka_consumer_process.delay()
    print("🚀 Kafka Consumer Process Started!")


"""
for task_id in other_task_ids:
    try:
        app.control.revoke(task_id, terminate=True, signal="SIGKILL")
    except:
        continue
"""

@app.task(bind=True, rate_limit="100/m")
def save_id(
    self,
    loan_id : str,
    user_id : str
):
    return {
        'loan_id': loan_id,
        'user_id': user_id
    }
    
@app.task(bind=True, max_retries=3, rate_limit="100/m")
def evaluate_credit(
    self,
    loan_amount: float,
    duration_months: float,
    gross_monthly_income: float,
    user_credits: list,
    date_of_birth: str,
    number_of_dependents: int,
    work_status: str,
    loan_id: str,
    user_id: str,
    url: str,
    countdown: int,
    other_task_ids : list
):
    """
    Celery Task: Evaluates creditworthiness based on user financial history.
    """
    payload = {
        "loan_amount": loan_amount,
        "duration_months": duration_months,
        "gross_monthly_income": gross_monthly_income,
        "user_credits": user_credits,
        "date_of_birth": date_of_birth,
        "number_of_dependents": number_of_dependents,
        "work_status": work_status
    }

    headers = {
        "Content-Type": "application/json"
    }
    
    start_time = get_current_date()
    try:
        response = requests.post(url, json=payload, headers=headers)   
    except Exception as e:
        raise self.retry(exc=e, countdown=countdown)
    # logs
    end_time = get_current_date()
    status_code = response.status_code
    response = response.json()
    if status_code == 201:
        # send notification
        print('📢 send notification')
        kill = "Denied" == response.get("status")
        notify_response = asyncio.run(
            notify(
                user_id=user_id,
                loan_id=loan_id,
                password=ADMIN_PASSWORD,
                loan_status=response.get("status"),
                finish=kill,
                message=response.get("message"),
                url=NOTIFICATION_URL
            )
        )
       
        if notify_response.status_code != 201:
            error_msg = notify_response.json().get('detail')
            error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
            print(f'❌ notification error: {error_msg}')
            kill = True
        else:
            print("✅ Notification successfully sent !")  

        # if denied kill other evalueation task (property)
        if kill:
            for task_id in other_task_ids:
                try:
                    app.control.revoke(task_id, terminate=True, signal="SIGKILL")
                except:
                    continue

            # update loan 
            print(f"❌ update loan before")
            update_response = asyncio.run(
                update_loan_request(
                    user_id=user_id,
                    loan_id=loan_id,
                    password=ADMIN_PASSWORD,
                    loan_status=response.get("status"),
                    loan_message=response.get("message"),
                    credit_check_response=response,
                    url=UPDATE_LOAN_URL,

                )
            )
            if update_response.status_code != 201:
                error_msg = update_response.json().get('detail')
                error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
                print(f'❌ update error: {error_msg}')
            else:
                print("✅ loan was successfully updated !")  


        # send log
        logEntry = LogEntry(
            service='credit-check-app',
            endpoint='evaluate_credit',
            method='POST', 
            status=status_code,
            log_message=response.get("message"),
            start_time=start_time,
            end_time=end_time,
            metadata={
                'loan_id': loan_id,
                'user_id': user_id,
                'status': response.get("status"),
            }
        )
        try:
            print(f"📢 Sending message to Kafka: {logEntry}")
            send_log_sync(logEntry=logEntry)
            print("✅ Message successfully sent to Kafka!")  
        except Exception as e:
            print(f"❌ Kafka Error: {e}")
            pass # log will not be see but don't need to impact user loan request

        return response
    
    error_msg = response.get('detail')
    error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
    # notify error
    notify_response = asyncio.run(
            notify(
                user_id=user_id,
                loan_id=loan_id,
                password=ADMIN_PASSWORD,
                loan_status="Cancelled",
                finish=True,
                message=error_msg,
                url=NOTIFICATION_URL
            )
        )
    if notify_response.status_code != 201:
            error_msg = notify_response.json().get('detail')
            error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
            print(f'❌ notification error: {error_msg}')
    else:
        print("✅ Notification successfully sent !")  
    #kill other evaluation task (property)
    for task_id in other_task_ids:
        try:
            app.control.revoke(task_id, terminate=True, signal="SIGKILL")
        except:
            continue

    # update loan 
    print(f"❌ update loan before")
    update_response = asyncio.run(
        update_loan_request(
            user_id=user_id,
            loan_id=loan_id,
            password=ADMIN_PASSWORD,
            loan_status="Cancelled",
            loan_message=error_msg,
            url=UPDATE_LOAN_URL,

        )
    )
    if update_response.status_code != 201:
        error_msg = update_response.json().get('detail')
        error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
        print(f'❌ update error: {error_msg}')
    else:
        print("✅ loan was successfully updated !")  

    # send log
    logEntry: LogEntry = LogEntry(
        service='credit-check-app',
        endpoint='evaluate_credit',
        method='POST', 
        status=status_code, 
        message=error_msg,
        start_time=start_time,
        end_time=end_time,
        metadata={
            'loan_id': loan_id,
            'user_id': user_id,
            'status' : "Cancelled"
        }
    )
    try:
        print(f"📢 Sending message to Kafka: {logEntry}")
        send_log_sync(logEntry=logEntry)
        print("✅ Message successfully sent to Kafka!")
    except Exception as e:
        print(f"❌ Kafka Error: {e}")
        pass
    raise Exception(f"Failed to evaluate credit: {error_msg}")


@app.task(bind=True, max_retries=3, rate_limit="100/m")
def evaluate_property(
    self,
    loan_amount: float,
    property_value: float,
    loan_id: str,
    user_id: str,
    url: str,
    countdown: int,
    other_task_ids : list
):
    """
    Celery Task: Evaluates property project based on loan amount.
    """
    payload = {
        "loan_amount": loan_amount,
        "property_value": property_value
    }

    headers = {
        "Content-Type": "application/json"
    }
    
    start_time = get_current_date()
    try:
        response = requests.post(url, json=payload, headers=headers)   
    except Exception as e:
        raise self.retry(exc=e, countdown=countdown)
    # logs
    end_time = get_current_date()
    status_code = response.status_code
    response = response.json()
    if status_code == 201:
        # send notification
        print('📢 send notification')
        kill = "Denied" == response.get("status")
        notify_response = asyncio.run(
            notify(
                user_id=user_id,
                loan_id=loan_id,
                password=ADMIN_PASSWORD,
                loan_status=response.get("status"),
                finish=kill,
                message=response.get("message"),
                url=NOTIFICATION_URL
            )
        )
       
        if notify_response.status_code != 201:
            error_msg = notify_response.json().get('detail')
            error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
            print(f'❌ notification error: {error_msg}')
            kill = True
        else:
            print("✅ Notification successfully sent !") 

        # if denied kill other evalueation task (property)
        if kill:
            for task_id in other_task_ids:
                try:
                    app.control.revoke(task_id, terminate=True, signal="SIGKILL")
                except:
                    continue

            # update loan 
            print(f"❌ update loan before")
            update_response = asyncio.run(
                update_loan_request(
                    user_id=user_id,
                    loan_id=loan_id,
                    password=ADMIN_PASSWORD,
                    loan_status=response.get("status"),
                    loan_message=response.get("message"),
                    property_check_response=response,
                    url=UPDATE_LOAN_URL,

                )
            )
            if update_response.status_code != 201:
                error_msg = update_response.json().get('detail')
                error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
                print(f'❌ update error: {error_msg}')
            else:
                print("✅ loan was successfully updated !")  

        # send log
        logEntry = LogEntry(
            service='property-check-app',
            endpoint='evaluate_property',
            method='POST', 
            status=status_code,
            log_message=response.get("message"),
            start_time=start_time,
            end_time=end_time,
            metadata={
                'loan_id': loan_id,
                'user_id': user_id,
                'status': response.get("status"),
            }
        )
        try:
            print(f"📢 Sending message to Kafka: {logEntry}")
            send_log_sync(logEntry=logEntry)
            print("✅ Message successfully sent to Kafka!")  
        except Exception as e:
            print(f"❌ Kafka Error: {e}")
            pass
        return response
    error_msg = response.get('detail')
    error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
    # notify error
    notify_response = asyncio.run(
            notify(
                user_id=user_id,
                loan_id=loan_id,
                password=ADMIN_PASSWORD,
                loan_status="Cancelled",
                finish=True,
                message=error_msg,
                url=NOTIFICATION_URL
            )
        )
    if notify_response.status_code != 201:
            error_msg = notify_response.json().get('detail')
            error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
            print(f'❌ notification error: {error_msg}')
    else:
        print("✅ Notification successfully sent !")  
    #kill other evalueation task (property)
    for task_id in other_task_ids:
        try:
            app.control.revoke(task_id, terminate=True, signal="SIGKILL")
        except:
            continue

    # update loan 
    print(f"❌ update loan before")
    update_response = asyncio.run(
        update_loan_request(
            user_id=user_id,
            loan_id=loan_id,
            password=ADMIN_PASSWORD,
            loan_status="Cancelled",
            loan_message=error_msg,
            url=UPDATE_LOAN_URL,

        )
    )
    if update_response.status_code != 201:
        error_msg = update_response.json().get('detail')
        error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
        print(f'❌ update error: {error_msg}')
    else:
        print("✅ loan was successfully updated !")  

    # send log
    logEntry: LogEntry = LogEntry(
        service='property-check-app',
        endpoint='evaluate_property',
        method='POST', 
        status=status_code, 
        message=error_msg,
        start_time=start_time,
        end_time=end_time,
        metadata={
            'loan_id': loan_id,
            'user_id': user_id,
            'status' : "Cancelled"
        }
    )
    try:
        print(f"📢 Sending message to Kafka: {logEntry}")
        send_log_sync(logEntry=logEntry)
        print("✅ Message successfully sent to Kafka!")
    except Exception as e:
        print(f"❌ Kafka Error: {e}")
        raise e
    raise Exception(f"Failed to evaluate property: {error_msg}")


@app.task(bind=True, max_retries=3, rate_limit="100/m")
def loan_decision(
    self,
    result
):
    """
    Celery Task: Evaluates property project based on loan amount.
    """
    print(result)
    payload = {
        "credit_check_response": result[0],
        "property_check_response": result[1]
    }

    headers = {
        "Content-Type": "application/json"
    }
    
    start_time = get_current_date()
    try:
        response = requests.post(DECISION_URL, json=payload, headers=headers)   
    except Exception as e:
        raise self.retry(exc=e, countdown=DECISION_COUNTDOWN)
    # logs
    end_time = get_current_date()
    status_code = response.status_code
    response = response.json()
    if status_code == 201:
        # send notification
        print('📢 send notification')
        notify_response = asyncio.run(
            notify(
                user_id=result[-1]['user_id'],
                loan_id=result[-1]['loan_id'],
                password=ADMIN_PASSWORD,
                loan_status=response.get("status"),
                finish=True,
                message=response.get("message"),
                url=NOTIFICATION_URL
            )
        )
        if notify_response.status_code != 201:
            error_msg = notify_response.json().get('detail')
            error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
            print(f'❌ notification error: {error_msg}')
        else:
            print("✅ Notification successfully sent !") 

        # udpate 
        print('✅ udpate final loan (all good)')
        update_response = asyncio.run(
                update_loan_request(
                    user_id=result[-1]['user_id'],
                    loan_id=result[-1]['loan_id'],
                    password=ADMIN_PASSWORD,
                    loan_status=response.get("status"),
                    loan_message=response.get("message"),
                    credit_check_response=response.get('credit_check_response', None),
                    property_check_response=response.get('property_check_response', None),
                    repaymentSchedule=response.get('repaymentSchedule', None),
                    url=UPDATE_LOAN_URL,
                )
            )
        if update_response.status_code != 201:
            error_msg = update_response.json().get('detail')
            error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
            print(f'❌ update error: {error_msg}')
        else:
            print("✅ loan was successfully updated !")  

        logEntry = LogEntry(
            service='decision-app',
            endpoint='loan_decision',
            method='POST', 
            status=status_code,
            log_message=response.get("message"),
            start_time=start_time,
            end_time=end_time,
            metadata={
                'loan_id': result[-1]['loan_id'],
                'user_id': result[-1]['user_id'],
                'status': response.get("status"),
            }
        )
        try:
            print(f"📢 Sending message to Kafka: {logEntry}")
            send_log_sync(logEntry=logEntry)
            print("✅ Message successfully sent to Kafka!")  
        except Exception as e:
            print(f"❌ Kafka Error: {e}")
            raise e
        return response
    error_msg = response.get('detail')
    error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg

    # notify error
    notify_response = asyncio.run(
            notify(
                user_id=result[-1]['user_id'],
                loan_id=result[-1]['loan_id'],
                password=ADMIN_PASSWORD,
                loan_status="Cancelled",
                finish=True,
                message=error_msg,
                url=NOTIFICATION_URL
            )
        )
    if notify_response.status_code != 201:
            error_msg = notify_response.json().get('detail')
            error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
            print(f'❌ notification error: {error_msg}')
    else:
        print("✅ Notification successfully sent !")  

    # update loan 
    print(f"❌ update loan before")
    update_response = asyncio.run(
        update_loan_request(
            user_id=result[-1]['user_id'],
            loan_id=result[-1]['loan_id'],
            password=ADMIN_PASSWORD,
            loan_status="Cancelled",
            loan_message=error_msg,
            url=UPDATE_LOAN_URL,

        )
    )
    if update_response.status_code != 201:
        error_msg = update_response.json().get('detail')
        error_msg = error_msg[0].get('msg') if isinstance(error_msg, list) else error_msg
        print(f'❌ update error: {error_msg}')
    else:
        print("✅ loan was successfully updated !")

    # send log
    logEntry: LogEntry = LogEntry(
        service='decision-app',
        endpoint='loan_decision',
        method='POST', 
        status=status_code, 
        message=error_msg,
        start_time=start_time,
        end_time=end_time,
        metadata={
            'loan_id': result[-1]['loan_id'],
            'user_id': result[-1]['user_id'],
            'status' : "Cancelled"
        }
    )
    try:
        print(f"📢 Sending message to Kafka: {logEntry}")
        send_log_sync(logEntry=logEntry)
        print("✅ Message successfully sent to Kafka!")
    except Exception as e:
        print(f"❌ Kafka Error: {e}")
        raise e
    raise Exception(f"Failed to compute final decision {error_msg}")
