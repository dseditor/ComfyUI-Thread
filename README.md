# ComfyUI-Thread

A ComfyUI custom node package for seamless integration with Threads (Meta's social platform). This package allows you to publish posts, manage images, and retrieve post history directly from your ComfyUI workflows.

ComfyUI 的 Threads 整合自定義節點包，讓您能夠直接在 ComfyUI 工作流程中發布貼文、管理圖片和獲取發文歷史。
本說明由Claude產生，老實講他寫得真好，我只要補充就好了。

## Features | 功能特色

### 🚀 **Post Publishing | 發文功能**
- ✅ Text-only posts | 純文字發文
- ✅ Single image posts | 單圖發文
- ✅ Multi-image carousel posts | 多圖輪播發文
- ✅ Image tensor support (from ComfyUI generators) | 支援圖片張量（來自 ComfyUI 生成器）
- ✅ External image URL support | 支援外部圖片網址

### 📊 **Analytics | 數據分析**
- ✅ Retrieve post history | 獲取發文歷史
- ✅ Customizable date range (1-365 days) | 可自訂日期範圍（1-365天）
- ✅ Formatted post content output | 格式化的貼文內容輸出

### ⚙️ **Configuration | 配置管理**
- ✅ Long-lived access token management | 長期訪問令牌管理
- ✅ Custom ComfyUI URL support | 支援自訂 ComfyUI 網址
- ✅ Automatic configuration persistence | 自動配置持久化

## Installation | 安裝方式

1. Navigate to your ComfyUI custom nodes directory:
   ```bash
   cd ComfyUI/custom_nodes/
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/dseditor/ComfyUI-Thread.git
   ```

3. Restart ComfyUI | 重啟 ComfyUI

## ExampleWorkflow | 範例工作流

範例工作流使用了ollama-gemini節點來產生圖文提示內容，此節點需自行配置API金鑰才能使用Gemini。  
https://github.com/al-swaiti/ComfyUI-OllamaGemini  
有關於圖像生成模型的部分，可以修改為你自己常用的模型與節點。  

## Setup | 設置

### 1. Get Threads API Credentials | 獲取 Threads API 憑證

You need to obtain the following from Meta Developers:
您需要從 Meta 開發者平台獲取以下資訊：

- `USER_ID` - Your Threads user ID | 您的 Threads 用戶 ID
- `ACCESS_TOKEN` - Short-lived access token | 短期訪問令牌
- `APP_SECRET` - Your app secret | 您的應用密鑰

有關他們的取得方式，可以參考SDK的開發者網址，同時你也必須安裝**requirement.txt**中的SDK：  
https://nijialin.com/2024/08/17/python-threads-sdk-introduction/  

### 2. Configure API Access | 配置 API 訪問

Use the **Start With Long Live Token** node with your credentials to generate a long-lived access token.

搜尋並使用 **Start With Long Live Token** 節點輸入您的憑證來生成長期訪問令牌。

## Nodes | 節點說明

### 📝 **Start With Long Live Token**
Initialize the Threads API connection and generate a long-lived access token.

初始化 Threads API 連接並生成長期訪問令牌。

**Inputs | 輸入:**
- `USER_ID` - Your Threads user ID | 您的 Threads 用戶 ID
- `ACCESS_TOKEN` - Short-lived access token | 短期訪問令牌
- `APP_SECRET` - Your app secret | 您的應用密鑰

**Outputs | 輸出:**
- `result` - Configuration status message | 配置狀態訊息，成功後會產生一個token.json檔案在token資料夾下。

### 📤 **Publish Thread**
Publish posts to Threads with text and images.

發布包含文字和圖片的 Threads 貼文。

**Inputs | 輸入:**
- `text` - Post content (required) | 貼文內容（必填）
- `ComfyUIHttpsURL` - Custom ComfyUI base URL (optional) | 自訂 ComfyUI 基礎網址（選填），此網址必須使用ngrok等建立https對外的網址，填入一次之後不用再次填寫，網址會記憶在url.json檔案中，如果網址變更才需要再填寫，沒有填過它就會預設為127.0.0.1，image接點會無法傳圖只能使用網址。
- `image` - Image tensor input (optional) | 圖片張量輸入（選填），一定要有https設定過才會生效。
- `image_url` - External image URLs, one per line (optional) | 外部圖片網址，每行一個（選填)，可填入多行網址成為容器，狀態可以看到收集多少圖片網址。

