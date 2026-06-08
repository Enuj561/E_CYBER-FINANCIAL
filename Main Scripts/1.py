import ctypes

# Gọi hàm MessageBoxW của thư viện C/C++ Windows
ctypes.windll.user32.MessageBoxW(0, "Hello cc\nChào mừng đến với Python!", "Thông báo xịn xò", 0)
