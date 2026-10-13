import itertools
from locust import HttpUser, task, between

ROOM_ID = "6ace6629938aee17ecf07d37"
_counter = itertools.count(1)

class ChatUser(HttpUser):
    wait_time = between(2, 5)

    def on_start(self):
        n = next(_counter) % 50 + 1
        self.email = f"testuser{n}@example.com"
        self.latest_seq = 1

        res = self.client.post("/api/auth/login", data={
            "username": self.email,        # the email goes in the "username" field
            "password": "password123",
        }, name="POST /login")
        if res.status_code != 200:
            raise Exception(f"Login failed for {self.email}: {res.status_code} {res.text}")

        token = res.json()["token"]["access_token"]
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(3)
    def load_rooms(self):
        with self.client.get("/users/get-user-rooms", headers=self.headers,
                            name="GET /rooms", catch_response=True) as res:
            if res.status_code != 200:
                res.failure(f"{res.status_code} {res.text}")

    @task(2)
    def load_messages(self):
        with self.client.get(f"/room/{ROOM_ID}/messages?limit=50", headers=self.headers,
                            name="GET messages", catch_response=True) as res:
            if res.status_code != 200:
                res.failure(f"{res.status_code} {res.text}")
            else:
                msgs = res.json().get("messages", [])
                if msgs:
                    self.latest_seq = max(m["seq"] for m in msgs)

    @task(1)
    def mark_read(self):
        with self.client.put(
            f"/users/read-messages?room_id={ROOM_ID}&seq={self.latest_seq}",
            headers=self.headers,
            name="PUT read",
            catch_response=True,
        ) as res:
            if res.status_code != 200:
                res.failure(f"status {res.status_code}")