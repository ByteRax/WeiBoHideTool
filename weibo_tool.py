"""
微博批量操作 CLI 工具

功能：
1. 批量将微博设为仅自己可见

作者：WeiBoHideTool
"""

import requests
import time
import math
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ======================
# 全局配置
# ======================

# 请求间隔（秒），避免请求过于频繁被限流
SLEEP = 1.5

# 并发线程数（用于多线程处理）
THREADS = 5

# 线程安全的计数器
class ThreadSafeCounter:
    """线程安全的计数器"""

    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self._value += 1

    @property
    def value(self):
        with self._lock:
            return self._value


# ======================
# 初始化配置
# ======================

def get_user_config():
    """
    获取用户配置（UID 和 Cookie）

    Returns:
        tuple: (uid, cookie_string)
    """
    uid = input("输入微博UID: ").strip()
    cookie_string = input("粘贴完整Cookie: ").strip()
    return uid, cookie_string


def parse_cookie(cookie_str):
    """
    将 Cookie 字符串解析为字典

    Args:
        cookie_str: Cookie 字符串，格式为 "key1=value1; key2=value2"

    Returns:
        dict: Cookie 字典
    """
    cookies = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            cookies[k] = v
    return cookies


def build_headers(uid, cookie):
    """
    构建请求头

    Args:
        uid: 微博用户 ID
        cookie: Cookie 字典

    Returns:
        dict: 请求头字典
    """
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "client-version": "3.0.0",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://weibo.com",
        "referer": f"https://weibo.com/u/{uid}",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "server-version": "v2026.03.13.2",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "x-xsrf-token": cookie.get("XSRF-TOKEN", "")
    }


def validate_config(uid, cookie, headers):
    """
    校验 UID 和 Cookie 是否有效

    通过发送一个简单的请求来验证配置是否正确

    Args:
        uid: 微博用户 ID
        cookie: Cookie 字典
        headers: 请求头

    Returns:
        tuple: (is_valid, error_message)
    """
    print("\n校验配置中...")

    # 1. 校验 UID 格式
    if not uid:
        return False, "UID 不能为空"
    if not uid.isdigit():
        return False, f"UID 格式错误: 应为纯数字，当前为 '{uid}'"

    # 2. 校验 Cookie 必要字段
    required_cookies = ["SUBP"]
    missing = [k for k in required_cookies if k not in cookie or not cookie[k]]
    if missing:
        return False, f"Cookie 缺少必要字段: {', '.join(missing)}"

    # 3. 发送请求验证
    try:
        url = "https://weibo.com/ajax/statuses/mymblog"
        params = {"uid": uid, "page": 1, "feature": 0}
        r = requests.get(url, headers=headers, cookies=cookie, params=params, timeout=10)

        if r.status_code == 403:
            return False, "Cookie 已过期或无效，请重新获取"
        elif r.status_code == 400:
            return False, f"请求参数错误，请检查 UID 是否正确"
        elif r.status_code != 200:
            return False, f"请求失败: HTTP {r.status_code}"

        data = r.json()

        # 检查响应内容
        if data.get("ok") == 0:
            msg = data.get("msg", "未知错误")
            return False, f"API 返回错误: {msg}"

        if "data" not in data:
            return False, "响应数据格式异常，可能是 Cookie 无效"

        print("✓ 配置校验通过")
        return True, None

    except requests.exceptions.Timeout:
        return False, "请求超时，请检查网络连接"
    except requests.exceptions.ConnectionError:
        return False, "网络连接失败，请检查网络"
    except Exception as e:
        return False, f"校验失败: {e}"


# ======================
# 获取微博列表
# ======================

def fetch_page(uid, headers, cookie, page, since_id=None, retry=3):
    """
    获取单页微博列表

    API: https://weibo.com/ajax/statuses/mymblog

    Args:
        uid: 微博用户 ID
        headers: 请求头
        cookie: Cookie 字典
        page: 页码（从 1 开始）
        since_id: 分页参数，上一页返回的 since_id
        retry: 重试次数

    Returns:
        dict | None: API 响应数据，失败返回 None
    """
    url = "https://weibo.com/ajax/statuses/mymblog"
    params = {
        "uid": uid,
        "page": page,
        "feature": 0
    }
    if since_id:
        params["since_id"] = since_id

    for attempt in range(retry):
        try:
            r = requests.get(url, headers=headers, cookies=cookie, params=params)

            if r.status_code != 200:
                print(f"  请求失败 [{attempt+1}/{retry}]: HTTP {r.status_code}")
                if attempt < retry - 1:
                    time.sleep(3)
                    continue
                return None

            return r.json()

        except Exception as e:
            print(f"  解析错误 [{attempt+1}/{retry}]: {e}")
            if attempt < retry - 1:
                time.sleep(3)
                continue
            return None

    return None


