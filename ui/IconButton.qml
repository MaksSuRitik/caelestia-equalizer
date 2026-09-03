import QtQuick
import QtQuick.Controls

Button {
    id: control
    property string buttonIcon: ""
    property real iconFontSize: 16
    property color accentColor: ThemeBackend.surface0 || "#313244"
    property color textColor: ThemeBackend.text || "#cdd6f4"
    property real cornerRadius: 8
    property real iconOffsetY: 0
    property bool isHoveredOrHighlighted: control.hovered || control.pressed

    implicitWidth: 38
    implicitHeight: 38

    background: Rectangle {
        color: control.pressed ? Qt.darker(accentColor, 1.2) : (control.hovered ? Qt.lighter(accentColor, 1.2) : accentColor)
        radius: cornerRadius
        Behavior on color { ColorAnimation { duration: 150 } }
    }
    contentItem: Text {
        text: control.buttonIcon
        color: control.textColor
        font.pixelSize: control.iconFontSize
        font.family: ThemeBackend.fontFamily
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        y: control.iconOffsetY
        Behavior on color { ColorAnimation { duration: 150 } }
    }
}
