import os
import sys
import shutil
import subprocess
import re
import random
import json
import signal
from pathlib import Path
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QObject, pyqtSlot, pyqtProperty, QUrl, pyqtSignal, QTimer, QMetaObject

class SysBridge(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot('QVariantList', result=str)
    def exec_cmd_list(self, command):
        try:
            cmd_list = [str(x) for x in command]
            return subprocess.run(cmd_list, capture_output=True, text=True).stdout
        except Exception as e:
            return str(e)

    @pyqtSlot(str, result=str)
    def exec_cmd(self, command):
        try:
            return subprocess.run(command, shell=True, capture_output=True, text=True).stdout
        except Exception as e:
            return str(e)

    @pyqtSlot()
    def save_hyprland_position(self):
        # Ищем окно по title, так как Wayland часто не совпадает с PID питона
        try:
            output = subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True).stdout
            if not output: return

            clients = json.loads(output)
            for client in clients:
                if client.get("title") == "Standalone Music App":
                    new_x, new_y = client.get("at", [0, 0])
                    base_dir = Path.home() / ".config" / "music-standalone-app"
                    base_dir.mkdir(parents=True, exist_ok=True)

                    fx = base_dir / ".saved_pos_x"
                    fy = base_dir / ".saved_pos_y"

                    old_x = int(fx.read_text().strip()) if fx.exists() else -1
                    old_y = int(fy.read_text().strip()) if fy.exists() else -1

                    # Перезаписываем только если окно реально сдвинули
                    if old_x != int(new_x) or old_y != int(new_y):
                        fx.write_text(str(int(new_x)))
                        fy.write_text(str(int(new_y)))
                    break
        except Exception:
            pass

class MockPlayer(QObject):
    changed = pyqtSignal()
    postTrackChanged = pyqtSignal()
    trackArtUrlChanged = pyqtSignal()
    trackTitleChanged = pyqtSignal()
    positionChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._title = "Ожидание плеера..."
        self._artist = ""
        self._art = ""
        self._playing = False
        self._position = 0.0
        self._length = 100.0

    @pyqtProperty(str, notify=trackTitleChanged)
    def trackTitle(self): return self._title
    @pyqtProperty(str, notify=changed)
    def trackArtist(self): return self._artist
    @pyqtProperty(str, notify=trackArtUrlChanged)
    def trackArtUrl(self): return self._art
    @pyqtProperty(bool, notify=changed)
    def isPlaying(self): return self._playing
    @pyqtProperty(float, notify=positionChanged)
    def position(self): return self._position
    @position.setter
    def position(self, val):
        subprocess.run(["playerctl", "position", str(val)])
        self._position = val
        self.positionChanged.emit()
        self.changed.emit()
    @pyqtProperty(float, notify=changed)
    def length(self): return self._length
    @pyqtProperty(bool, notify=changed)
    def canGoPrevious(self): return True
    @pyqtProperty(bool, notify=changed)
    def canGoNext(self): return True
    @pyqtProperty(bool, notify=changed)
    def canTogglePlaying(self): return True
    @pyqtProperty(bool, notify=changed)
    def canSeek(self): return True
    @pyqtProperty(str, notify=changed)
    def identity(self): return "System"
    @pyqtProperty(str, notify=changed)
    def desktopEntry(self): return "Media"

    @pyqtSlot()
    def togglePlaying(self): subprocess.run("playerctl play-pause", shell=True)
    @pyqtSlot()
    def next(self): subprocess.run("playerctl next", shell=True)
    @pyqtSlot()
    def previous(self): subprocess.run("playerctl previous", shell=True)

    def fetch_data(self):
        try:
            t = subprocess.run(["playerctl", "metadata", "title"], capture_output=True, text=True).stdout.strip()
            a = subprocess.run(["playerctl", "metadata", "artist"], capture_output=True, text=True).stdout.strip()
            art = subprocess.run(["playerctl", "metadata", "mpris:artUrl"], capture_output=True, text=True).stdout.strip()
            st = subprocess.run(["playerctl", "status"], capture_output=True, text=True).stdout.strip()

            l_raw = subprocess.run(["playerctl", "metadata", "mpris:length"], capture_output=True, text=True).stdout.strip()
            length = float(l_raw) / 1000000.0 if l_raw.isdigit() else self._length

            p_raw = subprocess.run(["playerctl", "position"], capture_output=True, text=True).stdout.strip()
            pos = float(p_raw) if p_raw.replace('.', '', 1).isdigit() else self._position

            changed_any = False
            if t != self._title:
                self._title = t
                self.trackTitleChanged.emit()
                self.postTrackChanged.emit()
                changed_any = True
            if art != self._art:
                self._art = art
                self.trackArtUrlChanged.emit()
                changed_any = True
            if abs(self._position - pos) > 1.5:
                self._position = pos
                self.positionChanged.emit()
                changed_any = True
            if a != self._artist or (st == "Playing") != self._playing or self._length != length:
                self._artist = a
                self._playing = (st == "Playing")
                self._length = length
                changed_any = True

            if changed_any:
                self.changed.emit()
        except:
            pass

