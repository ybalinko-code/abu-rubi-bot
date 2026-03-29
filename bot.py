def scrape_telegram_channels():
    """סורק את נבחרת הברזל, מנקה ג'יבריש ומתרגם שפות זרות"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for channel in CHANNELS:
        try:
            url = f"https://t.me/s/{channel}"
            res = requests.get(url, headers=headers, timeout=10)
            # חילוץ הודעות מה-HTML של טלגרם
            msgs = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', res.text)
            
            for msg_html in msgs[-2:]: # סורק רק את ה-2 האחרונות למניעת עומס
                # 1. ניקוי ראשוני של HTML וג'יבריש
                raw_text = re.sub(r'<[^>]+>', ' ', msg_html).strip()
                clean_text = html.unescape(raw_text)
                
                # 2. מניעת כפילויות לפי תוכן (Hash)
                msg_hash = hashlib.md5(clean_text.encode('utf-8')).hexdigest()
                if msg_hash not in processed_hashes:
                    processed_hashes.add(msg_hash)
                    
                    # 3. זיהוי צורך בתרגום (אם יש אנגלית/ערבית משמעותית)
                    if any(c.isalpha() for c in clean_text if ord(c) < 128) and channel == 'Intellinews':
                        try:
                            trans_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=iw&dt=t&q={clean_text}"
                            trans_res = requests.get(trans_url, timeout=5).json()
                            translated_parts = [part[0] for part in trans_res[0] if part[0]]
                            clean_text = "".join(translated_parts)
                            clean_text = f"[מתורגם] {clean_text}"
                        except:
                            pass

                    # 4. בדיקת מילות מפתח לשליחה
                    is_critical = any(kw in clean_text for kw in CRITICAL_KEYWORDS)
                    is_general = any(kw in clean_text for kw in GENERAL_KEYWORDS)
                    
                    if is_critical or is_general:
                        send_telegram_alert(channel, clean_text, is_critical)
                        
        except Exception as e:
            print(f"Scrape Error for {channel}: {e}")
        time.sleep(1)
