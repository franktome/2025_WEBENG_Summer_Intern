import time
from locust import HttpUser, task, constant, LoadTestShape

# request.txt 읽기
lines = [int(x.strip()) for x in open("request.txt")]
EP_LEN = len(lines)
WINDOW = 15

class MyUser(HttpUser):
    wait_time = constant(1)
    host = "http://143.248.47.134:30556"  # Bookinfo Gateway 주소

    @task(1)
    def productpage(self):
        self.client.get("/productpage")


class StagesShape(LoadTestShape):
    def __init__(self):
        super().__init__()
        self.t0 = time.time()

    def tick(self):
        run_time = time.time() - self.t0
        idx = int(run_time // WINDOW) % EP_LEN
        users = max(1, int(lines[idx]/300))
        return (users, users*2)
