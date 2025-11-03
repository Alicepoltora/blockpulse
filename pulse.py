import requests
import time
import statistics

class BlockPulse:
    def __init__(self, rpc_url: str, window_size: int = 20):
        """
        rpc_url: адрес RPC узла (например, https://rpc.ankr.com/eth)
        window_size: количество последних блоков для анализа
        """
        self.rpc_url = rpc_url
        self.window_size = window_size

    def _rpc_call(self, method, params=[]):
        """Отправка JSON-RPC запроса"""
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        r = requests.post(self.rpc_url, json=payload, timeout=10)
        r.raise_for_status()
        return r.json()["result"]

    def get_latest_block(self):
        """Получить номер последнего блока"""
        block_hex = self._rpc_call("eth_blockNumber")
        return int(block_hex, 16)

    def get_block_timestamp(self, block_number: int):
        """Получить временную метку блока"""
        block = self._rpc_call("eth_getBlockByNumber", [hex(block_number), False])
        return int(block["timestamp"], 16)

    def compute_health_index(self):
        """Вычислить Network Health Index (0–100)"""
        latest = self.get_latest_block()
        timestamps = []

        for i in range(latest - self.window_size, latest):
            try:
                ts = self.get_block_timestamp(i)
                timestamps.append(ts)
            except Exception:
                continue

        if len(timestamps) < 2:
            return None

        intervals = [t2 - t1 for t1, t2 in zip(timestamps, timestamps[1:])]
        avg = statistics.mean(intervals)
        std = statistics.pstdev(intervals)

        # Чем стабильнее блок-тайм, тем выше индекс
        score = max(0, 100 - (std / avg * 100))
        return round(score, 2), avg, std

    def live_monitor(self, interval=60):
        """Наблюдать за сетью в реальном времени"""
        print("🔍 Starting BlockPulse live monitor...")
        while True:
            result = self.compute_health_index()
            if result:
                score, avg, std = result
                print(f"⛓ NHI: {score}/100 | avg_block_time: {avg:.2f}s | jitter: {std:.2f}")
            else:
                print("⚠️ Недостаточно данных...")
            time.sleep(interval)