def get_all_weibo_ids(uid, headers, cookie):
    """
    获取所有微博 ID 列表

    Args:
        uid: 微博用户 ID
        headers: 请求头
        cookie: Cookie 字典

    Returns:
        list: 微博 ID 列表
    """
    page = 1
    since_id = None
    ids = []

    while True:
        print(f"读取第 {page} 页...")
        data = fetch_page(uid, headers, cookie, page, since_id)

        if not data or "data" not in data:
            break

        blogs = data["data"].get("list", [])
        if not blogs:
            break

        for blog in blogs:
            ids.append(blog["id"])

        since_id = data["data"].get("since_id")
        page += 1
        time.sleep(SLEEP)

    return ids


# ======================
# 修改微博可见性
# ======================

def set_private(wid, headers, cookie, retry=3, silent=False):
    """
    将单条微博设为仅自己可见

    API: https://weibo.com/ajax/statuses/modifyVisible

    Args:
        wid: 微博 ID
        headers: 请求头
        cookie: Cookie 字典
        retry: 重试次数
        silent: 是否静默模式（不打印日志）

    Returns:
        tuple: (success: bool, wid: int)
    """
    url = "https://weibo.com/ajax/statuses/modifyVisible"
    data = {"ids": wid, "visible": 1}

    for attempt in range(retry):
        try:
            r = requests.post(url, headers=headers, cookies=cookie, data=data)

            if r.status_code != 200:
                if not silent:
                    print(f"  [{wid}] 请求失败: HTTP {r.status_code}")
                if attempt < retry - 1:
                    time.sleep(2)
                    continue
                return False, wid

            result = r.json()
            if result.get("ok") == 1:
                if not silent:
                    print(f"  [{wid}] ✓ 已设为仅自己可见")
                return True, wid
            else:
                if not silent:
                    print(f"  [{wid}] ✗ 设置失败: {result}")
                return False, wid

        except Exception as e:
            if not silent:
                print(f"  [{wid}] 异常: {e}")
            if attempt < retry - 1:
                time.sleep(2)
                continue
            return False, wid

    return False, wid


def set_private_batch_task(wid, headers, cookie, success_counter, fail_counter):
    """
    多线程任务：设置单条微博可见性并更新计数器

    Args:
        wid: 微博 ID
        headers: 请求头
        cookie: Cookie 字典
        success_counter: 成功计数器
        fail_counter: 失败计数器

    Returns:
        bool: 是否成功
    """
    success, _ = set_private(wid, headers, cookie, silent=True)
    if success:
        success_counter.increment()
        print(f"  [{wid}] ✓")
    else:
        fail_counter.increment()
        print(f"  [{wid}] ✗")

    time.sleep(SLEEP)
    return success


def get_weibo_stats(uid, headers, cookie, max_pages=None):
    """
    获取微博统计信息（总数和总页数）

    从第一页 API 响应中获取 total 字段，计算总页数

    Args:
        uid: 微博用户 ID
        headers: 请求头
        cookie: Cookie 字典
        max_pages: 最大处理页数限制，None 表示不限制

    Returns:
        tuple: (total_count, total_pages, actual_pages)
               actual_pages 是实际要处理的页数（考虑 max_pages 限制）
    """
    print("\n获取微博统计信息...")

    data = fetch_page(uid, headers, cookie, 1)
    if not data or "data" not in data:
        return 0, 0, 0

    # 从 API 响应获取总数
    total_count = data["data"].get("total", 0)

    # 每页 20 条，计算总页数
    PAGE_SIZE = 20
    total_pages = math.ceil(total_count / PAGE_SIZE) if total_count > 0 else 0

    # 计算实际要处理的页数
    actual_pages = min(total_pages, max_pages) if max_pages else total_pages

    return total_count, total_pages, actual_pages


