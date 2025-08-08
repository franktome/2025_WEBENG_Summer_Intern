from locust import HttpUser, task, constant, LoadTestShape
import random

# request.txt 읽기
lines = [int(x.strip()) for x in open("request.txt")]

class MyUser(HttpUser):
    wait_time = constant(1)
    # host = "http://<VMware 클러스터의 NodePort 주소>"  # 예: http://143.248.47.134:30001
    host = "http://143.248.47.134:31166"
    @task(1)
    def index(self):
        self.client.get("/")  # VM에 배포된 앱의 엔드포인트로 요청


class StagesShape(LoadTestShape):
    def __init__(self):
        super().__init__()
        self.lines = lines

    def tick(self):
        run_time = self.get_run_time()
        idx = int(run_time / 15)  # 5초 단위로 1분 데이터를 빠르게 재생
        if idx < len(self.lines):
            users = max(1, int(self.lines[idx] / 300))  # 너무 많으면 스케일 다운
            return (users, users * 2)
        else:
            return None
