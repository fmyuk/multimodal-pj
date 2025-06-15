from PyQt5.QtWidgets import QApplication, QLabel
import sys

app = QApplication(sys.argv)
label = QLabel("PyQt5動作テスト")
label.show()
app.exec_()