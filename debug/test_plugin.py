"""插件框架测试脚本 - 无需启动 GUI 即可验证插件加载和调度"""

import os
import sys

# 确保 src 目录在搜索路径中
src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, src_dir)

os.chdir(src_dir)  # 切换到 src 目录，确保相对路径正确

from plugin_manager import PluginManager


def test_plugin_loading():
    """测试插件加载"""
    print("=" * 50)
    print("1. 测试插件加载")
    print("=" * 50)

    pm = PluginManager()
    loaded = pm.load_plugins()
    print(f"   已加载 {len(loaded)} 个插件: {loaded}")

    for plugin in pm.get_all_plugins():
        print(f"   - {plugin.name} v{plugin.version} | 关键词: {plugin.keywords}")

    assert len(loaded) >= 3, f"期望至少加载 3 个插件，实际加载了 {len(loaded)} 个"
    print("   ✅ 插件加载成功!\n")
    return pm


def test_keyword_routing(pm):
    """测试关键词路由"""
    print("=" * 50)
    print("2. 测试关键词路由")
    print("=" * 50)

    # 测试 calc 关键词
    plugin = pm.route("calc 1+1")
    assert plugin is not None, "calc 路由失败"
    assert plugin.name == "计算器", f"期望路由到计算器，实际路由到 {plugin.name}"
    print(f"   'calc 1+1' -> {plugin.name} ✅")

    # 测试中文关键词
    plugin = pm.route("计算 2*3")
    assert plugin is not None, "计算 路由失败"
    print(f"   '计算 2*3' -> {plugin.name} ✅")

    # 测试 search 关键词
    plugin = pm.route("search Python教程")
    assert plugin is not None, "search 路由失败"
    assert plugin.name == "网页搜索"
    print(f"   'search Python教程' -> {plugin.name} ✅")

    # 测试 clip 关键词
    plugin = pm.route("clip list")
    assert plugin is not None, "clip 路由失败"
    assert plugin.name == "剪贴板历史"
    print(f"   'clip list' -> {plugin.name} ✅")

    # 测试无匹配关键词
    plugin = pm.route("notepad")
    assert plugin is None, "非插件关键词不应路由"
    print(f"   'notepad' -> None ✅")

    print()


def test_keyword_extraction(pm):
    """测试关键词提取"""
    print("=" * 50)
    print("3. 测试关键词提取")
    print("=" * 50)

    kw, args = pm.extract_keyword_and_args("calc 1+2+3")
    assert kw == "calc", f"期望 kw='calc', 实际 kw='{kw}'"
    assert args == "1+2+3", f"期望 args='1+2+3', 实际 args='{args}'"
    print(f"   'calc 1+2+3' -> keyword='{kw}', args='{args}' ✅")

    kw, args = pm.extract_keyword_and_args("search")
    assert kw == "search"
    assert args == ""
    print(f"   'search' -> keyword='{kw}', args='{args}' ✅")

    kw, args = pm.extract_keyword_and_args("hello world")
    assert kw is None
    print(f"   'hello world' -> keyword=None ✅")

    print()


def test_plugin_handle(pm):
    """测试插件处理"""
    print("=" * 50)
    print("4. 测试插件执行")
    print("=" * 50)

    # 测试计算器
    calc = pm.route("calc 1+1")
    result = pm.handle(calc, "1+1", context={"keyword": "calc"})
    print(f"   calc '1+1' -> {result}")
    assert result["type"] == "display"
    assert "2" in result["message"]
    print(f"   ✅ 计算 1+1 = 2")

    # 测试计算器复杂表达式
    result = pm.handle(calc, "sqrt(16) + 3", context={"keyword": "calc"})
    print(f"   calc 'sqrt(16)+3' -> {result}")
    assert "7" in result["message"]
    print(f"   ✅ sqrt(16)+3 = 7")

    # 测试空输入
    result = pm.handle(calc, "", context={"keyword": "calc"})
    print(f"   calc '' -> {result}")
    assert "请输入" in result["message"]
    print(f"   ✅ 空输入提示正确")

    # 测试剪贴板（动作模式，handle 不直接打开对话框，跳过 UI 测试）
    clip = pm.route("clip list")
    assert clip is not None, "clip 路由失败"
    print(f"   clip 'list' -> 路由到 {clip.name}")
    # 测试 preview（不需要 QApplication）
    preview_text = clip.preview("list")
    assert preview_text, "preview 不应为空"
    print(f"   clip preview 'list' -> '{preview_text}'")
    print(f"   ✅ 剪贴板插件正常（UI 测试需启动主程序）")

    print()


def test_plugin_search(pm):
    """测试插件全局搜索"""
    print("=" * 50)
    print("5. 测试插件全局搜索")
    print("=" * 50)

    results = pm.search_all("python")
    print(f"   搜索 'python' 得到 {len(results)} 条插件结果")
    for r in results[:3]:
        print(f"     - {r.get('name', '?')}")
    print(f"   ✅ 全局搜索正常")

    print()


def test_enable_disable(pm):
    """测试启用/禁用"""
    print("=" * 50)
    print("6. 测试启用/禁用插件")
    print("=" * 50)

    pm.disable("计算器")
    assert not pm.is_enabled("计算器")
    plugin = pm.route("calc 1+1")
    assert plugin is None, "禁用后不应路由到该插件"
    print(f"   禁用计算器后 'calc 1+1' -> None ✅")

    pm.enable("计算器")
    assert pm.is_enabled("计算器")
    plugin = pm.route("calc 1+1")
    assert plugin is not None, "启用后应能路由"
    print(f"   启用计算器后 'calc 1+1' -> {plugin.name} ✅")

    print()


if __name__ == "__main__":
    print("\n🧪 QStart 插件框架测试\n")

    try:
        pm = test_plugin_loading()
        test_keyword_routing(pm)
        test_keyword_extraction(pm)
        test_plugin_handle(pm)
        test_plugin_search(pm)
        test_enable_disable(pm)

        print("=" * 50)
        print("🎉 所有测试通过!")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)