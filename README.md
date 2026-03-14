# WeiBoHideTool

微博批量操作工具，支持将微博批量设置为仅自己可见。

## 功能

- **批量转为仅自己可见** - 将所有微博设置为仅自己可见
- **自动跳过已隐藏** - 自动跳过已经是仅自己可见的微博
- **多线程处理** - 支持多线程并发处理，提高效率
- **统计信息展示** - 显示总微博数、总页数和处理进度

## 环境要求

- Python 3.10+
- requests

## 安装

```bash
# 克隆项目
git clone https://github.com/ByteRax/WeiBoHideTool.git
cd WeiBoHideTool

# 安装依赖
pip install -r requirements.txt
```

## 使用前必看

此脚本需要 2 个参数：**UID** 和 **Cookie**

### 1. UID 获取方式

1. 登录 https://weibo.com/
2. 点击右上角头像
3. 浏览器地址栏会显示 `https://weibo.com/u/1835716684`
4. 其中 `1835716684` 就是你的 UID

![](https://files.mdnice.com/user/2778/9c2d1018-1948-4b3f-9458-5f855adb4d9f.png)

### 2. Cookie 获取方式

#### 步骤 1：打开开发者工具

在网页任意位置右键点击 **检查**

![](https://files.mdnice.com/user/2778/0e3aca52-8bcf-4214-b787-879ba93397b0.jpg)

#### 步骤 2：获取 Cookie

1. 切换到 **Network（网络）** 标签
2. 点击 **Fetch/XHR** 过滤器
3. 随便找到一个请求（如 `read` 请求）
4. 在右侧 **Headers（标头）** 中找到 **Cookie** 字段
5. 复制完整的 Cookie 值

![](https://files.mdnice.com/user/2778/6211bc76-9c32-456c-9bbe-2fb352bf966d.jpg)

## 执行脚本

```bash
python weibo_tool.py
```

运行后依次输入获取到的 UID 和 Cookie 即可。

## 执行效果

### 输入配置

![](https://files.mdnice.com/user/2778/fe43c104-dbf0-4726-9552-e8f30a581903.png)

### 统计信息

![](https://files.mdnice.com/user/2778/688472db-1669-4e0f-a508-1edfbef346df.png)

### 批量处理

![](https://files.mdnice.com/user/2778/02d6e68c-de00-47b0-9c31-8a4e48b07860.png)

## 注意事项

- Cookie 包含敏感信息，请勿泄露给他人
- 建议在处理前确认统计信息是否正确
- 如遇到请求频繁被限流，可适当增加 `SLEEP` 参数

## License

MIT
