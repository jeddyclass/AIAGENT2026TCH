import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# task_queue.py

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    task_id: str
    agent_id: str
    input_data: Any
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None

class TaskQueue:
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()  # 用於衝突處理

    def add_task(self, task: Task):
        with self.lock:
            self.queue.append(task)
            print(f"Task {task.task_id} added by {task.agent_id}.")

    def get_next_task(self, agent_id: str) -> Task | None:
        """Agent 呼叫此方法來領取下一個任務"""
        with self.lock:
            for task in self.queue:
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.PROCESSING
                    task.agent_id = agent_id
                    print(f"Task {task.task_id} picked up by {agent_id}.")
                    return task
            return None

    def complete_task(self, task_id: str, result: Any):
        with self.lock:
            for task in self.queue:
                if task.task_id == task_id:
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    print(f"Task {task_id} completed.")
                    return

# 模擬兩個Agent協作
class WorkerAgent:
    def __init__(self, agent_id: str, task_queue: TaskQueue):
        self.id = agent_id
        self.queue = task_queue

    def work(self):
        while True:
            task = self.queue.get_next_task(self.id)
            if task:
                print(f"  {self.id} processing task {task.task_id}...")
                time.sleep(2)  # 模擬處理時間
                # 假設處理結果
                result = f"Result from {self.id} for {task.input_data}"
                self.queue.complete_task(task.task_id, result)
            else:
                time.sleep(1)  # 沒有任務時休息

# 使用範例
if __name__ == "__main__":
    queue = TaskQueue()
    agent_a = WorkerAgent("WeatherAgent", queue)
    agent_b = WorkerAgent("BusAgent", queue)

    # 啟動Agent (背景執行緒)
    import threading
    threading.Thread(target=agent_a.work, daemon=True).start()
    threading.Thread(target=agent_b.work, daemon=True).start()

    # 加入任務
    queue.add_task(Task(task_id="1", agent_id="user", input_data="查天氣"))
    queue.add_task(Task(task_id="2", agent_id="user", input_data="查公車"))

    time.sleep(5)
    print("Final queue state:", queue.queue)
