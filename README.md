# Gradio WordPress 内容生成器

该项目使用 Gradio 创建一个 Web 界面，允许用户使用 AI 生成和发布内容到 WordPress。用户可以直接输入文本或提供微信公众号文章链接以提取内容，然后使用 AI 提示词重写并发布到 WordPress 网站。
第一次设置好参数之后，下一次使用只需要输入自己的用户名，即可调用出参数，方便下次快速发布文章。
![image](https://github.com/user-attachments/assets/1e0404a9-7b31-443b-b262-b763ef403593)
![image](https://github.com/user-attachments/assets/dfc8fcd2-9905-4d1a-bbfb-4d5aece54aa0)


## 功能

- 输入文本或微信公众号文章链接以生成内容
- 使用 AI 提示词重写和增强内容
- 自动从内容中提取标签
- 将生成的内容发布到 WordPress

## 要求

- Python 3.7+
- 虚拟环境
- OpenAI API 密钥
- 启用 XML-RPC 的 WordPress 网站

## 安装

1. **克隆仓库**：
    ```sh
    git clone https://github.com/yourusername/gradio-wordpress-content-generator.git
    cd gradio-wordpress-content-generator
    ```

2. **创建并激活虚拟环境**：
    ```sh
    python -m venv venv
    source venv/bin/activate
    ```

3. **安装所需的包**：
    ```sh
    pip install -r requirements.txt
    ```

4. **安装附加依赖项**：
    ```sh
    pip install beautifulsoup4 requests
    ```

## 配置

1. **打开项目目录**：
    ```sh
    cd /path/to/your/project/gradio
    ```

2. **运行应用程序**：
    ```sh
    ./start_gradio.sh
    ```

## 使用

1. **访问 Gradio Web 界面**：
   打开您的 Web 浏览器，访问 `http://localhost:7861`（如果远程运行，请使用服务器 IP）。

2. **设置选项卡**：
    - 输入您的 OpenAI API 密钥。
    - 选择 API 计费方式。
    - 输入您的 WordPress URL、用户名和密码。
    - 指定发布文章的 WordPress 分类。
    - 选择或输入要使用的 AI 模型。

3. **生成内容选项卡**：
    - 输入几句话的灵感或微信公众号文章链接。
    - 选择所需的 AI 提示词（如果需要）。
    - 点击“生成内容”以创建内容。
    - 查看生成的标题和内容。可以选择重新生成标题。
    - 输入用逗号分隔的标签。
    - 点击“发布到 WordPress”以发布内容。

## 高级自定义

- **提示词**：您可以在设置选项卡中保存和删除 AI 提示词以便重复使用。
- **微信公众号文章**：提供微信公众号文章链接以自动提取和重写内容。

## 故障排除

- **端口问题**：如果默认端口 7861 已被占用，请更改 `gradio_app.py` 文件中的端口：
    ```python
    demo.launch(server_name="0.0.0.0", server_port=7862, debug=True)
    ```

- **依赖项**：确保所有依赖项都已正确安装。缺少的包可以通过 `pip install <package>` 安装。

- **权限**：确保 WordPress 启用了 XML-RPC，并且您的凭据正确。

## 贡献

欢迎贡献！请 fork 仓库并提交 pull 请求以添加任何功能、改进或修复错误。

## 许可证

该项目使用 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。




