import asyncio
import aiohttp
import time
import os
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import my_pb2
import output_pb2

class FreeFireTokenGetter:
    def __init__(self):
        self.aes_key = b'Yg&tc%DEuh6%Zc^8'
        self.aes_iv = b'6oyZDr22E3ychjM%'
        self.input_file = "acc.txt"
        self.output_file = "tokenlikes.txt"
        self.max_workers = 200 
        self.max_retries = 10
        self.models = ['SM-A125F','SM-A225F','SM-A325M','SM-A515F','SM-A725F','Redmi 9A','Redmi 9C','POCO M3','POCO M4 Pro','moto g(9) play']
        self.android_versions = ['9','10','11','12','13','14']
        self.versions = ['4.0.18P6','4.1.0P3','4.2.1P8','5.0.1B2','5.1.0P1','5.2.5P3','5.3.2P2','5.4.3B2','5.5.2P3']
        self.builds = {
            '9':['PKQ1.190616.001'],'10':['QP1A.190711.020'],'11':['RP1A.200720.011'],
            '12':['SP1A.210812.016'],'13':['TP1A.220624.014'],'14':['UP1A.231005.007']
        }
        self.langs = ['en-US','id-ID','vi-VN']
        self._proto_template = None

    def _get_random_ip(self):
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

    def _get_proto_template(self):
        if self._proto_template is None:
            g = my_pb2.GameData()
            fields = {
                "timestamp": "2026-04-08 18:05:57",
                "game_name": "free fire",
                "game_version": 1,
                "version_code": "1.123.2",
                "os_info": "Android OS 9 / API-28 (PQ3A.190605.03171033/3793265)",
                "device_type": "Handheld",
                "network_provider": "MobiFone",
                "connection_type": "WIFI",
                "screen_width": 1600,
                "screen_height": 900,
                "dpi": "240",
                "cpu_info": "x86-64 SSE3 SSE4.1 SSE4.2 AVX | 2865 | 4",
                "total_ram": 3004,
                "gpu_name": "Adreno (TM) 640",
                "platform_type": 1,
                "device_model": "Xiaomi 2203121C",
                "marketplace": "Handheld",
                "encryption_key": "KqsHT1y2dlDX0ywnP1LQ75AXqqV8YVvFC48pUhDlHSFPi7zihMoH4je/A9lW1Sa5OUKZngMdKfCwTE8lUtNlp7X97/w=",
                "total_storage": 49386,
                "field_97": 1,
                "field_98": 1,
                "field_99": "4",
                "field_100": "4"
            }
            for k, v in fields.items():
                setattr(g, k, v)
            self._proto_template = g
        return self._proto_template

    def rand_ua_dalvik(self):
        m = random.choice(self.models)
        v = random.choice(self.android_versions)
        b = random.choice(self.builds.get(v, ['QP1A.190711.020']))
        return f"Dalvik/2.1.0 (Linux; U; Android {v}; {m} Build/{b})"

    def rand_ua_garena(self):
        return f"GarenaMSDK/{random.choice(self.versions)}({random.choice(self.models)};Android {random.choice(self.android_versions)};{random.choice(self.langs)};)"

    def encrypt(self, data):
        try:
            c = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
            return c.encrypt(pad(data, AES.block_size))
        except:
            return None

    async def get_oauth(self, session, uid, pwd):
        try:
            ip_premium = self._get_random_ip()
            
            async with session.post(
                "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant",
                data={
                    "uid": uid, "password": pwd, "response_type": "token",
                    "client_type": "2", "client_id": "100067",
                    "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
                },
                headers={
                    "User-Agent": self.rand_ua_garena(),
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Forwarded-For": ip_premium,
                    "Client-IP": ip_premium,
                    "X-Real-IP": ip_premium
                },
                timeout=aiohttp.ClientTimeout(total=8, connect=4),
                ssl=False
            ) as r:
                if r.status == 200:
                    j = await r.json()
                    print(f"[INFO] {uid} - {j}")
                    return j.get("access_token"), j.get("open_id")
        except asyncio.TimeoutError:
            return "TIMEOUT", None
        except:
            pass
        return None, None

    async def get_major_token(self, session, oauth, oid):
        if not oauth or not oid:
            return None
        
        template = self._get_proto_template()
        setattr(template, "open_id", oid)
        setattr(template, "access_token", oauth)

        encrypted = self.encrypt(template.SerializeToString())
        if not encrypted:
            return None
        
        try:
            ip_premium = self._get_random_ip()
            
            async with session.post(
                "https://loginbp.ggblueshark.com/MajorLogin",
                data=encrypted,
                headers={
                    "User-Agent": self.rand_ua_dalvik(),
                    "Content-Type": "application/octet-stream",
                    "X-GA": "v1 1",
                    "ReleaseVersion": "OB54",
                    "X-Forwarded-For": ip_premium,
                    "Client-IP": ip_premium,
                    "X-Real-IP": ip_premium
                },
                timeout=aiohttp.ClientTimeout(total=10, connect=4),
                ssl=False
            ) as r:
                print(f"[INFO] MajorLogin {oid} - {r.status}")
                if r.status == 200:
                    msg = output_pb2.Garena_420()
                    msg.ParseFromString(await r.read())
                    token = getattr(msg, 'token', None)
                    print(token)
                    return token
        except asyncio.TimeoutError:
            pass
        except:
            pass
        return None

    async def try_one(self, session, line):
        if ":" not in line: return None
        uid, pwd = line.strip().split(":", 1)
        for _ in range(self.max_retries):
            oauth, oid = await self.get_oauth(session, uid, pwd)
            if oauth == "TIMEOUT":
                continue
            if oauth and oid:
                token = await self.get_major_token(session, oauth, oid)
                if token:
                    print(f"[OK] {uid}")
                    return token
            await asyncio.sleep(0.01)
            
        print(f"[X] {uid}")
        return None

    async def run(self):
        if not os.path.exists(self.input_file):
            print(f"Không thấy {self.input_file}")
            return
        with open(self.input_file, encoding="utf-8", errors="ignore") as f:
            accs = [l.strip() for l in f if ":" in l.strip()]
        if not accs:
            print("File rỗng")
            return
        print(f"Bắn tốc độ tối đa cho {len(accs)} Acc...")
        connector = aiohttp.TCPConnector(
            limit=0, 
            limit_per_host=0, 
            ssl=False, 
            use_dns_cache=True,
            ttl_dns_cache=300
        )
        
        async with aiohttp.ClientSession(connector=connector) as s:
            sem = asyncio.Semaphore(self.max_workers)
            async def bounded(acc):
                async with sem: return await self.try_one(s, acc)
            tasks = [bounded(a) for a in accs]
            tokens = [t for t in await asyncio.gather(*tasks, return_exceptions=True) if isinstance(t, str) and t]
            
        if tokens:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(tokens) + "\n")
            print(f"Đã Lưu {len(tokens)} Token Vào {self.output_file}")
        else:
            print("Không File Token")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(FreeFireTokenGetter().run())