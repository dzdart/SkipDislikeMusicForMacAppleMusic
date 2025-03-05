import subprocess
import time
import os
from plyer import notification  # 用于发送系统通知

HOME_DIR = os.path.sep.join([os.path.expanduser("~"),"SkipMusic"])


if not os.path.exists(HOME_DIR):
    os.makedirs(HOME_DIR)

KEYWORDS_FILE = os.path.sep.join([HOME_DIR,"keywords.txt"])  # 关键字文件路径
LOG_FILE=os.sep.join([HOME_DIR,"SkipMusic.log"])  # 日志文件路径
GARBAGE_MUSIC_FILE=os.sep.join([HOME_DIR,"Garbage.txt"])  # 垃圾音乐文件路径

# 记录日志
def log(message):
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

try:
    # 检查关键字文件是否存在，不存在则创建
    if not os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
            f.write("# Add keywords to skip tracks\n")
            f.flush()
            f.close()

    # 检查日志文件是否存在，不存在则创建
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("# SkipMusic Log\n")
            f.flush()
            f.close()

    if not os.path.exists(GARBAGE_MUSIC_FILE):
        with open(GARBAGE_MUSIC_FILE, "w", encoding="utf-8") as f:
            f.write("# Garbage Music\n")
            f.flush()
            f.close

    # 读取关键字列表，跳过第一行（注释）
    def read_keywords_from_file():
        try:
            with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                keywords = [line.strip() for line in lines[1:] if line.strip()]  # 跳过第一行
            return keywords
        except Exception as e:
            print(f"Error reading keywords file: {e}")
            return []

    # 获取 Apple Music 当前播放的歌曲信息
    def get_current_track_info():
        try:
            name = subprocess.run(
                ['osascript', '-e', 'tell application "Music" to name of current track'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            ).stdout.strip()
            
            artist = subprocess.run(
                ['osascript', '-e', 'tell application "Music" to artist of current track'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            ).stdout.strip()
            
            album = subprocess.run(
                ['osascript', '-e', 'tell application "Music" to album of current track'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            ).stdout.strip()
            
            track_info = f"{name} - {artist} ({album})"
            return track_info
        except Exception as e:
            print(f"Error getting track info: {e}")
            return None

    # 获取 Apple Music 播放状态
    def get_playback_status():
        try:
            status = subprocess.run(
                ['osascript', '-e', 'tell application "Music" to player state as string'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            ).stdout.strip()
            return status.lower()  # 返回小写 "playing" 或 "paused"
        except Exception as e:
            print(f"Error getting playback status: {e}")
            return None

    # 切换到下一曲
    def skip_to_next_track(track=""):
        try:
            MarkDislike()
            subprocess.run(['osascript', '-e', 'tell application "Music" to skip to next track'])
            if track!="":
                log(f"Skipping track: {track}")
                with open(GARBAGE_MUSIC_FILE,"a", encoding="utf-8") as f:
                    f.write(track + "\n")
                    f.flush()
                    f.close()
        except Exception as e:
            print(f"Error skipping track: {e}")

    # 发送系统通知
    def send_notification(message):
        try:
            subprocess.run(
                ['osascript', '-e', f'display notification "{message}" with title "Apple Music Notification"'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
        except Exception as e:
            print(f"Error sending notification: {e}")

    #标记不喜欢
    def MarkDislike():
        applescript = '''
        tell application "Music"
            if player state is playing then
                try
                    set currentTrack to current track
                    set disliked of currentTrack to true
                    display notification "已标记减少推荐: " & (get name of currentTrack)
                on error
                    display dialog "无法标记当前歌曲"
                end try
            else
                display dialog "当前没有播放的歌曲"
            end if
        end tell
        '''
        try:
            # 执行AppleScript
            process = subprocess.run(
                ["osascript", "-e", applescript],
                check=True,
                text=True,
                capture_output=True
            )

            # 输出执行结果（调试时使用）
            log(f"执行结果:{process.stdout}")

        except subprocess.CalledProcessError as e:
            log(f"执行失败 (错误码 {e.returncode}):")
            log(f"错误信息:{e.stderr}", )
        except Exception as e:
            log(f"发生意外错误:{e}")


    # 监控 Apple Music 播放状态
    def monitor_music_playback():
        oldstr = ""
        last_modified = os.stat(KEYWORDS_FILE).st_mtime if os.path.exists(KEYWORDS_FILE) else 0
        keywords = read_keywords_from_file()  # 初始化关键字

        while True:
            # 检测 Apple Music 是否正在播放
            status = get_playback_status()
            if status == "playing":
                # 检测关键字文件是否更新
                try:
                    current_modified = os.stat(KEYWORDS_FILE).st_mtime
                    if current_modified != last_modified:
                        log("Keywords file updated, reloading keywords.")
                        keywords = read_keywords_from_file()
                        last_modified = current_modified
                except Exception as e:
                    print(f"Error checking keywords file: {e}")

                # 获取当前播放歌曲信息
                current_track = get_current_track_info()
                if current_track:
                    if oldstr != current_track:
                        oldstr = current_track
                        log(oldstr)
                    for keyword in keywords:
                        if keyword.lower() in current_track.lower():
                            log(f"Track contains the keyword '{keyword}', skipping to next track.")
                            skip_to_next_track(current_track)
                            send_notification(f"Skipped track: {current_track}")

                            break  # 找到匹配的关键字后跳出循环

            else:
                # 如果没有在播放，暂停检测
                print("Apple Music is not playing. Waiting for playback to start.")
            
            time.sleep(5)  # 每 5 秒检查一次
except Exception as e:
    print(f"Error: {e}")
    log(f"Error: {e}")

if __name__ == "__main__":
    monitor_music_playback()