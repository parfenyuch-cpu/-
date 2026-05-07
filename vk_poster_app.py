import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="VK AutoPoster", page_icon="📝", layout="centered")

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "vk_settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_settings(or_key, vk_token, vk_gid, model, is_paid):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "openrouter_api_key": or_key, 
            "vk_access_token": vk_token, 
            "vk_group_id": vk_gid, 
            "selected_model": model,
            "is_paid": is_paid
        }, f, ensure_ascii=False)

def delete_settings():
    if os.path.exists(SETTINGS_FILE):
        os.remove(SETTINGS_FILE)

def generate_post(topic, api_key, model_name):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/parfenyuch-cpu",
        "X-Title": "VK AutoPoster"
    }
    
    prompt = f"Напиши текст поста для ВКонтакте на тему: {topic}. Используй эмодзи. В конце добавь призыв заказать консультацию."
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        # Если API вернул ошибку
        if 'error' in result:
            error_msg = result['error'].get('message', 'Unknown error')
            # Если это ошибка про image.png, возвращаем понятное сообщение
            if "image" in error_msg.lower() and "support" in error_msg.lower():
                return False, f"❌ Ошибка: Модель '{model_name}' требует картинку или сломана. **Выберите другую модель!**"
            return False, f"❌ Ошибка API: {error_msg}"
            
        content = result.get('choices', [{}])[0].get('message', {}).get('content')
        
        if not content:
            return False, "❌ Нейросеть вернула пустой ответ."
            
        if "image.png" in content.lower() or "image input" in content.lower():
            return False, f"❌ Модель '{model_name}' вернула ошибку формата. **Выберите другую модель!**"
            
        return True, content.strip()
    except requests.exceptions.HTTPError as e:
        return False, f"❌ Ошибка HTTP: {response.status_code}. {response.text[:200]}"
    except Exception as e:
        return False, f"❌ Ошибка соединения: {str(e)}"

def publish_to_vk(text, vk_token, vk_group_id):
    url = "https://api.vk.com/method/wall.post"
    params = {
        "access_token": vk_token,
        "owner_id": f"-{vk_group_id}",
        "from_group": 1,
        "message": text,
        "v": "5.199"
    }
    
    try:
        response = requests.post(url, data=params, timeout=10)
        result = response.json()
        
        if 'response' in result and 'post_id' in result['response']:
            return {"success": True, "post_id": result['response']['post_id']}
        else:
            return {"success": False, "error": result}
    except Exception as e:
        return {"success": False, "error": {"exception": str(e)}}

# --- Загрузка настроек ---
settings = load_settings()

if "publish_status" not in st.session_state:
    st.session_state.publish_status = None
if "post_text" not in st.session_state:
    st.session_state.post_text = None

st.title("📝 VK AutoPoster")
st.caption("Генерация и публикация постов во ВКонтакте")

with st.sidebar:
    st.header("⚙️ Настройки")
    openrouter_api_key = st.text_input("OpenRouter API Key", value=settings.get("openrouter_api_key", ""), type="password")
    vk_access_token = st.text_input("VK Access Token", value=settings.get("vk_access_token", ""), type="password")
    vk_group_id = st.text_input("VK Group ID", value=settings.get("vk_group_id", ""))
    
    is_paid = st.checkbox("💎 Платная модель (стабильнее)", value=settings.get("is_paid", False))
    
    # Модели
    if is_paid:
        models = [
            ("google/gemini-flash-1.5", "Gemini 1.5 Flash"),
            ("openai/gpt-4o-mini", "GPT-4o Mini")
        ]
    else:
        models = [
            ("openai/gpt-oss-20b:free", "GPT-OSS 20B (Рекомендуется)"), 
            ("meta-llama/llama-3.1-8b-instruct:free", "Llama 3.1 8B"), 
            ("mistralai/mistral-7b-instruct:free", "Mistral 7B")
        ]
        
    default_model = settings.get("selected_model", "openai/gpt-oss-20b:free")
    model_options = [m[0] for m in models]
    model_labels = [m[1] for m in models]
    
    # Если сохраненной модели нет в текущем списке (из-за переключения платной/бесплатной), сбрасываем на первую
    if default_model not in model_options:
        default_model = model_options[0]
        
    selected_model_idx = model_options.index(default_model)
    selected_model_label = st.selectbox("Модель:", model_labels, index=selected_model_idx)
    selected_model_id = models[selected_model_idx][0]
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Сохранить", type="primary"):
            if openrouter_api_key and vk_access_token and vk_group_id:
                save_settings(openrouter_api_key, vk_access_token, vk_group_id, selected_model_id, is_paid)
                st.success("✅ Сохранено!")
            else:
                st.warning("⚠️ Заполните все поля!")
    with col2:
        if st.button("🗑️ Сброс"):
            delete_settings()
            st.session_state.clear()
            st.rerun()

