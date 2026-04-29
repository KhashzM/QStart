from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QDialogButtonBox, QApplication
from PyQt5.QtCore import Qt

class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Refreshing App Index")
        self.setFixedSize(400, 120)
        self.setWindowFlags(Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Starting...")
        self.status_label.setStyleSheet("font-size: 14px; color: #333;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 20px;
                border-radius: 10px;
                background: #eee;
            }
            QProgressBar::chunk {
                background: #4A90D9;
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
    
    def update_progress(self, message, value):
        self.status_label.setText(message)
        self.progress_bar.setValue(value)
        QApplication.processEvents()