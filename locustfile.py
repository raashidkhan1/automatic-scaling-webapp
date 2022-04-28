import time
from locust import HttpUser, task, between
import random

# usage: locust -f locustfile.py --headless -u 10 -r 1 -H http://192.168.0.105:5000 // replace ip with LB IP
class LoadTester(HttpUser):
    wait_time = between(1, 5)

    @task(5)
    def get_all(self):
        with self.client.get("/", catch_response=True) as response:
            if not response.text:
                response.failure("Got wrong response")
            elif response.elapsed.total_seconds() > 0.5:
                response.failure("Request took too long")

    @task(1)
    def delete_all(self):
        self.client.delete("/")

    @task(3)
    def get_obj_content(self):
        rand_num = random.randrange(100, 200)
        self.client.get(f"/objs/{rand_num}")

    @task(6)
    def put(self):
        rand_num = random.randrange(100, 200)
        content = ""
        for i in range(1000):
            content += str(i) + '\n'
        self.client.put(f"/objs/{rand_num}",data={"content": f"{content}"})
        time.sleep(1)
    
    @task(2)
    def delete_obj(self):
        rand_num = random.randrange(100, 200)
        self.client.delete(f"/objs/{rand_num}")

    @task(4)
    def get_obj_checksum(self):
        rand_num = random.randrange(100, 200)
        self.client.get(f"/objs/{rand_num}/checksum")