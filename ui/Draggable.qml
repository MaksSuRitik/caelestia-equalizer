import QtQuick
import QtQuick.Controls

Slider {
    id: control
    property color backgroundColor: ThemeBackend.surface0 || "#313244"
    property color accentColor: ThemeBackend.mauve || "#cba6f7"
    property color gradColor1: ThemeBackend.blue || "#89b4fa"
    property color gradColor2: ThemeBackend.mauve || "#cba6f7"
    property color gradColor3: ThemeBackend.mauve || "#cba6f7"
    property real cornerRadius: 8
    property real handleSize: 18
    property color handleColor: ThemeBackend.text || "#cdd6f4"
    property color handleHoverColor: Qt.lighter(accentColor, 1.15)
    property color handleDragColor: Qt.lighter(accentColor, 1.30)
    property color handleBorderColor: "transparent"
    property bool showValueBubble: false
    property bool showTooltip: false
    property var valueFormatter: function(v) { return v; }
    property bool isDragging: control.pressed

    background: Rectangle {
        x: control.leftPadding
        y: control.topPadding + control.availableHeight / 2 - height / 2
        implicitWidth: 200
        implicitHeight: 10
        width: control.availableWidth
        height: implicitHeight
        radius: cornerRadius
        color: control.backgroundColor

        Rectangle {
            width: control.visualPosition * parent.width
            height: parent.height
            color: control.accentColor
            radius: control.cornerRadius
        }
    }

    handle: Rectangle {
        x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
        y: control.topPadding + control.availableHeight / 2 - height / 2
        implicitWidth: control.handleSize
        implicitHeight: control.handleSize
        radius: control.handleSize / 2
        color: control.pressed ? control.handleDragColor : (control.hovered ? control.handleHoverColor : control.handleColor)
        scale: control.pressed ? 1.25 : (control.hovered ? 1.15 : 1.0)
        Behavior on scale { NumberAnimation { duration: 120 } }
        Behavior on color { ColorAnimation { duration: 120 } }
    }
}
