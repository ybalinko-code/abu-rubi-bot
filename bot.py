import html

# --- מילון שמות המקורות ---
SOURCE_MAPPING = {
    'Yair_Altman_channel14': 'יאיר אלטמן',
    'US2020US': 'עמיחי שטיין',
    'AlmogBoker': 'אלמוג בוקר',
    'yosiyehoshua': 'יוסי יהושוע',
    'HallelBittonRosen': 'הלל ביטון רוזן',
    'arielidan14': 'אריאל עידן',
    'noam_amir_news': 'נועם אמיר',
    'Intellinews': 'אינטליניוז'
}

def sanitize_and_format_text(text):
    """מנקה ג'יבריש, לינקים ומתקן ניסוחים לסטנדרט מקצועי"""
    # 1. ניקוי ג'יבריש
    clean = html.unescape(text)
    
    # 2. הסרת לינקים של טלגרם
    clean = re.sub(r'https?://t\.me/\S+', '', clean)
    
    # 3. החלת פילטרים שפתיים (החלפות טקסט נקיות)
    clean = clean.replace("פלסטינים", "מקומיים")
    clean = clean.replace("מצור", "כתר")
    clean = re.sub(r'\b(שניים|שלושה|ארבעה|חמישה)\s+(מתים|הרוגים)\b', 'הרוגים', clean)
    
    # 4. יצירת טקסט רציף (ללא רשימות)
    continuous_text = " ".join(clean.splitlines())
    return continuous_text.strip()

def send_telegram_alert(source_id, text, is_critical=False, is_disaster=False, event_time=None):
    """שליחת הדיווח בתבנית החדשות המחמירה"""
    # קביעת זמן האירוע (או זמן נוכחי כברירת מחדל)
    if not event_time:
        event_time = get_israel_time().strftime('%d/%m/%Y %H:%M')
        
    # תרגום שם המקור לעברית
    source_name = SOURCE_MAPPING.get(source_id, source_id)
    
    # ניקוי הטקסט
    clean_text = sanitize_and_format_text(text)
    
    # בניית הכותרת (6 מילים ראשונות)
    words = clean_text.split()
    headline = " ".join(words[:6]) + "..." if len(words) > 6 else clean_text
    
    icon = "🚨" if is_critical else "🌍" if is_disaster else "⚠️"
    
    # הפורמט הקפדני: Verified -> תאריך -> כותרת -> טקסט רציף (בלי Verified באמצע)
    msg = f"Verified\n{event_time}\n\n**{icon} {headline}**\n\nמקור: {source_name}\n{clean_text}"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": msg, 
        "parse_mode": "Markdown",
        "disable_notification": not is_critical
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Send Error: {e}")
