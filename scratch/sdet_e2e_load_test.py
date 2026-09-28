import asyncio
import time
import httpx
import json

URL = "https://smart-recipe-coach-frontend-uhldsvz65a-ue.a.run.app/chat"

PROMPTS = [
    "Suggest a healthy recipe for Chicken Biryani 🍳",
    "Calculate nutrition and macros for Grilled Chicken Curry with Brown Rice",
    "Calculate nutrition and macros for Coca Cola",
    "Calculate nutrition and macros for Tandoori Chicken",
    "generate a short video of sizzling salmon steak on a pan",
    "What is in my pantry?",
]

async def send_request(client, prompt, user_id):
    start = time.time()
    try:
        resp = await client.post(
            URL,
            json={"message": prompt, "user_id": user_id},
            timeout=30.0
        )
        elapsed = time.time() - start
        status = resp.status_code
        data = resp.json() if status == 200 else resp.text
        return {"prompt": prompt, "status": status, "elapsed": elapsed, "data": data, "error": None}
    except Exception as e:
        elapsed = time.time() - start
        return {"prompt": prompt, "status": 0, "elapsed": elapsed, "data": None, "error": str(e)}

async def run_functional_e2e_tests():
    print("\n--- 🧪 RUNNING E2E FUNCTIONAL TESTS ---")
    async with httpx.AsyncClient() as client:
        for idx, prompt in enumerate(PROMPTS):
            res = await send_request(client, prompt, f"sdet-user-{idx}")
            print(f"[{res['status']}] {res['elapsed']:.2f}s | Prompt: '{prompt[:40]}...'")
            if res['status'] == 200:
                parts = res['data'].get("parts", [])
                print(f"   -> Returned {len(parts)} part(s). First part type: {parts[0].get('kind') if parts else 'empty'}")
            else:
                print(f"   -> ❌ Error: {res['error']}")

async def run_load_test(concurrent_users=10, total_requests=30):
    print(f"\n--- ⚡ RUNNING LOAD TEST ({concurrent_users} concurrent users, {total_requests} total requests) ---")
    sem = asyncio.Semaphore(concurrent_users)

    async def worker(req_id, client):
        async with sem:
            prompt = PROMPTS[req_id % len(PROMPTS)]
            user_id = f"load-user-{req_id % 5}"
            return await send_request(client, prompt, user_id)

    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=50, max_keepalive_connections=20)) as client:
        tasks = [worker(i, client) for i in range(total_requests)]
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_duration = time.time() - start_time

    successes = [r for r in results if r["status"] == 200]
    failures = [r for r in results if r["status"] != 200]
    durations = [r["elapsed"] for r in successes]

    print("\n📊 --- LOAD TEST RESULTS ---")
    print(f"Total Time: {total_duration:.2f}s")
    print(f"Successful Requests: {len(successes)} / {total_requests} ({len(successes)/total_requests*100:.1f}%)")
    print(f"Failed Requests: {len(failures)}")
    if durations:
        print(f"Min Latency: {min(durations):.2f}s")
        print(f"Avg Latency: {sum(durations)/len(durations):.2f}s")
        print(f"Max Latency: {max(durations):.2f}s")
        print(f"Throughput (RPS): {len(successes)/total_duration:.2f} req/s")

if __name__ == "__main__":
    asyncio.run(run_functional_e2e_tests())
    asyncio.run(run_load_test(concurrent_users=10, total_requests=30))
