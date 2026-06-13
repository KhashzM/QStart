"""插件管理对话框 - 显示所有已加载插件，支持启用/禁用、安装和卸载"""

import os
import shutil

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox,
)

from plugin_settings_dialog import PluginSettingsDialog


class PluginCard(QWidget):
    """单个插件的卡片控件"""

    def __init__(self, plugin, enabled, plugin_path, on_toggle, on_settings, on_uninstall, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self._enabled = enabled
        self._plugin_path = plugin_path
        self._on_toggle = on_toggle
        self._on_settings = on_settings
        self._on_uninstall = on_uninstall
        self._build_ui()

    def _build_ui(self):
        self.setFixedHeight(100)
        self.setStyleSheet("""
            QWidget#plugin-card {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
            QWidget#plugin-card:hover {
                border-color: #4A90D9;
            }
        """)
        self.setObjectName("plugin-card")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        # 图标区域
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(44, 44)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("""
            QLabel {
                background: #f0f5ff;
                border-radius: 8px;
                font-size: 22px;
            }
        """)
        kw = self.plugin.keywords
        if any(k in ("calc", "计算") for k in kw):
            icon_lbl.setText("🧮")
        elif any(k in ("search", "搜索") for k in kw):
            icon_lbl.setText("🔍")
        elif any(k in ("clip", "剪贴板") for k in kw):
            icon_lbl.setText("📋")
        elif any(k in ("hk", "hotkey", "热键", "快捷键") for k in kw):
            icon_lbl.setText("⌨️")
        elif any(k in ("ai", "qa", "问答") for k in kw):
            icon_lbl.setText("🤖")
        else:
            icon_lbl.setText("🧩")
        layout.addWidget(icon_lbl)

        # 信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        name_row = QHBoxLayout()
        name_lbl = QLabel(self.plugin.name)
        name_lbl.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        name_row.addWidget(name_lbl)

        version_lbl = QLabel(f"v{self.plugin.version}")
        version_lbl.setStyleSheet("color: #aaa; font-size: 11px;")
        name_row.addWidget(version_lbl)
        name_row.addStretch()
        info_layout.addLayout(name_row)

        desc_lbl = QLabel(self.plugin.description)
        desc_lbl.setStyleSheet("color: #888; font-size: 12px;")
        desc_lbl.setWordWrap(True)
        info_layout.addWidget(desc_lbl)

        # 显示插件文件路径
        path_lbl = QLabel(f"📁 {os.path.basename(self._plugin_path) if self._plugin_path else '内置插件'}")
        path_lbl.setStyleSheet("color: #bbb; font-size: 10px;")
        info_layout.addWidget(path_lbl)

        kw_text = "关键词: " + ", ".join(self.plugin.keywords) if self.plugin.keywords else "无关键词（参与全局搜索）"
        kw_lbl = QLabel(kw_text)
        kw_lbl.setStyleSheet("color: #bbb; font-size: 11px;")
        info_layout.addWidget(kw_lbl)

        layout.addLayout(info_layout, 1)

        # 按钮区域
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        self.toggle_btn = QPushButton()
        self.toggle_btn.setFixedWidth(64)
        self.toggle_btn.setFixedHeight(28)
        self._update_toggle_style()
        self.toggle_btn.clicked.connect(self._do_toggle)
        btn_layout.addWidget(self.toggle_btn)

        self.settings_btn = QPushButton("设置")
        self.settings_btn.setFixedWidth(64)
        self.settings_btn.setFixedHeight(28)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: #f0f5ff; color: #4A90D9; border: 1px solid #c8ddf5;
                border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background: #e0edff; }
            QPushButton:pressed { background: #d0e5ff; }
            QPushButton:disabled {
                background: #f5f5f5; color: #aaa; border-color: #ddd;
            }
        """)
        self.settings_btn.clicked.connect(self._do_settings)
        if not self.plugin.get_settings_schema():
            self.settings_btn.setEnabled(False)
            self.settings_btn.setToolTip("此插件没有可配置的选项")
        btn_layout.addWidget(self.settings_btn)

        self.uninstall_btn = QPushButton("卸载")
        self.uninstall_btn.setFixedWidth(64)
        self.uninstall_btn.setFixedHeight(28)
        self.uninstall_btn.setStyleSheet("""
            QPushButton {
                background: #f8d7da; color: #721c24; border: 1px solid #f1aeb5;
                border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { background: #f5c6cb; }
            QPushButton:pressed { background: #f1b0b7; }
            QPushButton:disabled {
                background: #f5f5f5; color: #aaa; border-color: #ddd;
            }
        """)
        self.uninstall_btn.clicked.connect(self._do_uninstall)
        # 内置插件不允许卸载
        if not self._plugin_path or not os.path.isfile(self._plugin_path):
            self.uninstall_btn.setEnabled(False)
            self.uninstall_btn.setToolTip("内置插件，无法卸载")
        btn_layout.addWidget(self.uninstall_btn)

        layout.addLayout(btn_layout)

    def _update_toggle_style(self):
        if self._enabled:
            self.toggle_btn.setText("已启用")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background: #e6f4ea; color: #1e7e34; border: 1px solid #b7dfc0;
                    border-radius: 6px; font-size: 12px; font-weight: bold;
                }
                QPushButton:hover { background: #d4edda; }
            """)
        else:
            self.toggle_btn.setText("已禁用")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background: #f8d7da; color: #721c24; border: 1px solid #f1aeb5;
                    border-radius: 6px; font-size: 12px; font-weight: bold;
                }
                QPushButton:hover { background: #f5c6cb; }
            """)

    def _do_toggle(self):
        self._enabled = not self._enabled
        self._update_toggle_style()
        if self._on_toggle:
            self._on_toggle(self.plugin.name, self._enabled)

    def _do_settings(self):
        if self._on_settings:
            self._on_settings(self.plugin)

    def _do_uninstall(self):
        if self._on_uninstall:
            self._on_uninstall(self.plugin.name, self._plugin_path)


class PluginManagerDialog(QDialog):
    """插件管理对话框"""

    def __init__(self, plugin_manager, parent=None):
        super().__init__(parent)
        self.pm = plugin_manager
        self.setWindowTitle("插件管理")
        self.setMinimumSize(600, 500)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # 标题栏
        header = QHBoxLayout()
        title = QLabel("插件管理")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        header.addWidget(title)
        header.addStretch()

        install_btn = QPushButton("📦 安装插件")
        install_btn.setStyleSheet("""
            QPushButton {
                background: #28a745; color: white; border: 1px solid #20c997;
                border-radius: 6px; padding: 5px 14px; font-size: 12px;
            }
            QPushButton:hover { background: #218838; }
        """)
        install_btn.clicked.connect(self._install_plugin)
        header.addWidget(install_btn)

        reload_btn = QPushButton("🔄 重载全部")
        reload_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0; color: #555; border: 1px solid #ddd;
                border-radius: 6px; padding: 5px 14px; font-size: 12px;
            }
            QPushButton:hover { background: #e4e4e4; }
        """)
        reload_btn.clicked.connect(self._reload_all)
        header.addWidget(reload_btn)
        layout.addLayout(header)

        # 说明
        note = QLabel("管理已安装的插件。点击「安装插件」上传 .py 文件，或直接将插件文件拖放到 plugins/ 目录。")
        note.setStyleSheet("color: #999; font-size: 11px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #f8f8f8; border: none; }")

        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setContentsMargins(4, 4, 4, 4)

        self._build_cards()

        scroll.setWidget(self.cards_widget)
        layout.addWidget(scroll)

        # 底部按钮
        footer = QHBoxLayout()
        footer.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #4A90D9; color: white; border: none;
                border-radius: 6px; padding: 6px 20px; min-width: 80px;
            }
            QPushButton:hover { background: #3A80C9; }
        """)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        layout.addLayout(footer)

    def _build_cards(self):
        """为每个插件创建卡片"""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        plugins = self.pm.get_all_plugins()
        if not plugins:
            empty = QLabel("暂无已加载的插件。\n\n点击「安装插件」或手动将插件 .py 文件放入 src/plugins/ 目录后，点击「重载全部」。")
            empty.setStyleSheet("color: #999; font-size: 13px;")
            empty.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(empty)
        else:
            for plugin in plugins:
                enabled = self.pm.is_enabled(plugin.name)
                plugin_path = self._get_plugin_path(plugin)
                card = PluginCard(
                    plugin=plugin,
                    enabled=enabled,
                    plugin_path=plugin_path,
                    on_toggle=self._on_toggle,
                    on_settings=self._on_settings,
                    on_uninstall=self._on_uninstall,
                )
                self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _get_plugin_path(self, plugin):
        """获取插件文件路径"""
        import sys
        module_name = None
        for name, module in sys.modules.items():
            if hasattr(module, plugin.__class__.__name__):
                if getattr(module, plugin.__class__.__name__) is plugin.__class__:
                    module_name = name
                    break
        
        if module_name and module_name.startswith("plugins."):
            module = sys.modules.get(module_name)
            if module and hasattr(module, "__file__"):
                return module.__file__
        return None

    def _on_toggle(self, name, enabled):
        if enabled:
            self.pm.enable(name)
        else:
            self.pm.disable(name)

    def _on_settings(self, plugin):
        if plugin.name == "自定义热键":
            try:
                # 如果有设置项，先显示通用设置对话框（包含通知设置）
                if plugin.get_settings_schema():
                    dlg = PluginSettingsDialog(plugin, self)
                    dlg.exec_()
                else:
                    # 否则直接打开热键管理对话框
                    from plugins.custom_hotkeys_dialog import CustomHotkeysDialog
                    dlg = CustomHotkeysDialog(plugin, self)
                    dlg.exec_()
            except Exception as e:
                print(f"打开设置对话框失败: {e}")
        else:
            dlg = PluginSettingsDialog(plugin, self)
            dlg.exec_()

    def _on_uninstall(self, plugin_name, plugin_path):
        if not plugin_path or not os.path.isfile(plugin_path):
            QMessageBox.warning(self, "提示", "无法卸载此插件")
            return

        # 查找插件配置文件
        plugin_dir = os.path.dirname(plugin_path)
        config_path = os.path.join(plugin_dir, "plugin.json")
        data_files = []
        
        if os.path.exists(config_path):
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                data_files = config.get('data_files', [])
        
        # 检查数据文件是否存在
        data_dir = os.path.join(os.path.dirname(self.pm._plugins_dir), "data")
        existing_data_files = []
        for df in data_files:
            df_path = os.path.join(data_dir, df)
            if os.path.exists(df_path):
                existing_data_files.append(df)
        
        # 构建确认消息
        message = f"确定要卸载插件「{plugin_name}」吗？\n\n文件位置: {plugin_path}"
        if existing_data_files:
            message += f"\n\n该插件产生的数据文件:\n{chr(10).join(existing_data_files)}"
        
        reply = QMessageBox.question(
            self,
            "确认卸载",
            message + "\n\n此操作无法撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                # 先禁用插件
                self.pm.disable(plugin_name)
                
                # 删除插件文件
                os.remove(plugin_path)
                
                # 删除对应的 .pyc 文件
                pyc_path = plugin_path.replace(".py", ".pyc")
                if os.path.exists(pyc_path):
                    os.remove(pyc_path)
                
                # 删除数据文件（如果用户确认）
                if existing_data_files:
                    data_reply = QMessageBox.question(
                        self,
                        "删除数据文件",
                        f"是否同时删除插件产生的数据文件？\n\n{chr(10).join(existing_data_files)}",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if data_reply == QMessageBox.Yes:
                        for df in existing_data_files:
                            df_path = os.path.join(data_dir, df)
                            if os.path.exists(df_path):
                                os.remove(df_path)
                
                # 重新加载插件列表
                self.pm.reload_plugins()
                self._build_cards()
                
                QMessageBox.information(self, "成功", f"插件「{plugin_name}」已卸载")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"卸载失败: {str(e)}")

    def _install_plugin(self):
        """安装新插件（支持JSON配置文件）"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择插件配置文件",
            "",
            "插件配置文件 (*.json);;Python 文件 (*.py)"
        )
        
        if not file_path:
            return

        # 检查文件是否有效
        if not os.path.isfile(file_path):
            QMessageBox.warning(self, "错误", "选择的文件不存在")
            return

        plugins_dir = self.pm._plugins_dir
        
        try:
            if file_path.endswith('.json'):
                # 通过JSON配置文件安装
                self._install_plugin_from_json(file_path, plugins_dir)
            else:
                # 兼容旧版：直接安装单个py文件
                self._install_plugin_from_py(file_path, plugins_dir)
            
            # 重新加载插件
            self.pm.reload_plugins()
            self._build_cards()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"安装失败: {str(e)}")

    def _install_plugin_from_json(self, json_path, plugins_dir):
        """从JSON配置文件安装插件"""
        import json
        
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        plugin_name = config.get('name', '未知插件')
        files = config.get('files', [])
        main_module = config.get('main_module', '')
        
        if not files:
            QMessageBox.warning(self, "错误", "配置文件中未指定插件文件")
            return
        
        # 获取配置文件所在目录
        config_dir = os.path.dirname(json_path)
        
        # 从配置文件路径推断插件目录名（使用配置文件所在的文件夹名）
        plugin_folder_name = os.path.basename(config_dir)
        if not plugin_folder_name or plugin_folder_name == 'plugins':
            # 如果配置文件直接在 plugins 目录下，使用插件名称作为目录名
            plugin_folder_name = plugin_name.replace(' ', '_').lower()
        
        # 创建插件目标目录
        target_plugin_dir = os.path.join(plugins_dir, plugin_folder_name)
        os.makedirs(target_plugin_dir, exist_ok=True)
        
        # 检查是否有文件需要覆盖
        files_to_overwrite = []
        for file_name in files:
            target_path = os.path.join(target_plugin_dir, os.path.basename(file_name))
            if os.path.exists(target_path):
                files_to_overwrite.append(os.path.basename(file_name))
        
        # 如果有文件需要覆盖，询问用户
        if files_to_overwrite:
            file_list = '\n'.join(files_to_overwrite)
            reply = QMessageBox.question(
                self,
                "确认覆盖",
                f"以下文件已存在，是否覆盖？\n{file_list}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        
        # 复制所有文件到插件目录
        for file_name in files:
            src_path = os.path.join(config_dir, file_name)
            if not os.path.exists(src_path):
                print(f"警告：文件不存在: {src_path}")
                continue
            
            target_path = os.path.join(target_plugin_dir, os.path.basename(file_name))
            shutil.copy2(src_path, target_path)
        
        # 复制 plugin.json 到插件目录
        target_json_path = os.path.join(target_plugin_dir, 'plugin.json')
        shutil.copy2(json_path, target_json_path)
        
        # 创建 __init__.py 文件
        init_path = os.path.join(target_plugin_dir, '__init__.py')
        if not os.path.exists(init_path):
            # 从 main_module 推断插件类名
            if main_module:
                # main_module 格式如 "capslock_plugin.py"，需要转换为模块名
                module_name = main_module.replace('.py', '')
                init_content = f"# {plugin_name}\nfrom .{module_name} import *\n\n__all__ = []\n"
            else:
                init_content = f"# {plugin_name}\n"
            
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write(init_content)
        
        QMessageBox.information(self, "成功", f"插件「{plugin_name}」已安装到 {plugin_folder_name}/")

    def _install_plugin_from_py(self, file_path, plugins_dir):
        """安装单个Python文件（兼容旧版）"""
        file_name = os.path.basename(file_path)
        
        # 检查是否已存在
        target_path = os.path.join(plugins_dir, file_name)
        if os.path.exists(target_path):
            reply = QMessageBox.question(
                self,
                "确认覆盖",
                f"插件「{file_name}」已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        
        # 复制文件到插件目录
        shutil.copy2(file_path, target_path)
        QMessageBox.information(self, "成功", f"插件「{file_name}」已安装")

    def _reload_all(self):
        self.pm.reload_plugins()
        self._build_cards()