if not (openrouter_api_key and vk_access_token and vk_group_id):
    st.info("👈 Введите API ключи и ID группы в меню слева.")
    st.stop()

# --- Основная часть ---
st.markdown("---")
st.subheader("🎯 Тема поста")
predefined_topics = [
    "Устройство заездов на участок",
    "Дренаж и ливневые системы для дачи",
    "Укладка тротуарной плитки на участке",
    "Создание парковки из щебня",
    "Благоустройство территории частного дома",
    "Монтаж ливневой канализации",
    "Дорожки на участке из натурального камня",
    "Организация парковки на даче",
    "Отсыпка участка песком и гравием",
    "Подготовка участка к строительству"
]

topic_choice = st.radio("Выберите тему:", predefined_topics, index=0)
use_custom = st.checkbox("✏️ Ввести свою тему")

if use_custom:
    user_topic = st.text_input("Ваша тема:", placeholder="Например: Укрепление береговой линии")
    topic = user_topic if user_topic else topic_choice
else:
    topic = topic_choice

with st.form(key="post_form"):
    col1, col2 = st.columns([2, 1])
    with col1:
        gen_submitted = st.form_submit_button("🤖 Сгенерировать пост", type="primary")
    with col2:
        pass

if gen_submitted:
    with st.spinner(f"🤖 Генерация ({selected_model_label})..."):
        success, result = generate_post(topic, openrouter_api_key, selected_model_id)
        st.session_state.post_text = result
        st.session_state.publish_status = None
        
        if success:
            st.success("✅ Пост сгенерирован!")
        else:
            st.error(result)
            if "image" in result.lower() and "support" in result.lower():
                st.error("💡 РЕШЕНИЕ: В меню слева выберите модель 'GPT-OSS 20B' или 'Gemini Flash' и нажмите 'Сохранить'.")

if st.session_state.post_text and not st.session_state.post_text.startswith("❌"):
    st.markdown("---")
    st.subheader("📄 Предпросмотр")
    st.text_area("Текст поста:", value=st.session_state.post_text, height=300)
    
    with st.form(key="publish_form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            pub_submitted = st.form_submit_button("📤 Опубликовать во ВКонтакте", type="primary")
        with col2:
            clear_submitted = st.form_submit_button("🗑️ Очистить")

    if clear_submitted:
        st.session_state.post_text = None
        st.session_state.publish_status = None
        st.rerun()

    if pub_submitted:
        try:
            with st.spinner("📤 Публикация..."):
                result = publish_to_vk(st.session_state.post_text, vk_access_token, vk_group_id)
                st.session_state.publish_status = result
        except Exception as e:
            st.session_state.publish_status = {"success": False, "error": {"exception": str(e)}}
        st.rerun()

if st.session_state.publish_status:
    status = st.session_state.publish_status
    if status.get("success"):
        st.success(f"✅ Опубликовано! ID: {status['post_id']}")
        st.info(f"🔗 https://vk.com/wall-{vk_group_id}_{status['post_id']}")
    else:
        st.error("❌ Ошибка публикации:")
        st.code(json.dumps(status.get("error", {}), indent=2, ensure_ascii=False))