def batch_set_private(uid, headers, cookie, max_pages=None, use_threads=True):
    """
    批量将微博设为仅自己可见

    每获取一页就处理一页，自动跳过已是仅自己可见的微博

    Args:
        uid: 微博用户 ID
        headers: 请求头
        cookie: Cookie 字典
        max_pages: 最大处理页数，None 表示不限制
        use_threads: 是否使用多线程处理
    """
    # 获取微博统计信息
    total_count, total_pages, actual_pages = get_weibo_stats(uid, headers, cookie, max_pages)

    if total_count == 0:
        print("\n没有找到任何微博")
        return

    print("\n" + "=" * 50)
    print("微博统计")
    print(f"  总微博数: {total_count}")
    print(f"  总页数: {total_pages}")
    if max_pages:
        print(f"  实际处理: {actual_pages} 页（已限制）")
    print(f"  并发线程: {THREADS}" if use_threads else "  模式: 单线程")
    print("=" * 50)

    # 确认是否继续
    confirm = input("\n是否继续执行批量设置? (y/n): ").strip().lower()
    if confirm != "y":
        print("已取消操作")
        return

    page = 1
    since_id = None

    # 使用线程安全的计数器
    success_counter = ThreadSafeCounter()
    skip_counter = ThreadSafeCounter()
    fail_counter = ThreadSafeCounter()

    print("\n" + "=" * 50)
    print("开始批量设置微博为仅自己可见")
    print("=" * 50)

    while True:
        print(f"\n[第 {page} 页 / {actual_pages} 页]")

        data = fetch_page(uid, headers, cookie, page, since_id)

        if not data or "data" not in data:
            print("  获取数据失败或无更多数据")
            break

        blogs = data["data"].get("list", [])
        if not blogs:
            print("  无更多微博")
            break

        # 筛选需要处理的微博
        to_process = []
        for blog in blogs:
            visible_type = blog.get("visible", {}).get("type", 0)
            if visible_type == 1:
                skip_counter.increment()
                print(f"  [{blog['id']}] ⊘ 跳过（已仅自己可见）")
            else:
                to_process.append(blog["id"])

        # 处理当前页
        if to_process:
            if use_threads and len(to_process) > 1:
                # 多线程处理
                print(f"  使用 {THREADS} 个线程并行处理 {len(to_process)} 条微博...")
                with ThreadPoolExecutor(max_workers=THREADS) as executor:
                    futures = [
                        executor.submit(
                            set_private_batch_task,
                            wid, headers, cookie,
                            success_counter, fail_counter
                        )
                        for wid in to_process
                    ]
                    # 等待所有任务完成
                    for future in as_completed(futures):
                        pass
            else:
                # 单线程处理
                for wid in to_process:
                    success, _ = set_private(wid, headers, cookie)
                    if success:
                        success_counter.increment()
                    else:
                        fail_counter.increment()
                    time.sleep(SLEEP)

        since_id = data["data"].get("since_id")
        page += 1

        if page > actual_pages:
            print(f"\n已完成所有页数处理")
            break

        # 页间间隔
        time.sleep(SLEEP)

    # 打印统计
    print("\n" + "=" * 50)
    print("处理完成")
    print(f"  ✓ 成功: {success_counter.value}")
    print(f"  ⊘ 跳过: {skip_counter.value}")
    print(f"  ✗ 失败: {fail_counter.value}")
    print("=" * 50)


# ======================
# 主菜单
# ======================

def main():
    """主程序入口"""
    print("""
╔══════════════════════════════════════╗
║        微博批量操作工具 v1.0         ║
╠══════════════════════════════════════╣
║  1. 批量设为仅自己可见               ║
║  2. 退出                             ║
╚══════════════════════════════════════╝
""")

    # 获取用户配置
    uid, cookie_string = get_user_config()
    cookie = parse_cookie(cookie_string)
    headers = build_headers(uid, cookie)

    # 校验配置
    is_valid, error_msg = validate_config(uid, cookie, headers)
    if not is_valid:
        print(f"\n✗ 配置校验失败: {error_msg}")
        print("请检查 UID 和 Cookie 后重试")
        return

    while True:
        print()
        choice = input("请选择功能 [1-2]: ").strip()

        if choice == "1":
            max_pages = input("最大处理页数（留空不限制）: ").strip()
            max_pages = int(max_pages) if max_pages else None
            batch_set_private(uid, headers, cookie, max_pages)

        elif choice == "2":
            print("再见！")
            break

        else:
            print("无效选择，请重试")


if __name__ == "__main__":
    main()