class MockMprisController(QObject):
    changed = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = MockPlayer(self)
    @pyqtProperty(QObject, notify=changed)
    def activePlayer(self): return self._player
    @pyqtProperty(str, notify=changed)
    def artUrl(self): return ""
    @pyqtProperty(str, notify=changed)
    def blur(self): return ""
    @pyqtProperty(str, notify=changed)
    def grad(self): return ""
    @pyqtProperty(str, notify=changed)
    def textColor(self): return "#cdd6f4"
    @pyqtProperty(str, notify=changed)
    def deviceIcon(self): return "󰓃"
    @pyqtProperty(str, notify=changed)
    def deviceName(self): return "System"

class MockMpris(QObject):
    changed = pyqtSignal()
    def __init__(self, ctrl, parent=None):
        super().__init__(parent)
        self._ctrl = ctrl
    @pyqtProperty(list, notify=changed)
    def players(self): return [self._ctrl.activePlayer]

class MockTheme(QObject):
    themeChanged = pyqtSignal()
    def __init__(self, parent=None): super().__init__(parent)
    @pyqtProperty(str, notify=themeChanged)
    def base(self): return "#1e1e2e"
    @pyqtProperty(str, notify=themeChanged)
    def mauve(self): return "#cba6f7"
    @pyqtProperty(str, notify=themeChanged)
    def blue(self): return "#89b4fa"
    @pyqtProperty(str, notify=themeChanged)
    def red(self): return "#f38ba8"
    @pyqtProperty(str, notify=themeChanged)
    def text(self): return "#cdd6f4"
    @pyqtProperty(str, notify=themeChanged)
    def subtext0(self): return "#a6adc8"
    @pyqtProperty(str, notify=themeChanged)
    def surface0(self): return "#313244"
    @pyqtProperty(str, notify=themeChanged)
    def surface1(self): return "#45475a"
    @pyqtProperty(str, notify=themeChanged)
    def surface2(self): return "#585b70"
    @pyqtProperty(str, notify=themeChanged)
    def crust(self): return "#11111b"
    @pyqtProperty(str, notify=themeChanged)
    def mantle(self): return "#181825"
    @pyqtProperty(str, notify=themeChanged)
    def overlay0(self): return "#6c7086"
    @pyqtProperty(str, notify=themeChanged)
    def overlay1(self): return "#7f849c"
    @pyqtProperty(str, notify=themeChanged)
    def pink(self): return "#f5c2e7"
    @pyqtProperty(str, notify=themeChanged)
    def lavender(self): return "#b4befe"
    @pyqtProperty(int, notify=themeChanged)
    def borderRadius(self): return 12
    @pyqtProperty(str, notify=themeChanged)
    def fontFamily(self): return "sans-serif"

class RealCava(QObject):
    levelsChanged = pyqtSignal()
    
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self._levels = [0.0] * 60
        self.player = player
        self._cava_proc = None
        self._thread = None
        self._active = False
        self.start_cava()

    @pyqtProperty(list, notify=levelsChanged)
    def barLevels(self): 
        return self._levels

    def start_cava(self):
        cava_conf = Path.home() / ".config" / "music-standalone-app" / "cava.conf"
        cava_conf.parent.mkdir(parents=True, exist_ok=True)
        cava_conf.write_text("[general]\nbars = 60\n[output]\nmethod = raw\ndata_format = ascii\nascii_max_range = 100\n")

        try:
            self._cava_proc = subprocess.Popen(
                ["cava", "-p", str(cava_conf)],
                stdout=subprocess.PIPE,
                text=True
            )
            self._thread = threading.Thread(target=self._read_cava, daemon=True)
            self._thread.start()
        except FileNotFoundError:
            print("Cava не установлена!")

    def _read_cava(self):
        while True:
            if not self._cava_proc: break
            line = self._cava_proc.stdout.readline()
            if not line: break
            
            if self._active:
                try:
                    vals = [float(x) / 100.0 for x in line.strip().split(';') if x]
                    if len(vals) == 60:
                        self._levels = vals
                        self.levelsChanged.emit()
                except ValueError:
                    pass
            else:
                self._levels = [0.0] * 60
                self.levelsChanged.emit()

    @pyqtSlot()
    def registerConsumer(self): 
        self._active = True
        
    @pyqtSlot()
    def unregisterConsumer(self): 
        self._active = False

