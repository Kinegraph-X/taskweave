import re
import uuid
from urllib.parse import urlparse, parse_qs

TWITCH_HOSTS = re.compile(r"ttvnw\.net|twitch\.tv")

def extract_channel_info(url: str) -> tuple[str, str]:
    """Returns (channel_name, vod_uid)"""
    
    # Twitch VOD — Amazon CDN
    # ex: /a1b2c3d4_channel_name_123456_1080p/
    parsed = urlparse(url)
    
    # Twitch — known hostname OR pattern on path Amazon CDN Twitch
    m = re.search(r"/[a-f0-9]+_(.+?)_(\d+)_\d+/", url)
    if m and (TWITCH_HOSTS.search(url) or "cloudfront.net" in str(parsed.hostname)):
        return m.group(1), m.group(2)
    
    # fallback if path match but unknown hostname : try anyway
    if m:
        return m.group(1), m.group(2)
    
    # YouTube — googlevideo.com
    # id=o-XXXX in query params
    if "googlevideo.com" in url:
        params = parse_qs(urlparse(url).query)
        vid_id = params.get("id", [None])[0]
        if vid_id:
            return "youtube", vid_id.replace("o-", "")[:12]
    
    # Dailymotion — cdn.dailymotion.com/video/XXXXXXX
    m = re.search(r"dailymotion\.com/(?:video/)?([a-z0-9]+)", url, re.IGNORECASE)
    if m:
        return "dailymotion", m.group(1)

    # Twitter/X — video.twimg.com/ext_tw_video/VIDEOID/
    m = re.search(r"twimg\.com/(?:ext_tw_video|amplify_video)/(\d+)", url)
    if m:
        return "twitter", m.group(1)

    # Instagram — /v/ ou /video/ dans les CDN Meta
    m = re.search(r"cdninstagram\.com.+?/(\d{15,})/", url)
    if m:
        return "instagram", m.group(1)

    # TikTok — v19.tiktok.com ou similar, video_id dans le path
    m = re.search(r"tiktok\.com.+?/video/(\d+)", url)
    if m:
        return "tiktok", m.group(1)

    # Fallback — slug from hostname + random short uid 
    hostname = urlparse(url).hostname or "unknown"
    slug = hostname.split(".")[0]  # "rr3---sn-xxx" → "rr3---sn-xxx", only tld-2
    slug = re.sub(r"[^a-z0-9]", "_", slug.split(".")[-1] if "." in slug else slug)
    return slug, uuid.uuid4().hex[:8]