import asyncio
import httpx
import sys

BASE_URL = "http://127.0.0.1:8000"

async def verify_routing():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Login to get token
        print("1. Logging in...")
        login_resp = await client.post("/login", json={"email": "admin@example.com", "password": "adminpassword"})
        if login_resp.status_code != 200:
            print(f"Login Failed: {login_resp.text}")
            sys.exit(1)
        token = login_resp.json()["access_token"]

        # 2. Get API Key
        print("2. Getting API Key...")
        headers = {"Authorization": f"Bearer {token}"}
        key_resp = await client.post("/api-keys", headers=headers)
        api_key = key_resp.json()["api_key"]
        print(f"API Key: {api_key[:10]}...")

        # 3. Test Smart Routing (model="auto")
        print("\n3. Testing Smart Routing (model='auto')...")
        auth_headers = {"X-API-KEY": api_key}
        payload = {
            "model": "auto",
            "prompt": "Explain simple routing heuristics",
            "max_tokens": 100
        }
        
        try:
            resp = await client.post("/infer", json=payload, headers=auth_headers)
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print("Success!")
                print(f"Selected Provider: {data.get('provider')}") 
                print(f"Latency: {data.get('latency_ms')}ms")
                print(f"Model Used: {data.get('model')}")
                
                # Check if it selected the expected provider (Mock has score ~2.0, Gemini ~1.98 if cost=0.1875)
                # Wait, Mock: lat=200/100=2, cost=0 = 2.0
                # Gemini: lat=180/100=1.8, cost=0.1875*1000 = 187.5?? NO.
                # Let's check ModelRouter logic in code I read earlier.
                # Cost is usually small. verify logic.
            else:
                print(f"Error Body: {resp.text}")
        except httpx.ReadTimeout:
            print("Request timed out (Provider might be slow)")

if __name__ == "__main__":
    asyncio.run(verify_routing())
