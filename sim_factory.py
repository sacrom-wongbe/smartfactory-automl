import simpy
import random
import pandas as pd
from datetime import datetime, timedelta

import requests

API_GATEWAY_URL = "https://bwpwc9xl4h.execute-api.us-west-2.amazonaws.com/data"

def send_to_aws(row_dict):
    try:
        response = requests.post(
            API_GATEWAY_URL,
            headers={'Content-Type': 'application/json'},
            json=row_dict
        )
        if response.status_code != 200:
            print(f"❌ Error sending row: {response.status_code}, {response.text}")
        else:
            print(f"✅ Row sent successfully: {row_dict['MachineID']} at {row_dict['Timestamp']}")
    except Exception as e:
        print("❌ Exception while sending row:", e)




class Machine:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.data = []
        print(f"Registering machine {self.name}")
        self.process = env.process(self.run())  # Register machine as a SimPy process

    def run(self):
        current_time = datetime.now()

        while True:
            status = self.get_status()
            temperature = self.get_temperature(status)
            energy = self.get_energy(status)
            vibration = self.get_vibration(status)
            throughput = self.get_throughput(status)
            error_code = self.get_error_code(status)

            row_dict = {
                "Timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'),
                "MachineID": self.name,
                "Status": status,
                "Temperature": temperature,
                "Energy_kWh": energy,
                "Vibration": vibration,
                "Throughput": throughput,
                "ErrorCode": error_code
            }
            # Save a list version for local CSV storage
            self.data.append(list(row_dict.values()))

            # Send to AWS here
            send_to_aws(row_dict)

            if len(self.data) % 50 == 0:
                print(f"[{self.name}] Generated {len(self.data)} rows...")

            current_time += timedelta(minutes=5)
            yield self.env.timeout(5)

    def get_status(self):
        choices = ['Running', 'Idle', 'Fault', 'Offline']
        weights = [0.7, 0.15, 0.1, 0.05]
        return random.choices(choices, weights=weights)[0]

    def get_temperature(self, status):
        if status == 'Running':
            return round(random.gauss(65, 3), 2)
        elif status == 'Idle':
            return round(random.gauss(55, 2), 2)
        elif status == 'Fault':
            return round(random.gauss(85, 5), 2)
        elif status == 'Offline':
            return 0.0

    def get_energy(self, status):
        if status == 'Running':
            return round(random.uniform(2.0, 3.0), 2)
        elif status == 'Idle':
            return round(random.uniform(0.5, 1.0), 2)
        elif status == 'Fault':
            return round(random.uniform(0.1, 0.3), 2)
        elif status == 'Offline':
            return 0.0

    def get_vibration(self, status):
        if status == 'Running':
            return round(random.gauss(150, 10), 2)
        elif status == 'Idle':
            return round(random.gauss(50, 5), 2)
        elif status == 'Fault':
            return round(random.gauss(200, 20), 2)
        elif status == 'Offline':
            return 0.0

    def get_throughput(self, status):
        if status == 'Running':
            return random.randint(1, 5)
        else:
            return 0

    def get_error_code(self, status):
        if status == 'Fault':
            error_codes = ['E001', 'E002', 'E003', 'E004', 'E005']
            return random.choice(error_codes)
        else:
            return None
                  
def simulate():
    env = simpy.Environment()
    machines = [Machine(env, f'M{i}') for i in range(1, 4)]  # M1, M2, M3

    sim_duration = 288  # 288 steps = 1 day at 5-minute intervals
    env.run(until=sim_duration)

    # Combine all machine data
    all_data = []
    for m in machines:
        all_data.extend(m.data)

    df = pd.DataFrame(all_data, columns=[
        'Timestamp', 'MachineID', 'Status', 'Temperature',
        'Energy_kWh', 'Vibration', 'Throughput', 'ErrorCode'
    ])
    df.to_csv('factory_data.csv', index=False)
    print("Simulation complete. Data saved to factory_data.csv.")

if __name__ == "__main__":
    simulate()