class MockSounds(QObject):
    def __init__(self, parent=None): super().__init__(parent)
    @pyqtSlot(str)
    def playSfx(self, val): pass

class MockI18n(QObject):
    def __init__(self, parent=None): super().__init__(parent)
    @pyqtSlot(str, result=str)
    @pyqtSlot(str, 'QVariantMap', result=str)
    def t(self, key, args=None):
        return key.split('.')[-1].capitalize()

class MockScaler(QObject):
    def __init__(self, parent=None): super().__init__(parent)
    @pyqtSlot(float, result=float)
    def s(self, val): return val

class MockCaching(QObject):
    changed = pyqtSignal()
    def __init__(self, parent=None): super().__init__(parent)
    @pyqtProperty(str, notify=changed)
    def qsDir(self): return str(Path(__file__).parent.absolute())

def replace_block(text, header, replacement):
    start = text.find(header)
    if start == -1: return text
    brace_count = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == '{': brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end = i
                break
    if end != -1:
        return text[:start] + replacement + text[end+1:]
    return text

def setup_app():
    BASE_DIR = Path(__file__).parent.absolute()
    
    # Перенаправляем запись UI-файлов во временную папку пользователя
    UI_DIR = Path.home() / ".cache" / "caelestia-equalizer" / "ui"
    MEDIA_DIR = BASE_DIR / "media"

    UI_DIR.mkdir(exist_ok=True, parents=True)

    music_qml_path = BASE_DIR / "ui" / "MusicPopup.qml"
    
    if music_qml_path.exists():
        qml_content = music_qml_path.read_text(encoding='utf-8')
        qml_content = re.sub(r'import Quickshell.*\n', '', qml_content)
        qml_content = re.sub(r'import "\.\./.*"\n', '', qml_content)
        qml_content = qml_content.replace('import Quickshell.Io', '')
        qml_content = qml_content.replace('import Quickshell', '')
        qml_content = re.sub(r'onMoved:\s*val\s*=>\s*\{', 'onMoved: { let val = value;', qml_content)
        qml_content = re.sub(r'onExited:\s*\(exitCode\)\s*=>\s*destroy\(\)', 'onExited: function(exitCode) { destroy(); }', qml_content)
        qml_content = replace_block(qml_content, "function execCmd(cmdStr) {", "function execCmd(cmdStr) { SysBridge.exec_cmd(cmdStr); }\n")
        (UI_DIR / "MusicPopup.qml").write_text(qml_content, encoding='utf-8')

    (UI_DIR / "StdioCollector.qml").write_text("import QtQuick\n\nQtObject {\n    property string text: \"\"\n    signal streamFinished()\n}\n")
    (UI_DIR / "Process.qml").write_text("import QtQuick\n\nItem {\n    property var command: []\n    property bool running: false\n    property var stdout: null\n    signal exited(int exitCode)\n    onRunningChanged: {\n        if(running) {\n            let res = SysBridge.exec_cmd_list(command);\n            if(stdout) { stdout.text = res; stdout.streamFinished(); }\n            running = false;\n            exited(0);\n        }\n    }\n}\n")
    # Просто копируем файлы, если они есть в папке ui
    for qml_file in ["ClickButton.qml", "IconButton.qml", "Dropdown.qml", "Draggable.qml"]:
        src_file = BASE_DIR / "ui" / qml_file
        if src_file.exists():
            shutil.copy(src_file, UI_DIR / qml_file)

    # Переписанный main.qml с контейнером для анимации
    (UI_DIR / "main.qml").write_text("""import QtQuick
import QtQuick.Window

Window {
    id: mainWindow
    visible: true
    width: 600
    height: 579
    minimumWidth: 600
    maximumWidth: 600
    minimumHeight: 579
    maximumHeight: 579
    color: "transparent" // Делаем само окно прозрачным
    title: "Standalone Music App"
    flags: Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    // Обертка, которая будет ездить вверх-вниз
    Item {
        id: mainPanel
        width: parent.width
        height: parent.height
        y: mainWindow.height // На старте прячем внизу

        // Фон интерфейса
        Rectangle {
            anchors.fill: parent
            color: ThemeBackend.base
            radius: ThemeBackend.borderRadius
        }

        // Твой контент
        MusicPopup {
            anchors.fill: parent
            anchors.margins: 10
        }

        // Анимация при запуске (вверх)
        NumberAnimation on y {
            to: 0
            duration: 400
            easing.type: Easing.OutBack
        }

        // Анимация при закрытии (вниз)
        NumberAnimation {
            id: closeAnim
            target: mainPanel
            property: "y"
            to: mainWindow.height
            duration: 300
            easing.type: Easing.InBack
            onFinished: Qt.quit() // Убиваем прогу, когда анимация закончилась
        }
    }

    // Эта функция вызывается из питона
    function closeApp() {
        closeAnim.start()
    }
}
""")

