# -*- coding: utf-8 -*-
import gradio as gr
import json
import requests
import re
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
import os
import logging
import ssl
import xmlrpc.client
from bs4 import BeautifulSoup

# 全局禁用SSL验证
ssl._create_default_https_context = ssl._create_unverified_context

# Constants
PROMPTS_FILE = os.path.join(os.getcwd(), "prompts.json")
SETTINGS_DIR = os.path.join(os.getcwd(), "settings")
if not os.path.exists(SETTINGS_DIR):
    os.makedirs(SETTINGS_DIR)
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
API_URLS = {
    "按token计费": "https://zmgpt.cc/v1/chat/completions",
    "按次数计费": "https://ai.zmgpt.cc/v1/chat/completions"
}

# Setup logging
log_file_path = os.path.join(os.getcwd(), "logs/app.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    filename=log_file_path,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def save_prompt(name, prompt):
    try:
        with open(PROMPTS_FILE, 'r') as file:
            prompts = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        prompts = {}

    prompts[name] = prompt
    with open(PROMPTS_FILE, 'w') as file:
        json.dump(prompts, file)

def delete_prompt(name):
    try:
        with open(PROMPTS_FILE, 'r') as file:
            prompts = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        prompts = {}

    if name in prompts:
        del prompts[name]
    with open(PROMPTS_FILE, 'w') as file:
        json.dump(prompts, file)

def load_prompts():
    try:
        with open(PROMPTS_FILE, 'r') as file:
            prompts = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        prompts = {}
    return prompts

def save_settings(user_id, settings):
    if not user_id:
        return "保存失败：用户名是必需的。"
    with open(os.path.join(SETTINGS_DIR, f"{user_id}_settings.json"), 'w') as file:
        json.dump(settings, file)
    return "设置已保存！"

def load_settings(user_id):
    if not user_id:
        return {}
    try:
        with open(os.path.join(SETTINGS_DIR, f"{user_id}_settings.json"), 'r') as file:
            settings = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        settings = {}
    return settings

def generate_content(input_text, prompt="", model="gpt-3.5-turbo", api_url="https://zmgpt.cc/v1/chat/completions", api_key=""):
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': model,
            'messages': [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f'{prompt}\n\n{input_text}'}
            ],
            'max_tokens': 1000,
        }
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error generating content: {e}")
        return "Error generating content", "", ""

    if response.status_code == 200 and 'choices' in response.json():
        content = response.json()['choices'][0]['message']['content']
        title_prompt = "根据全文进行总结，提取一个标题。"
        try:
            title_response = requests.post(api_url, headers=headers, json={
                'model': model,
                'messages': [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f'{title_prompt}\n\n{content}'}
                ],
                'max_tokens': 50,
            })
            title_response.raise_for_status()
            title = title_response.json()['choices'][0]['message']['content'].replace('"', '')
        except requests.exceptions.RequestException as e:
            logging.error(f"Error generating title: {e}")
            title = "Error generating title"

        tags = extract_tags(content)
        return title, content, ','.join(tags)
    else:
        return "Error generating content", "", ""

def extract_tags(content):
    words = re.findall(r'\b\w+\b', content)
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    sorted_words = sorted(word_freq.items(), key=lambda item: item[1], reverse=True)
    
    # 提取最多三个标签，每个标签长度不超过五个字
    tags = [word for word, freq in sorted_words if len(word) <= 5][:3]
    return tags

def publish_to_wordpress(title, content, category, tags, wp_url, wp_username, wp_password):
    if not title:
        return {'status': 'error', 'message': '标题是必需的'}
    if not content:
        return {'status': 'error', 'message': '内容是必需的'}

    wp_url = wp_url.strip().rstrip('/') + '/xmlrpc.php'
    client = Client(wp_url, wp_username, wp_password)

    post = WordPressPost()
    post.title = title
    post.content = content
    post.post_status = 'publish'
    post.terms_names = {
        'category': [category],
        'post_tag': tags.split(',')
    }

    try:
        post_id = client.call(NewPost(post))
        return {'status': 'success', 'post_id': post_id}
    except Exception as e:
        logging.error(f"Error publishing to WordPress: {e}")
        return {'status': 'error', 'message': str(e)}

