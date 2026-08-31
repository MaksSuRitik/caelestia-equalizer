import os
import sys
import shutil
import subprocess
import re
import random
import json
from pathlib import Path
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QObject, pyqtSlot, pyqtProperty, QUrl, pyqtSignal, QTimer

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

class MockCava(QObject):
    levelsChanged = pyqtSignal()
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self._levels = [0.0]*60
        self.player = player

    @pyqtProperty(list, notify=levelsChanged)
    def barLevels(self): return self._levels

    def update_fake_cava(self):
        if self.player.isPlaying:
            self._levels = [random.uniform(0.01, 0.95) for _ in range(60)]
        else:
            self._levels = [0.0] * 60
        self.levelsChanged.emit()

    @pyqtSlot()
    def registerConsumer(self): pass
    @pyqtSlot()
    def unregisterConsumer(self): pass

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
    
    # ИСПРАВЛЕНИЕ: Перенаправляем запись UI-файлов во временную папку пользователя, 
    # так как /доступная по умолчанию /usrдоступна только для чтения!
    UI_DIR = Path.home() / ".cache" / "caelestia-equalizer" / "ui"
    MEDIA_DIR = BASE_DIR / "media" # Медиа оставляем как есть (они читаются из пакета)

    # Убеждаемся, что пользовательская папка для UI существует
    UI_DIR.mkdir(exist_ok=True, parents=True)

    # Путь к исходному MusicPopup.qml берем из системной директории пакета (BASE_DIR)
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

    # Обязательные заглушки для QML компонентов (теперь запишутся в ~/.cache/...)
    (UI_DIR / "StdioCollector.qml").write_text("import QtQuick\n\nQtObject {\n    property string text: \"\"\n    signal streamFinished()\n}\n")
    (UI_DIR / "Process.qml").write_text("import QtQuick\n\nItem {\n    property var command: []\n    property bool running: false\n    property var stdout: null\n    signal exited(int exitCode)\n    onRunningChanged: {\n        if(running) {\n            let res = SysBridge.exec_cmd_list(command);\n            if(stdout) { stdout.text = res; stdout.streamFinished(); }\n            running = false;\n            exited(0);\n        }\n    }\n}\n")
    (UI_DIR / "ClickButton.qml").write_text("import QtQuick\nimport QtQuick.Controls\n\nButton {\n    property string buttonText: \"Btn\"\n    property real textFontSize: 12\n    property color accentColor: \"#555\"\n    property color textColor: \"white\"\n    property real cornerRadius: 4\n    property bool isHoveredOrHighlighted: hovered || pressed\n    text: buttonText\n    background: Rectangle {\n        color: accentColor\n        radius: cornerRadius\n    }\n    contentItem: Text {\n        text: parent.text\n        color: textColor\n        font.pixelSize: textFontSize\n        horizontalAlignment: Text.AlignHCenter\n        verticalAlignment: Text.AlignVCenter\n    }\n}\n")
    (UI_DIR / "IconButton.qml").write_text("import QtQuick\nimport QtQuick.Controls\n\nButton {\n    property string buttonIcon: \"X\"\n    property real iconFontSize: 12\n    property color accentColor: \"#555\"\n    property color textColor: \"white\"\n    property real cornerRadius: 4\n    property real iconOffsetY: 0\n    property bool isHoveredOrHighlighted: hovered || pressed\n    text: buttonIcon\n    background: Rectangle {\n        color: accentColor\n        radius: cornerRadius\n    }\n    contentItem: Text {\n        text: parent.text\n        color: textColor\n        font.pixelSize: iconFontSize\n        horizontalAlignment: Text.AlignHCenter\n        verticalAlignment: Text.AlignVCenter\n        y: iconOffsetY\n    }\n}\n")
    (UI_DIR / "Dropdown.qml").write_text("import QtQuick\nimport QtQuick.Controls\n\nComboBox {\n    property real fontPixelSize: 12\n    property real iconSize: 12\n    property color accentColor: \"gray\"\n    property color baseColor: \"black\"\n    property color hoverColor: \"gray\"\n    property color dropdownColor: \"black\"\n    property color borderColor: \"gray\"\n    property color textColor: \"white\"\n    property color activeTextColor: \"white\"\n    property real cornerRadius: 5\n    property var options: []\n    model: options\n    signal valueChanged(int index, string value)\n    onActivated: function(index) {\n        valueChanged(index, textAt(index))\n    }\n}\n")
    (UI_DIR / "Draggable.qml").write_text("import QtQuick\nimport QtQuick.Controls\n\nSlider {\n    property color backgroundColor: \"gray\"\n    property color accentColor: \"blue\"\n    property color gradColor1: \"blue\"\n    property color gradColor2: "cyan"\n    property color gradColor3: \"cyan\"\n    property real cornerRadius: 5\n    property real handleSize: 10\n    property color handleColor: \"white\"\n    property color handleHoverColor: \"white\"\n    property color handleDragColor: \"white\"\n    property color handleBorderColor: \"black\"\n    property bool showValueBubble: false\n    property bool showTooltip: false\n    property var valueFormatter: function(v) { return v; }\n    property bool isDragging: pressed\n}\n")

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
    color: ThemeBackend.base
    title: "Standalone Music App"
    flags: Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    MusicPopup {
        anchors.fill: parent
        anchors.margins: 10
    }
}
""")

if __name__ == "__main__":
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
    mock_cava = MockCava(mock_mpris_ctrl.activePlayer, app)
    mock_sounds = MockSounds(app)
    mock_i18n = MockI18n(app)
    mock_scaler = MockScaler(app)
    mock_caching = MockCaching(app)

    mpris_timer = QTimer(app)
    mpris_timer.timeout.connect(mock_mpris_ctrl.activePlayer.fetch_data)
    mpris_timer.start(1000)

    cava_timer = QTimer(app)
    cava_timer.timeout.connect(mock_cava.update_fake_cava)
    cava_timer.start(60)

    # Таймер теперь корректно привязывается к заголовку окна и следит за ним
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

    qml_file = BASE_DIR / "ui" / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