if __name__ == "__main__":
    pid_file = Path.home() / ".cache" / "caelestia-equalizer" / "app.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)

    if pid_file.exists():
        try:
            old_pid = int(pid_file.read_text().strip())
            os.kill(old_pid, 0)
            os.kill(old_pid, signal.SIGTERM) 
            sys.exit(0)
        except OSError:
            pid_file.unlink(missing_ok=True)

    pid_file.write_text(str(os.getpid()))

    try:
        setup_app()
        app = QGuiApplication(sys.argv)
        engine = QQmlApplicationEngine()

        BASE_DIR = Path(__file__).parent.absolute()
        CONFIG_DIR = Path.home() / ".config" / "music-standalone-app"

        pos_x_file = CONFIG_DIR / ".saved_pos_x"
        pos_y_file = CONFIG_DIR / ".saved_pos_y"
        x, y = 20, 60
        if pos_x_file.exists() and pos_y_file.exists():
            try:
                x = int(pos_x_file.read_text().strip())
                y = int(pos_y_file.read_text().strip())
            except Exception:
                pass

        lua_rule = f"hl.window_rule({{ match = {{ title = 'Standalone Music App' }}, move = {{ '{x}', '{y}' }} }})"
        subprocess.run(["hyprctl", "eval", lua_rule])

        sys_bridge = SysBridge(app)
        mock_mpris_ctrl = MockMprisController(app)
        mock_mpris = MockMpris(mock_mpris_ctrl, app)
        mock_theme = MockTheme(app)
        mock_cava = RealCava(mock_mpris_ctrl.activePlayer, app) # Исправлено на RealCava
        mock_sounds = MockSounds(app)
        mock_i18n = MockI18n(app)
        mock_scaler = MockScaler(app)
        mock_caching = MockCaching(app)

        mpris_timer = QTimer(app)
        mpris_timer.timeout.connect(mock_mpris_ctrl.activePlayer.fetch_data)
        mpris_timer.start(1000)

        # cava_timer полностью удаляем, так как RealCava работает в отдельном потоке

        save_timer = QTimer(app)
        save_timer.timeout.connect(sys_bridge.save_hyprland_position)
        save_timer.start(2000)

        engine.rootContext().setContextProperty("SysBridge", sys_bridge)
        engine.rootContext().setContextProperty("MprisController", mock_mpris_ctrl)
        engine.rootContext().setContextProperty("Mpris", mock_mpris)
        engine.rootContext().setContextProperty("ThemeBackend", mock_theme)
        engine.rootContext().setContextProperty("Cava", mock_cava)
        engine.rootContext().setContextProperty("Sounds", mock_sounds)
        engine.rootContext().setContextProperty("I18n", mock_i18n)
        engine.rootContext().setContextProperty("Scaler", mock_scaler)
        engine.rootContext().setContextProperty("Caching", mock_caching)

        qml_file = Path.home() / ".cache" / "caelestia-equalizer" / "ui" / "main.qml"
        engine.load(QUrl.fromLocalFile(str(qml_file)))

        if not engine.rootObjects():
            sys.exit(-1)

        # Функция для активации QML-анимации
        def trigger_qml_close():
            root_obj = engine.rootObjects()[0]
            QMetaObject.invokeMethod(root_obj, "closeApp")

        # Обработчик сигнала
        def sigterm_handler(signum, frame):
            QTimer.singleShot(0, trigger_qml_close)

        signal.signal(signal.SIGTERM, sigterm_handler)

        # Чтобы питон не спал и мог перехватывать системные сигналы
        sig_timer = QTimer(app)
        sig_timer.timeout.connect(lambda: None)
        sig_timer.start(200)

        sys.exit(app.exec())
        
    finally:
        if pid_file.exists():
            pid_file.unlink(missing_ok=True)
