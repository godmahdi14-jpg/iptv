#!/usr/bin/env python3
"""
این اسکریپت آخرین نسخه‌ی پلی‌لیست کامل iptv-org رو دانلود می‌کنه،
و فقط کانال‌هایی که tvg-id شون توی channels.txt هست رو نگه می‌داره.
خروجی: playlist.m3u (لینک‌های همیشه تازه، فقط کانال‌های خودتون)

نکته: چون هر کانال ممکنه چند لینک استریم (چند منبع) داشته باشه،
اسکریپت همه‌ی لینک‌های موجود برای هر tvg-id رو نگه می‌داره
(همون رفتار فایل اصلی خودتون که چند لینک برای بعضی کانال‌ها داشت).
"""

import re
import sys
import urllib.request

SOURCE_URL = "https://iptv-org.github.io/iptv/index.m3u"
CHANNELS_FILE = "channels.txt"
OUTPUT_FILE = "playlist.m3u"


def load_wanted_ids(path):
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def fetch_source_playlist(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def filter_playlist(m3u_text, wanted_ids):
    lines = m3u_text.splitlines()
    output_lines = ["#EXTM3U"]
    found_ids = set()

    i = 0
    # skip the #EXTM3U header line if present
    if lines and lines[0].strip().startswith("#EXTM3U"):
        i = 1

    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF"):
            # collect this entry's extra tag lines (e.g. #EXTVLCOPT) + the url line
            entry_lines = [line]
            i += 1
            while i < len(lines) and lines[i].startswith("#"):
                entry_lines.append(lines[i])
                i += 1
            if i < len(lines):
                entry_lines.append(lines[i])  # the stream URL line
                i += 1

            m = re.search(r'tvg-id="([^"]*)"', line)
            tvg_id = m.group(1) if m else ""

            if tvg_id in wanted_ids:
                output_lines.extend(entry_lines)
                found_ids.add(tvg_id)
        else:
            i += 1

    missing = wanted_ids - found_ids
    return "\n".join(output_lines) + "\n", found_ids, missing


def main():
    wanted_ids = load_wanted_ids(CHANNELS_FILE)
    print(f"[i] {len(wanted_ids)} کانال در channels.txt پیدا شد.")

    try:
        source_text = fetch_source_playlist(SOURCE_URL)
    except Exception as e:
        print(f"[!] خطا در دانلود پلی‌لیست منبع: {e}", file=sys.stderr)
        sys.exit(1)

    filtered_text, found_ids, missing = filter_playlist(source_text, wanted_ids)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(filtered_text)

    print(f"[✓] {len(found_ids)} کانال با موفقیت فیلتر و ذخیره شد -> {OUTPUT_FILE}")
    if missing:
        print(f"[!] {len(missing)} کانال توی منبع iptv-org پیدا نشد (شاید حذف شده یا tvg-id عوض شده):")
        for mid in sorted(missing):
            print(f"    - {mid}")


if __name__ == "__main__":
    main()