def regenerate_title(content, model, api_url, api_key):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': model,
        'messages': [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f'根据全文进行总结，提取一个标题。\n\n{content}'}
        ],
        'max_tokens': 50,
    }
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        title = response.json()['choices'][0]['message']['content'].replace('"', '')
        return title
    except requests.exceptions.RequestException as e:
        logging.error(f"Error regenerating title: {e}")
        return "Error regenerating title"

def extract_content_from_wechat_article(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find('div', {'id': 'js_content'})
        if content:
            return content.get_text(strip=True)
        else:
            return "Error: 无法提取内容"
    except requests.exceptions.RequestException as e:
        logging.error(f"Error extracting WeChat article content: {e}")
        return "Error: 无法提取内容"

def main():
    saved_prompts = load_prompts()

    with gr.Blocks() as demo:
        user_id = gr.Textbox(label="用户名", placeholder="请输入用户名")

        with gr.Tab("设置"):
            with gr.Column():
                api_key = gr.Textbox(label="OpenAI API 密钥", placeholder="sk-...", type="password")
                api_url = gr.Dropdown(choices=list(API_URLS.keys()), label="API 计费方式", value="按token计费")
                wordpress_url = gr.Textbox(label="WordPress URL", placeholder="例如：www.example.com")
                wordpress_username = gr.Textbox(label="WordPress 用户名")
                wordpress_password = gr.Textbox(label="WordPress 密码", type="password")
                category = gr.Textbox(label="WordPress 分类", placeholder="分类名称")
                model_dropdown = gr.Dropdown(choices=["gpt-3.5-turbo", "gpt-4", "gpt-4o-all", "deepseek-chat", "custom"], label="选择模型")
                custom_model = gr.Textbox(label="自定义模型", placeholder="输入自定义模型名称")
                with gr.Accordion("高级自定义", open=False):
                    new_prompt_name = gr.Textbox(label="提示词名称", placeholder="输入提示词名称", lines=1)
                    new_prompt = gr.Textbox(label="添加新提示词", placeholder="输入新提示词", lines=2)
                    save_prompt_button = gr.Button("保存提示词")
                    delete_prompt_button = gr.Button("删除选择的提示词")
                save_settings_button = gr.Button("保存设置")
                save_status = gr.HTML()

        with gr.Tab("生成内容"):
            input_text = gr.Textbox(label="输入灵感或新闻", placeholder="输入几句话或一个标题", lines=10, elem_id="input-text")
            wechat_url = gr.Textbox(label="输入公众号链接", placeholder="输入公众号文章链接", lines=1)
            prompt_dropdown = gr.Dropdown(choices=list(saved_prompts.keys()), label="选择提示词", interactive=True)
            generate_button = gr.Button("生成内容")
            output_title = gr.Textbox(label="生成的标题")
            regenerate_title_button = gr.Button("重新生成标题")
            output_content = gr.Textbox(label="生成的内容", lines=20)
            tags = gr.Textbox(label="输入标签，用逗号分隔", placeholder="标签1,标签2")
            publish_button = gr.Button("发布到WordPress")
            result = gr.Textbox(label="发布结果")

        purchase_api_html = gr.HTML("<a href='https://faka.zmgpt.cc' target='_blank'>购买API密钥</a>")

        def on_save_prompt(new_prompt_name, new_prompt):
            if not new_prompt_name or not new_prompt:
                return gr.update(choices=list(saved_prompts.keys()), value=""), gr.update(value=""), gr.update(value="")
            save_prompt(new_prompt_name, new_prompt)
            saved_prompts.update({new_prompt_name: new_prompt})
            return gr.update(choices=list(saved_prompts.keys()), value=""), gr.update(value=""), gr.update(value="")

        def on_delete_prompt(prompt_dropdown):
            delete_prompt(prompt_dropdown)
            saved_prompts.pop(prompt_dropdown, None)
            return gr.update(choices=list(saved_prompts.keys()), value=""), gr.update(value=""), gr.update(value="")

        def on_save_settings(user_id, api_key, api_url, wordpress_url, wordpress_username, wordpress_password, category, model_dropdown, custom_model, new_prompt_name, new_prompt, prompt_dropdown):
            if not user_id or not api_key or not wordpress_url or not wordpress_username or not wordpress_password or not category or not model_dropdown:
                return gr.update(value="保存失败：所有字段都是必需的。")
            model = custom_model if model_dropdown == "custom" else model_dropdown
            settings = {
                "api_key": api_key,
                "api_url": API_URLS.get(api_url, API_URLS["按token计费"]),
                "wordpress_url": wordpress_url,
                "wordpress_username": wordpress_username,
                "wordpress_password": wordpress_password,
                "category": category,
                "model": model
            }
            if new_prompt_name and new_prompt:
                save_prompt(new_prompt_name, new_prompt)
                saved_prompts.update({new_prompt_name: new_prompt})
            message = save_settings(user_id, settings)
            return gr.update(value=message), gr.update(choices=list(saved_prompts.keys()), value=""), gr.update(value=""), gr.update(value="")

        def on_generate(input_text, wechat_url, prompt_dropdown, user_id):
            settings = load_settings(user_id)
            if not settings:
                return "Error: 设置未配置", "", ""
            model = settings.get("model", "gpt-3.5-turbo")
            api_url = settings.get("api_url", API_URLS["按token计费"])
            api_key = settings.get("api_key", "")
            if not api_key:
                return "Error: OpenAI API 密钥未配置", "", ""
            if wechat_url:
                input_text = extract_content_from_wechat_article(wechat_url)
            return generate_content(input_text, prompt_dropdown, model, api_url, api_key)

        def on_publish_to_wordpress(title, content, tags, user_id):
            settings = load_settings(user_id)
            wp_url = settings.get("wordpress_url", "")
            wp_username = settings.get("wordpress_username", "")
            wp_password = settings.get("wordpress_password", "")
            category = settings.get("category", "")
            if not wp_url or not wp_username or not wp_password or not category:
                return "Error: WordPress 配置未完成"
            response = publish_to_wordpress(title, content, category, tags, wp_url, wp_username, wp_password)
            if response['status'] == 'success':
                return f"发布成功，文章ID: {response['post_id']}"
            else:
                return f"发布失败: {response['message']}"

        def on_regenerate_title(content, user_id):
            settings = load_settings(user_id)
            model = settings.get("model", "gpt-3.5-turbo")
            api_url = settings.get("api_url", API_URLS["按token计费"])
            api_key = settings.get("api_key", "")
            if not api_key:
                return "Error: OpenAI API 密钥未配置"
            return regenerate_title(content, model, api_url, api_key)

        def on_user_id_change(user_id):
            settings = load_settings(user_id)
            if settings:
                return (settings.get("api_key", ""), settings.get("api_url", "按token计费"), settings.get("wordpress_url", ""),
                        settings.get("wordpress_username", ""), settings.get("wordpress_password", ""), settings.get("category", ""),
                        settings.get("model", "gpt-3.5-turbo"), settings.get("custom_model", ""))
            return "", "按token计费", "", "", "", "", "gpt-3.5-turbo", ""

        user_id.change(on_user_id_change, inputs=user_id, outputs=[api_key, api_url, wordpress_url, wordpress_username, wordpress_password, category, model_dropdown, custom_model])
        save_prompt_button.click(on_save_prompt, inputs=[new_prompt_name, new_prompt], outputs=[prompt_dropdown, new_prompt_name, new_prompt])
        delete_prompt_button.click(on_delete_prompt, inputs=[prompt_dropdown], outputs=[prompt_dropdown, new_prompt_name, new_prompt])
        save_settings_button.click(on_save_settings, inputs=[user_id, api_key, api_url, wordpress_url, wordpress_username, wordpress_password, category, model_dropdown, custom_model, new_prompt_name, new_prompt, prompt_dropdown], outputs=[save_status, prompt_dropdown, new_prompt_name, new_prompt])
        generate_button.click(on_generate, inputs=[input_text, wechat_url, prompt_dropdown, user_id], outputs=[output_title, output_content, tags])
        publish_button.click(on_publish_to_wordpress, inputs=[output_title, output_content, tags, user_id], outputs=[result])
        regenerate_title_button.click(on_regenerate_title, inputs=[output_content, user_id], outputs=[output_title])

    demo.launch(server_name="0.0.0.0", server_port=7861, debug=True)

if __name__ == "__main__":
    main()
