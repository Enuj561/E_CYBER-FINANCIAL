import os
import subprocess
import datetime
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

PROJECT_DIR = r"C:\Users\HP\Documents\E_CYBER-FINANCIAL"
GIT_PATH = r"C:\Program Files\Git\cmd\git.exe"

def run_command(command):
    try:
        # Ẩn cửa sổ console khi chạy ngầm bằng Task Scheduler
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(
            command, 
            cwd=PROJECT_DIR, 
            capture_output=True, 
            text=True, 
            check=False,
            startupinfo=startupinfo
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Lỗi chạy lệnh {' '.join(command)}: {e}")
        return None, -1

def main():
    log_msg = f"[{datetime.datetime.now()}] Bắt đầu kiểm tra thay đổi dự án...\n"
    
    # Kiểm tra trạng thái Git
    stdout, code = run_command([GIT_PATH, "status", "--porcelain"])
    
    if code == 0 and stdout:
        log_msg += f"Phát hiện có thay đổi:\n{stdout}\nĐang tiến hành sync lên GitHub...\n"
        
        # 1. Add all files
        run_command([GIT_PATH, "add", "."])
        
        # 2. Commit
        commit_msg = f"Auto-sync lúc {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        run_command([GIT_PATH, "commit", "-m", commit_msg])
        
        # 3. Push to GitHub
        push_stdout, push_code = run_command([GIT_PATH, "push", "-u", "origin", "main"])
        
        if push_code == 0:
            log_msg += "Sync thành công lên GitHub!\n"
        else:
            log_msg += f"Sync thất bại khi push. Có thể do chưa thiết lập chứng thực (credentials).\n"
    elif code == 0:
        log_msg += "Không có thay đổi nào mới. Bỏ qua sync.\n"
    else:
        log_msg += f"Lỗi kiểm tra trạng thái Git (Chưa có kho chứa, v.v..)\n"
        
    print(log_msg)
    
    # Ghi lại lịch sử chạy vào file sync_log.txt để bạn tiện theo dõi
    log_file_path = os.path.join(PROJECT_DIR, "agent", "sync_log.txt")
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(log_msg + "-"*40 + "\n")

if __name__ == "__main__":
    main()
