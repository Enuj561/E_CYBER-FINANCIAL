"""
Module:  E_auto_sync
Logic:   Scheduled Git sync via Windows Task Scheduler
Detail:  Script chạy tự động, kiểm tra thay đổi Git → add → commit → push.
         Có try/except toàn cục để không bao giờ crash im lặng.
"""
import subprocess
import sys
from datetime import datetime

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Import centralized paths
from E_Helper.E_config import PROJECT_DIR
from E_Helper.E_BlackBox import get_black_box

# Đường dẫn Git executable
GIT_PATH = r"C:\Program Files\Git\cmd\git.exe"
black_box = get_black_box(__file__, console=True)

def run_command(command, run_log):
    try:
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
    except Exception:
        run_log.exception("Không chạy được Git command", command=command[1] if len(command) > 1 else "git")
        return None, -1

def main():
    run_log = black_box.bind()
    try:
        run_log.info("Bắt đầu kiểm tra thay đổi dự án")
        # Kiểm tra trạng thái Git
        stdout, code = run_command([GIT_PATH, "status", "--porcelain"], run_log)
        
        if code == 0 and stdout:
            run_log.info("Phát hiện thay đổi, bắt đầu sync", changed_lines=len(stdout.splitlines()))
            
            _, add_code = run_command([GIT_PATH, "add", "."], run_log)
            if add_code != 0:
                run_log.error("Git add thất bại", return_code=add_code)
                return 1
            
            commit_msg = f"Auto-sync lúc {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            _, commit_code = run_command([GIT_PATH, "commit", "-m", commit_msg], run_log)
            if commit_code != 0:
                run_log.error("Git commit thất bại", return_code=commit_code)
                return 1
            
            _, push_code = run_command([GIT_PATH, "push", "-u", "origin", "main"], run_log)
            
            if push_code == 0:
                run_log.info("Sync thành công lên GitHub")
                return 0
            else:
                run_log.error("Git push thất bại", return_code=push_code)
                return 1
        elif code == 0:
            run_log.info("Không có thay đổi mới, bỏ qua sync")
            return 0
        else:
            run_log.error("Git status thất bại", return_code=code)
            return 1
    except Exception:
        run_log.exception("Auto Sync thất bại")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
