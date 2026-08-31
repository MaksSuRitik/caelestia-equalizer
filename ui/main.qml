import QtQuick
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
