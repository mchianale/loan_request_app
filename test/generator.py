from faker import Faker
import random
from datetime import datetime, timedelta
from client import register, login, update_credits_history, create_loan_request, retrieve_user_information
import asyncio 
import threading
import time
from tqdm import tqdm

TOTAL_USER = 250

# init faker 
fake = Faker()

def random_date(start_year=1960, end_year=2002):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    random_days = random.randint(0, (end_date - start_date).days)
    return (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")

def generateFakeRequest():
    credit = {}
    credit['credit_type'] = random.choice([
        "Consumer Loan",
        "Mortgage",
        "Auto Loan",
        "Personal Loan",
        "Business Loan"
    ])
    rate = random.choice([10000, 10000,10000, 100000, 100000, 1000000])
    credit['loan_amount'] = random.random()*rate + 1500
    credit['duration_months'] = random.randint(1, 240)
    credit['purpose']= fake.text()
    credit['property_location'] = fake.address()
    credit['property_value'] =  random.random()*rate + 1500
    credit['property_type'] = random.choice([
        "House",
        "Apartment",
        "Land",
        "Commercial",
        "Other",
    ])
    return credit

def generateFakeCredit():
    credit = {}
    credit['credit_type'] = random.choice([
        "Consumer Loan",
        "Mortgage",
        "Auto Loan",
        "Personal Loan",
        "Business Loan"
    ])
    credit['start_date'] = random_date(end_year=2025)
    credit['amount'] = random.random()*1000000 + 1500
    credit['duration_months'] = random.randint(1, 240)
    credit['annual_rate'] = random.random()*5 + 0.5
    credit['status'] = random.choice([
        "Ongoing",
        "Completed",
        "Canceled"
    ])
    payment_history = []
    for i in range(random.randint(0, 100)):
        payment = {
            "payment_date" : random_date(),
            "status" : random.choice([
                "Paid on time","Paid late","Never paid"
            ])
        }
        payment_history.append(payment)
    credit['payment_history'] = payment_history
    return credit 


class ourClient():
    def __init__(self):
        self.client = {}
        # last_name, first_name
        name = fake.name().split(' ')
        self.client['first_name'], self.client['last_name'] = name[0], " ".join(name[1:])

        # range
        r = random.choice([0,1,2,3])
        if r == 0:
            self.client['gross_monthly_income'] = random.random()*1200
        elif r == 1:
            self.client['gross_monthly_income'] = random.random()*2500
        elif r == 2:
            self.client['gross_monthly_income'] = random.random()*5000
        else:
            self.client['gross_monthly_income'] = random.random()*20000

        self.client['date_of_birth']=random_date()
        self.client['address']=fake.address()
        self.client['marital_status'] = random.choice(["Married", "Single"])
        self.client['tax_residence']="US"
        self.client['nationality']="American"
        self.client['email']=self.client['first_name'].replace(' ', '_') + str(random.randint(0, 1000)) + "@gmail.com"
        self.client['phone']="+" + "".join(str(random.randint(0, 9)) for _ in range(9))
        self.client['number_of_dependents']=random.randint(0,6)
        self.client['work_status'] = random.choice([
                        "Employed",
                        "Self-employed",
                        "Unemployed",
                        "Student",
                        "Retired",
                        "Other"
                    ])
        
        self.client['username'] = self.client['email']
        self.client['password'] = "Test12345*"

        self.already_register = False
        self.access_token = None

    def log(self):
        if self.access_token is not None:
            return
        if self.already_register == False:
            try:
                response = asyncio.run(
                        register(
                            **self.client
                        )
                    )
                if response.status_code == 201:
                    self.access_token = response.json()['token']['access_token']
                    self.already_register = True
                else:
                    print(response.json())
                    print(self.client)
                    print('-'*100)
            except:
                return 
        else:
            try:
                response = asyncio.run(login(username=self.client["username"], password=self.client["password"]))
                if response.status_code == 201:
                    self.access_token = response.json()['token']['access_token']
                else:
                    print(response.json())
                    print(self.client)
                    print('-'*100)
            except:
                return 

    def update_credits(self):
        if not self.access_token:
            return
        credits = []
        for i in range(random.randint(1,10)):
            credits.append(generateFakeCredit())
        try:
            response = asyncio.run(
            update_credits_history(
                    access_token=self.access_token,
                    credits=credits
                )
            )
            if response.status_code > 201:
                print(response.json())
                print(self.access_token)
                print('-'*100)
                self.access_token = None
                
        except:
            self.access_token = None
            
    
    def create_new_request(self):
        if not self.access_token:
            return
        request = generateFakeRequest() | {"access_token": self.access_token}
        try:
            response = asyncio.run(
                create_loan_request(
                    **request
                )
            )
            if response.status_code > 201:
                print(response.json())
                print(self.access_token)
                print('-'*100)
                self.access_token = None
                
        except:
            self.access_token = None
         
            
    def retrieve_information(self):
        if not self.access_token:
            return
        try: 
            response = asyncio.run(retrieve_user_information(access_token=self.access_token))
            if response.status_code > 201:
                print(response.json())
                print(self.access_token)
                print('-'*100)
                self.access_token = None
        except:
            self.access_token = None

if __name__ == '__main__':
    users = []
    actions = {}
    for i in range(TOTAL_USER):
        users.append(ourClient())

    for i in tqdm(range(1000), desc="generate traffic"):
        n_current_user = random.randint(0, min(10, TOTAL_USER))
        current_users = random.sample(users, n_current_user)
        threads = []
        for user in current_users:
            if user.access_token is None:
                thread = threading.Thread(target=user.log)
                thread.start()
                threads.append(thread)
            if user.client['username'] not in actions:
                actions[user.client['username']] = 0
        for user in current_users:
            if random.choice([0,1,2,4,5]) <= 1:
                thread = threading.Thread(target=user.update_credits)
                thread.start()
                threads.append(thread)
                 
            if random.choice([0,1,2,4,5]) <= 1:
                thread = threading.Thread(target=user.retrieve_information)
                thread.start()
                threads.append(thread)
                
        for user in current_users:
            thread = threading.Thread(target=user.create_new_request)
            thread.start()
            threads.append(thread)
            actions[user.client['username']] += 1

        for thread in threads:
            thread.join()
         
        time.sleep(random.random()*2)

    n_actions = 0
    best, max = None, None
    for k,v in actions.items():
        if max is None:
            max = v
            best = k 
        elif max < v:
            max = v 
            best = k
        n_actions += v

    print(f"Compute {n_actions} actions on {len(list(actions.keys()))}")
    print('Best client', k)

            
 