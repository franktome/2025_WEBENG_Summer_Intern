from locust import HttpUser, task, constant, LoadTestShape

# request.txt 읽기
lines = [int(x.strip()) for x in open("request.txt")]

class MyUser(HttpUser):
    wait_time = constant(1)
    host = "http://143.248.47.134:30556"  # Bookinfo Gateway 주소

    @task(1)
    def productpage(self):
        self.client.get("/productpage")


class StagesShape(LoadTestShape):
    def __init__(self):
        super().__init__()
        self.lines = lines

    def tick(self):
        run_time = self.get_run_time()
        idx = int(run_time / 15)  # 15초 단위로 한 줄씩 사용
        if idx < len(self.lines):
            users = max(1, int(self.lines[idx] / 300))  # 사용자 수 조정
            return (users, users * 2)  # (현재 사용자 수, 스폰 속도)
        else:
            return None
