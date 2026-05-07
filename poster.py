import requests
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# НАСТРОЙКИ (Вставьте ваши данные сюда)
# ==========================================
OPENROUTER_API_KEY = "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"  # Ваш ключ от OpenRouter
VK_ACCESS_TOKEN  = "vk1.a.Gu98GXj0R8PRgOkBamtH63MeHxTv1iNAlLZk0DgjRbbgtmy-ByNRSJVXXqqEvOJrIjDAUviR6yxchmwdt-0KjFjC_SD5lQw8v38vKkAZUdkTJ0xiV4x9qHIyUo1povqHHrn6ioH5_rVhC8z-FLRw7D5B7yRN1MDdeG4lSneVl8Cz088rRjWjgfqzqw6mgNvLnZjj-1F2poXEg8_h5Ni1pw"        # Токен с правом wall (стена)
VK_GROUP_ID      = "235499550"       # ID вашей группы (только цифры)
# ==========================================

def generate_post(topic):
    """Генерирует текст поста через OpenRouter API."""
    print(f"🤖 Генерация поста на тему: '{topic}'...")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/parfenyuch-cpu",
        "X-Title": "VK AutoPoster",
        "Content-Type": "application/json"
    }
    
    prompt = (
        f"Напиши профессиональный, но понятный пост для соцсетей на тему: {topic}. "
        f"Используй эмодзи и в конце добавь призыв заказать консультацию."
    )
    
    payload = {
        "model": "openai/gpt-oss-20b:free",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        content = result.get('choices', [{}])[0].get('message', {}).get('content')
        if content:
            return content.strip()
        else:
            print("❌ Ошибка: Нейросеть вернула пустой ответ.")
            print(result)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения с OpenRouter: {e}")
        return None

def publish_to_vk(text):
    """Публикует текст на стене группы ВКонтакте."""
    print("📤 Публикация во ВКонтакте...")
    
    url = "https://api.vk.com/method/wall.post"
    
    params = {
        "access_token": VK_ACCESS_TOKEN,
        "owner_id": f"-{VK_GROUP_ID}",
        "message": text,
        "v": "5.199"
    }
    
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if 'response' in result and 'post_id' in result['response']:
            post_id = result['response']['post_id']
            print(f"✅ Успешно! Пост опубликован. ID: {post_id}")
            return True
        else:
            print(f"❌ Ошибка VK API: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения с VK API: {e}")
        return False

if __name__ == "__main__":
    if not OPENROUTER_API_KEY or not VK_ACCESS_TOKEN or not VK_GROUP_ID:
        print("⚠️ ОШИБКА: Пожалуйста, заполните переменные API ключей и ID группы в начале скрипта.")
        sys.exit(1)

    print("=== VK AutoPoster (Neuro Edition) ===")
    
    # Поддержка ввода из аргументов командной строки или интерактивного ввода
    if len(sys.argv) > 1:
        user_topic = " ".join(sys.argv[1:])
        print(f"📝 Тема: {user_topic}")
    else:
        try:
            user_topic = input("📝 Введите тему поста: ").strip()
        except EOFError:
            print("❌ Тема не указана. Используйте: python poster.py \"Ваша тема\"")
            sys.exit(1)
    
    post_text = generate_post(user_topic)
    
    if post_text:
        publish_to_vk(post_text)
    else:
        print("💾 Публикация отменена, так как текст не был сгенерирован.")
