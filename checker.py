import os,re,random,threading,requests
from queue import Queue

def parse_proxies_from_text(text: str) -> list:
    proxies = []
    for token in re.split(r'[\s,;]+', text):
        for part in re.findall(r'(?:https?|socks[45])://(?:(?!https?://|socks[45]://)[^\s,;])+', token, re.I) or [token]:
            part = part.strip()
            if not part:
                continue
            proto = "http"
            if "://" in part:
                proto, part = part.split("://", 1)
            
            user_pass, host_port = "", part
            if "@" in part:
                user_pass, host_port = part.split("@", 1)
            elif part.count(":") == 3:
                p = part.split(":")
                if p[1].isdigit() and 1 <= int(p[1]) <= 65535:
                    host_port, user_pass = f"{p[0]}:{p[1]}", f"{p[2]}:{p[3]}"
                else:
                    user_pass, host_port = f"{p[0]}:{p[1]}", f"{p[2]}:{p[3]}"
            
            uri = f"{proto}://{user_pass}@{host_port}" if user_pass else f"{proto}://{host_port}"
            proxies.append({"http": uri, "https": uri})
    return proxies

class GunsLolUsernameChecker:
    def __init__(self):
        self.lock = threading.Lock()
        self.proxies = []
        
    def load_proxies(self):
        if not os.path.exists("proxies.txt"):
            print("proxies.txt not found. Running without proxies")
            return
        try:
            with open("proxies.txt", "r", encoding="utf-8", errors="ignore") as f:
                self.proxies = parse_proxies_from_text(f.read())
            print(f"loaded {len(self.proxies)} proxies from proxies.txt")
        except Exception as e:
            print(f"error loading proxies: {e}")
            
    def generate_name(self, length: int) -> str:
        letters = "abcdefghijklmnopqrstuvwxyzöäå"
        numbers = "0123456789"
        return ''.join(random.choices(letters + numbers, k=length))
        
    def check_username(self, username: str) -> dict:
        try:
            url = f"https://guns.lol/api/auth/username/{username}/availability"
            headers = {
                "Accept": "*/*",
                "Cookie": "guns_clearance=710df0650c01b04bb9fce389f3a711c53a382f6106d217cb6ee9242b4ff89b09.1783722741.jN2H0CQ3Uj_1-91a2829c40474d4f1244de0dbab1c6e94321aa742df34864b844ac10573b2a73; GUNS_LOCALE=en",
                "Referer": "https://guns.lol/register?ref=header",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
            }
            proxy = random.choice(self.proxies) if self.proxies else None

            response = requests.get(url, headers=headers, timeout=10, proxies=proxy)

            if response.status_code == 200:

                available = response.json().get("available")

                if available is True:
                    with self.lock:

                        with open("valid_usernames.txt", "a", encoding="utf-8") as f:
                            f.write(f"{username}\n")
                    
                return {"username": username, "available": available}
            return {"username": username, "available": None, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"username": username, "available": None, "error": str(e)}
            
    def scan(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(" guns.lol username checker\n")
        self.load_proxies()
        
        try:
            count = int(input(" How many usernames to check ") or "100")
        except ValueError:
            count = 100
            
        try:
            length = int(input(" Username length (1-20): ") or "6")
            length = max(1, min(20, length))
        except ValueError:
            length = 6
            
        try:
            threads = int(input(" How many threads? ") or "5")
            threads = max(1, min(100, threads))
        except ValueError:
            threads = 5
            
        print(f"\n cheking {count} usernames (length {length})")
        queue = Queue()
        for _ in range(count):
            queue.put(self.generate_name(length))
            
        print("started \n")
        
        def worker():
            while not queue.empty():
                try:
                    username = queue.get_nowait()
                    result = self.check_username(username)
                    avail = result.get("available")
                    if avail is True:
                        print(f"  VALID      | {username}")
                    elif avail is False:
                        print(f"  TAKEN      | {username}")
                    else:
                        print(f"  ERROR      | {username} ({result.get('error', 'unknown error')})")
                    queue.task_done()
                except Exception:
                    break
                    
        thread_list = []
        for _ in range(threads):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            thread_list.append(t)
            
        for t in thread_list:
            t.join()
            
        print("\n Finished checking")

if __name__ == "__main__":
    GunsLolUsernameChecker().scan()