import sys
import os
import platform
import subprocess
import ctypes
import psutil
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QPixmap

# Hàm xử lý đường dẫn tài nguyên để sau này đóng gói không bị mất ảnh
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- HÀM TRÍCH XUẤT THÔNG TIN HỆ THỐNG ---
def get_system_info():
    # 1. Hệ điều hành hiện tại
    os_name = f"{platform.system()} {platform.release()} {platform.architecture()[0]}"
    
    # 2. Tên Laptop
    laptop_name = "Unknown Laptop"
    try:
        out = subprocess.check_output('wmic csproduct get name', shell=True).decode('utf-8', errors='ignore').split('\n')
        if len(out) > 1 and out[1].strip():
            laptop_name = out[1].strip()
    except:
        pass
        
    # 3. CPU
    cpu_name = "Unknown CPU"
    try:
        out = subprocess.check_output('wmic cpu get name', shell=True).decode('utf-8', errors='ignore').split('\n')
        if len(out) > 1 and out[1].strip():
            cpu_name = out[1].strip()
    except:
        pass
        
    # 4. RAM
    ram_gb = "Unknown RAM"
    try:
        total_bytes = psutil.virtual_memory().total
        ram_gb = f"{total_bytes / (1024**3):.1f} GB"
    except:
        pass
        
    return os_name, laptop_name, cpu_name, ram_gb

# --- HÀM TRÍCH XUẤT THÔNG TIN PIN ---
def get_battery_stats():
    battery = psutil.sensors_battery()
    percent = 100
    is_charging = False
    
    if battery:
        percent = battery.percent
        is_charging = battery.power_plugged
    else:
        return 100, "N/A (Máy Bàn)", "Tốt", "#2ECC71", "Không sạc"

    # Tính độ chai pin (Wear Level)
    wear_str = "Đang quét..."
    try:
        design_out = subprocess.check_output('powershell -command "(Get-WmiObject -Namespace root\\wmi -Class BatteryStaticData).DesignedCapacity"', shell=True).decode('utf-8', errors='ignore').strip()
        full_out = subprocess.check_output('powershell -command "(Get-WmiObject -Namespace root\\wmi -Class BatteryFullChargedCapacity).FullChargedCapacity"', shell=True).decode('utf-8', errors='ignore').strip()
        
        if design_out and full_out:
            design_val = int(design_out.split()[0])
            full_val = int(full_out.split()[0])
            if design_val > 0:
                health = (full_val / design_val) * 100
                wear = max(0.0, 100 - health)
                wear_str = f"{wear:.1f}%"
    except:
        wear_str = "Không hỗ trợ"

    # Tính công suất sạc hiện tại (W)
    charge_power = "Không sạc"
    if is_charging:
        try:
            rate_out = subprocess.check_output('powershell -command "(Get-WmiObject -Namespace root\\wmi -Class BatteryStatus).ChargeRate"', shell=True).decode('utf-8', errors='ignore').strip()
            if rate_out:
                rate_val = int(rate_out.split()[0])
                if rate_val > 0:
                    watts = rate_val / 1000
                    charge_power = f"{watts:.1f} W"
                else:
                    charge_power = "Đang sạc (Đầy/Duy trì)"
        except:
            charge_power = "Đang sạc"

    # Tình trạng pin
    if percent < 20:
        status_text = "Xấu"
        status_color = "#E74C3C"
    else:
        status_text = "Tốt"
        status_color = "#2ECC71"

    return percent, wear_str, status_text, status_color, charge_power


