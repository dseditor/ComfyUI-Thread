import os
import json
import requests
from datetime import datetime, timedelta
from PIL import Image
import numpy as np
import torch

# 嘗試導入 ComfyUI 的 folder_paths，如果失敗則使用備用方案
try:
    import folder_paths
    def get_output_directory():
        return folder_paths.get_output_directory()
except ImportError:
    # 備用方案：假設在 ComfyUI 目錄結構中
    def get_output_directory():
        # 從當前文件位置向上查找 ComfyUI 根目錄
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 嘗試找到 ComfyUI 根目錄（包含 output 資料夾）
        while current_dir != os.path.dirname(current_dir):  # 直到根目錄
            output_path = os.path.join(current_dir, "output")
            if os.path.exists(output_path):
                return output_path
            current_dir = os.path.dirname(current_dir)
        
        # 如果找不到，在當前目錄創建 output 資料夾
        fallback_output = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(fallback_output, exist_ok=True)
        return fallback_output

# 確保 token 目錄存在
TOKEN_DIR = os.path.join(os.path.dirname(__file__), "token")
os.makedirs(TOKEN_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(TOKEN_DIR, "thread_config.json")
URL_CONFIG_FILE = os.path.join(TOKEN_DIR, "url.json")

def load_base_url():
    """讀取基礎 URL 配置"""
    if os.path.exists(URL_CONFIG_FILE):
        with open(URL_CONFIG_FILE, 'r', encoding='utf-8') as f:
            url_config = json.load(f)
            return url_config.get("base_url", "http://127.0.0.1:8188")
    return "http://127.0.0.1:8188"

def save_base_url(base_url):
    """保存基礎 URL 配置"""
    url_config = {"base_url": base_url}
    with open(URL_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(url_config, f, ensure_ascii=False, indent=2)

class ThreadsAPI:
    def __init__(self, user_id, access_token, app_secret):
        self.user_id = user_id
        self.access_token = access_token
        self.app_secret = app_secret
        self.api_url = "https://graph.threads.net/v1.0"

    def get_long_live_access_token(self):
        resp = requests.get(
            f"{self.api_url}/access_token",
            params={
                "grant_type": "th_exchange_token",
                "client_secret": self.app_secret,
                "access_token": self.access_token,
            },
        )
        return resp.json()

    def create_media_container(
        self,
        text: str = None,
        media_type: str = "TEXT",
        image_url: str = None,
        video_url: str = None,
        is_carousel_item: bool = False,
    ) -> dict:
        params = {
            "access_token": self.access_token,
            "media_type": media_type,
        }

        # 只有非輪播項目才加入 text
        if not is_carousel_item and text:
            params["text"] = text

        if media_type == "IMAGE" and image_url is not None:
            params["image_url"] = image_url
        elif media_type == "VIDEO" and video_url is not None:
            params["video_url"] = video_url
        
        if is_carousel_item:
            params["is_carousel_item"] = "true"

        print(f"創建媒體容器參數: {params}")

        resp = requests.post(
            f"{self.api_url}/{self.user_id}/threads",
            params=params,
        )

        if resp.status_code != 200:
            print(f"API 錯誤回應: {resp.json()}")
            raise Exception(resp.json())

        return resp.json()

    def publish_container(self, media_id: str) -> dict:
        resp = requests.post(
            f"{self.api_url}/{self.user_id}/threads_publish",
            params={
                "creation_id": media_id,
                "access_token": self.access_token,
            },
        )

        if resp.status_code != 200:
            raise Exception(resp.json())

        return resp.json()

    def create_carousel_container(self, media_list: list, text: str = None) -> dict:
        media_id_list = ",".join(media_list)
        resp = requests.post(
            f"{self.api_url}/{self.user_id}/threads",
            params={
                "media_type": "CAROUSEL",
                "children": media_id_list,
                "access_token": self.access_token,
                "text": text,
            },
        )

        if resp.status_code != 200:
            raise Exception(resp.json())

        return resp.json()

    def get_user_bio(self):
        resp = requests.get(
            f"{self.api_url}/me",
            params={
                "fields": "username",
                "access_token": self.access_token,
            },
        )
        return resp.json()


class StartWithLongLiveToken:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "USER_ID": ("STRING", {"multiline": False, "default": ""}),
                "ACCESS_TOKEN": ("STRING", {"multiline": False, "default": ""}),
                "APP_SECRET": ("STRING", {"multiline": False, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "get_long_live_token"
    CATEGORY = "ComfyUI-Thread"

    def get_long_live_token(self, USER_ID, ACCESS_TOKEN, APP_SECRET):
        try:
            # 創建 ThreadsAPI 實例
            threads_api = ThreadsAPI(USER_ID, ACCESS_TOKEN, APP_SECRET)
            
            # 取得長期 access token
            result = threads_api.get_long_live_access_token()
            
            if "access_token" in result:
                new_access_token = result["access_token"]
                
                # 保存配置到 JSON 文件
                config = {
                    "USER_ID": USER_ID,
                    "ACCESS_TOKEN": new_access_token,
                    "APP_SECRET": APP_SECRET,
                    "created_at": datetime.now().isoformat(),
                    "expires_in": result.get("expires_in", 0)
                }
                
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                return (f"建立成功！新的 Long Live Token: {new_access_token}",)
            else:
                return (f"錯誤: {result}",)
                
        except Exception as e:
            return (f"錯誤: {str(e)}",)


class ThreadsHistory:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "backfill_days": ("INT", {"default": 7, "min": 1, "max": 365, "step": 1}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("history_content",)
    FUNCTION = "get_history"
    CATEGORY = "ComfyUI-Thread"

    def get_history(self, backfill_days):
        try:
            # 讀取配置
            if not os.path.exists(CONFIG_FILE):
                return ("錯誤: 請先執行 StartWithLongLiveToken 節點",)
            
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            threads_api = ThreadsAPI(
                config["USER_ID"],
                config["ACCESS_TOKEN"],
                config["APP_SECRET"]
            )
            
            # 獲取歷史貼文
            print(f"正在獲取過去 {backfill_days} 天的貼文...")
            
            # 設定回溯天數
            original_api = ThreadsAPI(config["USER_ID"], config["ACCESS_TOKEN"], config["APP_SECRET"])
            original_api.backfill_date_interval = backfill_days
            
            # 獲取貼文數據
            from datetime import timedelta
            start_date_dt = datetime.now() - timedelta(days=backfill_days)
            
            resp = requests.get(
                f"{original_api.api_url}/{config['USER_ID']}/threads",
                params={
                    "fields": "id,permalink,username,timestamp,text",
                    "since": str(start_date_dt.isoformat()),
                    "access_token": config["ACCESS_TOKEN"],
                    "limit": 100,  # 可以根據需要調整
                },
            )
            
            if resp.status_code != 200:
                return (f"API 錯誤: {resp.json()}",)
            
            data = resp.json().get("data", [])
            print(f"找到 {len(data)} 篇貼文")
            
            if not data:
                return (f"過去 {backfill_days} 天內沒有找到貼文",)
            
            # 格式化貼文內容
            history_content = f"=== 過去 {backfill_days} 天的 Threads 貼文 ===\n\n"
            
            for i, post in enumerate(data, 1):
                # 格式化時間
                timestamp = post.get('timestamp', '')
                if timestamp:
                    try:
                        # 解析 ISO 時間格式
                        post_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_time = post_time.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_time = timestamp
                else:
                    formatted_time = "未知時間"
                
                # 獲取貼文內容
                text_content = post.get('text', '(無文字內容)')
                permalink = post.get('permalink', '')
                post_id = post.get('id', '')
                
                # 添加到結果中
                history_content += f"第 {i} 篇貼文\n"
                history_content += f"時間: {formatted_time}\n"
                history_content += f"內容: {text_content}\n"
                history_content += f"連結: {permalink}\n"
                history_content += f"ID: {post_id}\n"
                history_content += "-" * 50 + "\n\n"
            
            return (history_content,)
            
        except Exception as e:
            return (f"錯誤: {str(e)}",)


class PublishThread:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "ComfyUIHttpsURL": ("STRING", {"multiline": False, "default": ""}),
                "image": ("IMAGE",),
                "image_url": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "publish_thread"
    CATEGORY = "ComfyUI-Thread"

    def publish_thread(self, text, ComfyUIHttpsURL="", image=None, image_url=""):
        try:
            # 讀取配置
            if not os.path.exists(CONFIG_FILE):
                return ("錯誤: 請先執行 StartWithLongLiveToken 節點",)
            
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            threads_api = ThreadsAPI(
                config["USER_ID"],
                config["ACCESS_TOKEN"],
                config["APP_SECRET"]
            )
            
            # 處理 ComfyUI URL 配置
            base_url = load_base_url()
            if ComfyUIHttpsURL.strip():
                # 更新 base URL
                base_url = ComfyUIHttpsURL.strip()
                save_base_url(base_url)
                print(f"更新基礎網址為: {base_url}")
            
            print(f"使用基礎網址: {base_url}")
            
            # 收集所有圖片
            image_urls = []
            
            # 處理圖片 tensor
            if image is not None:
                img_url = self._process_image(image, base_url)
                if img_url:
                    image_urls.append(img_url)
                    print(f"添加圖片 tensor URL: {img_url}")
            
            # 處理圖片網址
            if image_url.strip():
                print(f"原始圖片網址輸入: {repr(image_url)}")
                urls = [u.strip() for u in image_url.split('\n') if u.strip()]
                print(f"解析後的網址列表: {urls}")
                for url in urls:
                    if url.startswith('http://') or url.startswith('https://'):
                        image_urls.append(url)
                        print(f"添加有效網址: {url}")
                    else:
                        print(f"跳過無效網址: {url}")
            
            print(f"收集到的圖片網址總數: {len(image_urls)}")
            print(f"圖片網址列表: {image_urls}")
            
            # 發送邏輯
            if not image_urls:
                # 純文字發文
                media = threads_api.create_media_container(text=text)
                result = threads_api.publish_container(media["id"])
            elif len(image_urls) == 1:
                # 單張圖片
                media = threads_api.create_media_container(
                    text=text,
                    media_type="IMAGE",
                    image_url=image_urls[0]
                )
                result = threads_api.publish_container(media["id"])
            else:
                # 多圖片輪播
                media_ids = []
                for img_url in image_urls:
                    print(f"創建輪播項目: {img_url}")
                    media = threads_api.create_media_container(
                        media_type="IMAGE",
                        image_url=img_url,
                        is_carousel_item=True
                    )
                    print(f"輪播項目 ID: {media['id']}")
                    media_ids.append(media["id"])
                
                print(f"創建輪播容器，包含 {len(media_ids)} 個項目")
                carousel = threads_api.create_carousel_container(media_ids, text)
                print(f"輪播容器 ID: {carousel['id']}")
                result = threads_api.publish_container(carousel["id"])
            
            # 取得用戶名稱來組合網址
            user_info = threads_api.get_user_bio()
            username = user_info.get("username", "")
            thread_id = result["id"]
            
            post_url = f"https://www.threads.net/@{username}/post/{thread_id}"
            
            return (f"發送成功！貼文網址: {post_url}",)
            
        except Exception as e:
            return (f"錯誤: {str(e)}",)

    def _process_image(self, image, base_url):
        """處理圖片並轉換為 URL"""
        try:
            # 將 tensor 轉換為 PIL Image
            if isinstance(image, torch.Tensor):
                if image.dim() == 4:
                    image = image.squeeze(0)  # 移除 batch 維度
                
                # 轉換為 numpy array
                image_np = image.cpu().numpy()
                
                # 確保數值在 0-255 範圍內
                if image_np.max() <= 1.0:
                    image_np = (image_np * 255).astype(np.uint8)
                else:
                    image_np = image_np.astype(np.uint8)
                
                # 轉換為 PIL Image
                pil_image = Image.fromarray(image_np)
            else:
                pil_image = image

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"thread_image_{timestamp}.png"
            
            # 保存到 output 目錄
            output_dir = get_output_directory()
            filepath = os.path.join(output_dir, filename)
            pil_image.save(filepath)
            
            print(f"圖片已保存: {filepath}")
            
            # 生成 URL
            url = f"{base_url}/api/view?filename={filename}"
            print(f"生成圖片 URL: {url}")
            return url
            
        except Exception as e:
            print(f"圖片處理錯誤: {str(e)}")
            return None


# 註冊節點
NODE_CLASS_MAPPINGS = {
    "StartWithLongLiveToken": StartWithLongLiveToken,
    "PublishThread": PublishThread,
    "ThreadsHistory": ThreadsHistory,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StartWithLongLiveToken": "Start With Long Live Token",
    "PublishThread": "Publish Thread",
    "ThreadsHistory": "Threads History",
}