**Outputs | 輸出:**
- `result` - Post status and URL | 發文狀態和網址，失敗會傳出API錯誤訊息。

### 📈 **Threads History**
Retrieve your post history from Threads.

從 Threads 獲取您的發文歷史。

**Inputs | 輸入:**
- `backfill_days` - Number of days to look back (1-365) | 回溯天數（1-365）

**Outputs | 輸出:**
- `history_content` - Formatted post history | 格式化的發文歷史

## Usage Examples | 使用範例

### Simple Text Post | 簡單文字發文
1. Connect **Start With Long Live Token** → Configure your API credentials | 必須先以API的token開始
2. Connect **Publish Thread** → Enter your text content | 打入文字，按下Queue就會發文
3. Execute to post

### Image Post with Generated Content | 使用生成內容的圖片發文
1. Create images using ComfyUI generators (Stable Diffusion, etc.) | 直接接入圖片節點，或使用LoadImage，注意不支援ImageList/ImageBatch，會被視為多張圖
2. Connect image output to **Publish Thread** `image` input
3. Add your text content
4. Execute to post with generated images | 可組合圖片與文案至Thread

### Multi-Image Carousel | 多圖輪播
1. In **Publish Thread**, enter multiple image URLs in `image_url` field (one per line) | 貼入多行HTTPS網址
2. Add your text content
3. Execute to create a carousel post

### Analyze Post History | 分析歷史貼文
1. Use **Threads History** to retrieve recent posts
2. Set `backfill_days` to desired time range
3. Review formatted output for content analysis

## File Structure | 檔案結構

```
ComfyUI-Thread/
├── __init__.py          # Module initialization | 模組初始化
├── nodes.py             # Main node implementations | 主要節點
└── token/               # Auto-generated config directory | 自動生成的配置目錄
    ├── thread_config.json   # API credentials | API 憑證
    └── url.json            # ComfyUI URL configuration | ComfyUI 網址配置
```

## Requirements | 系統需求

- ComfyUI
- Python 3.8+
- PIL (Pillow)
- numpy
- torch
- requests
- threads_sdk

## API Limitations | API 限制

- **Scope**: Only works with your own Threads account | 僅適用於您自己的 Threads 帳號
- **Rate Limits**: Subject to Meta's API rate limits | 受 Meta API 速率限制約束
- **Video Support**: Currently limited due to Threads' strict video requirements | 目前沒有支援影片上傳，因 Threads 對視頻格式要求嚴格

## Troubleshooting | 疑難排解

### Common Issues | 常見問題

**"Please execute StartWithLongLiveToken node first(無法發送)"**
- Make sure you've run the token configuration node before posting
- 確保在發文前已執行令牌配置節點

**"Param image_url is not a valid URL"**
- Check that your image URLs are complete and accessible
- Ensure URLs start with `https://`
- 檢查圖片網址是否完整且可存取，如果使用Image，ComfyUI必須有可認證的HTTPS對外

**Image not displaying in posts(發送成功圖片無法顯示，只有文字)**
- Verify your ComfyUI URL is accessible from the internet
- Check the `ComfyUIHttpsURL` configuration
- 確認您的 ComfyUI 網址可從網際網路存取
- 檢查 `ComfyUIHttpsURL` 配置

## License | 授權

MIT License

## Support | 支援

If you encounter any issues or have questions, please open an issue on GitHub.

如果您遇到任何問題或有疑問，請在 GitHub 上開啟 issue。

---

**Note**: This project is not officially affiliated with Meta or Threads. Use responsibly and in accordance with Threads' Terms of Service.

**注意**：此專案與 Meta 或 Threads 無官方關聯。請負責任地使用並遵守 Threads 的服務條款。