# --- MÀN HÌNH KHỞI ĐỘNG CẬP NHẬT ẢNH NỀN HOSHINO ---
class SplashScreen(QWidget):
    def __init__(self, on_finish_callback):
        super().__init__()
        self.on_finish_callback = on_finish_callback
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(600, 340)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.card = QWidget()
        self.card.setObjectName("SplashCard")
        
        bg_splash = resource_path("Hosino.jfif").replace("\\", "/")
        if os.path.exists(bg_splash):
            self.card.setStyleSheet(f"""
                QWidget#SplashCard {{
                    border-image: url('{bg_splash}') 0 0 0 0 stretch stretch;
                    border: 2px solid #00D2FF;
                    border-radius: 20px;
                }}
            """)
        else:
            self.card.setStyleSheet("""
                QWidget#SplashCard {
                    background-color: rgba(18, 20, 26, 0.95);
                    border: 2px solid #00D2FF;
                    border-radius: 20px;
                }
            """)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            color: #00D2FF;
            font-family: 'Mi Sans', 'MiSans', 'Segoe UI';
            font-size: 32px;
            font-weight: bold;
            letter-spacing: 2px;
            background-color: rgba(18, 20, 26, 0.75);
            padding: 8px 20px;
            border-radius: 10px;
        """)

        self.sub_label = QLabel("")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("""
            color: #FFFFFF;
            font-family: 'Mi Sans', 'MiSans', 'Segoe UI';
            font-size: 14px;
            font-style: italic;
            margin-top: 15px;
            background-color: rgba(18, 20, 26, 0.75);
            padding: 4px 12px;
            border-radius: 6px;
        """)

        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.sub_label)
        layout.addWidget(self.card)

        self.full_title = "BatteryTest Archive"
        self.full_sub = "by Hải Phong Phosphorus"
        self.title_index = 0
        self.sub_index = 0

        self.typing_timer = QTimer(self)
        self.typing_timer.timeout.connect(self.type_text)
        self.typing_timer.start(50)

        QTimer.singleShot(5000, self.finish_splash)

    def type_text(self):
        if self.title_index < len(self.full_title):
            self.title_label.setText(self.full_title[:self.title_index + 1])
            self.title_index += 1
        elif self.sub_index < len(self.full_sub):
            self.sub_label.setText(self.full_sub[:self.sub_index + 1])
            self.sub_index += 1
        else:
            self.typing_timer.stop()

    def finish_splash(self):
        self.close()
        self.on_finish_callback()


# --- MÀN HÌNH CHÍNH (MAIN APPLICATION) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BatteryTest Archive")
        self.setFixedSize(780, 480)

        try:
            myappid = 'schale.batterytest.archive.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass

        # CẬP NHẬT: Sử dụng pic2.ico làm icon của cửa sổ phần mềm
        icon_path = resource_path("pic2.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(35, 35, 35, 35)

        self.card = QWidget()
        self.card.setObjectName("InfoCard")
        
        self.card.setStyleSheet("""
            QWidget#InfoCard {
                background-color: rgba(18, 22, 30, 0.88);
                border: 2px solid rgba(255, 255, 255, 0.15);
                border-radius: 20px;
            }
            QLabel {
                font-family: 'Inter', 'Segoe UI Semibold', 'Segoe UI', Arial;
                color: #FFFFFF;
                font-size: 14px;
            }
            QLabel.TitleText {
                font-size: 18px;
                font-weight: bold;
                color: #00D2FF;
                letter-spacing: 2px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                padding-bottom: 8px;
            }
            QLabel.LabelName {
                color: #A0AAB2;
                font-weight: bold;
            }
            QLabel.ValueText {
                color: #00FFCC;
                font-weight: bold;
            }
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 25, 30, 25)
        card_layout.setSpacing(15)

        card_title = QLabel("SYSTEM DIAGNOSTIC ARCHIVE")
        card_title.setProperty("class", "TitleText")
        card_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(card_title)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(18)

        self.lbl_battery = QLabel("--%")
        self.lbl_wear = QLabel("--%")
        self.lbl_status = QLabel("--")
        self.lbl_power = QLabel("--")

        self.lbl_os = QLabel("--")
        self.lbl_laptop = QLabel("--")
        self.lbl_cpu = QLabel("--")
        self.lbl_ram = QLabel("--")

        self.create_row(grid, "Số pin hiện tại:", self.lbl_battery, 0, 0)
        self.create_row(grid, "Độ chai pin:", self.lbl_wear, 1, 0)
        self.create_row(grid, "Tình trạng pin:", self.lbl_status, 2, 0)
        self.create_row(grid, "Công suất sạc:", self.lbl_power, 3, 0)

        self.create_row(grid, "Hệ điều hành:", self.lbl_os, 0, 2)
        self.create_row(grid, "Tên Laptop:", self.lbl_laptop, 1, 2)
        self.create_row(grid, "Bộ vi xử lý (CPU):", self.lbl_cpu, 2, 2)
        self.create_row(grid, "Bộ nhớ (RAM):", self.lbl_ram, 3, 2)

        card_layout.addWidget(grid_widget)
        main_layout.addWidget(self.card)

        os_name, laptop_name, cpu_name, ram_gb = get_system_info()
        self.lbl_os.setText(os_name)
        self.lbl_laptop.setText(laptop_name)
        self.lbl_cpu.setText(cpu_name)
        self.lbl_ram.setText(ram_gb)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_battery_ui)
        self.timer.start(4000)

        self.update_battery_ui()

    def create_row(self, grid, label_name, value_label, row, col_start):
        lbl = QLabel(label_name)
        lbl.setProperty("class", "LabelName")
        value_label.setProperty("class", "ValueText")
        grid.addWidget(lbl, row, col_start)
        grid.addWidget(value_label, row, col_start + 1)

    def update_battery_ui(self):
        percent, wear_str, status_text, status_color, charge_power = get_battery_stats()

        self.lbl_battery.setText(f"{percent}%")
        self.lbl_wear.setText(wear_str)
        self.lbl_status.setText(status_text)
        self.lbl_status.setStyleSheet(f"color: {status_color}; font-size: 15px; font-weight: bold;")
        self.lbl_power.setText(charge_power)

        bg_image = "pic1.jfif" if percent >= 20 else "pic3.jfif"
        bg_path = resource_path(bg_image).replace("\\", "/")

        if os.path.exists(bg_path):
            self.central_widget.setStyleSheet(f"""
                QWidget#CentralWidget {{
                    border-image: url('{bg_path}') 0 0 0 0 stretch stretch;
                }}
            """)
        else:
            self.central_widget.setStyleSheet("QWidget#CentralWidget { background-color: #11141A; }")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    def show_main():
        global main_win
        main_win = MainWindow()
        main_win.show()

    splash = SplashScreen(show_main)
    splash.show()
    
    sys.exit(app.exec())