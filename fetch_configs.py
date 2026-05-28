import os
import re
import random
import requests
import base64
from urllib.parse import urlparse, urlunparse, quote, unquote

# لیست سابلینک‌های موجود در پوشه servers ریپازیتوری مقصد (بر اساس کامیت درخواستی شما)
# برای پایداری و عدم نیاز به بررسی تک‌تک فایل‌ها، مستقیماً از فایل‌های تجمیعی یا تکست اصلی استفاده می‌شود.
# اما جهت اطمینان، منابع اصلی از پوشه servers کامیت ذکر شده به صورت مستقیم تعریف شده‌اند.
SUBLINKS = [
    "https://raw.githubusercontent.com/MohammadBahemmat/V2ray-Collector/6422fd9880b1f346f94b6b46feaf7ede6eafe25b/servers/mix.txt",
    "https://raw.githubusercontent.com/MohammadBahemmat/V2ray-Collector/6422fd9880b1f346f94b6b46feaf7ede6eafe25b/servers/vmess.txt",
    "https://raw.githubusercontent.com/MohammadBahemmat/V2ray-Collector/6422fd9880b1f346f94b6b46feaf7ede6eafe25b/servers/vless.txt",
    "https://raw.githubusercontent.com/MohammadBahemmat/V2ray-Collector/6422fd9880b1f346f94b6b46feaf7ede6eafe25b/servers/trojan.txt",
    "https://raw.githubusercontent.com/MohammadBahemmat/V2ray-Collector/6422fd9880b1f346f94b6b46feaf7ede6eafe25b/servers/shadowsocks.txt",
]

NEW_REMARK = "☬SHΞN™🪽"

def decode_base64_content(content):
    """اگر محتوای سابلینک کلا Base64 بود آن را دیکود می‌کند"""
    try:
        # حذف فاصله‌ها و خطوط جدید احتمالی
        cleaned_content = content.strip().replace("\n", "").replace("\r", "")
        # پدینگ زدن به بیس۶۴ برای جلوگیری از ارور
        missing_padding = len(cleaned_content) % 4
        if missing_padding:
            cleaned_content += '=' * (4 - missing_padding)
        decoded = base64.b64decode(cleaned_content).decode('utf-8', errors='ignore')
        # بررسی اینکه آیا خروجی شبیه به کانفیگ هست یا خیر
        if any(p in decoded for p in ["vless://", "vmess://", "ss://", "trojan://"]):
            return decoded
    except Exception:
        pass
    return content

def change_remark(config_line):
    config_line = config_line.strip()
    if not config_line:
        return None
    
    protocols = ["vless://", "vmess://", "trojan://", "ss://", "shadowsocks://", "tuic://", "hysteria2://", "hy2://"]
    if not any(config_line.startswith(p) for p in protocols):
        return None

    # مدیریت کانفیگ‌های vmess که ساختار JSON Base64 دارند
    if config_line.startswith("vmess://"):
        try:
            b64_part = config_line.split("vmess://").strip()
            # تصحیح پدینگ بیس۶۴
            b64_part += "=" * ((4 - len(b64_part) % 4) % 4)
            import json
            decoded_json = json.loads(base64.b64decode(b64_part).decode('utf-8', errors='ignore'))
            # تغییر ریمارک (فیلد ps در ویمس)
            decoded_json['ps'] = NEW_REMARK
            new_b64 = base64.b64encode(json.dumps(decoded_json).encode('utf-8')).decode('utf-8')
            return f"vmess://{new_b64}"
        except Exception:
            # اگر فرمت JSON استاندارد نبود یا به عنوان بک‌آپ:
            if "#" in config_line:
                base_part = config_line.split("#")
                return f"{base_part}#{quote(NEW_REMARK)}"
            return f"{config_line}#{quote(NEW_REMARK)}"

    # مدیریت سایر پروتکل‌ها (VLESS, Trojan, Shadowsocks و...)
    if "#" in config_line:
        # جدا کردن بخش آدرس و بخش ریمارک قبلی
        parts = config_line.split("#")
        base_part = parts
        # قرار دادن ریمارک جدید به صورت URL Encoded (برای سازگاری کامل با کلاینت‌ها)
        return f"{base_part}#{quote(NEW_REMARK)}"
    else:
        return f"{config_line}#{quote(NEW_REMARK)}"

def main():
    all_configs = set()  # استفاده از set برای حذف کانفیگ‌های تکراری احتمالی
    
    print("Starting to fetch configurations...")
    for url in SUBLINKS:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                content = response.text
                # بررسی اینکه آیا کل فایل بیس۶۴ است یا خیر
                decoded_content = decode_base64_content(content)
                
                # تفکیک خط به خط
                lines = decoded_content.splitlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        modified = change_remark(line)
                        if modified:
                            all_configs.add(modified)
                print(f"Successfully fetched and processed: {url}")
            else:
                print(f"Failed to fetch {url} - Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    # تبدیل به لیست جهت شافل و میکس کردن
    config_list = list(all_configs)
    random.shuffle(config_list)
    
    # ذخیره در فایل sub.txt
    output_filename = "sub.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        for config in config_list:
            f.write(config + "\n")
            
    print(f"Done! Saved {len(config_list)} unique mixed configurations to {output_filename}")

if __name__ == "__main__":
    main()
