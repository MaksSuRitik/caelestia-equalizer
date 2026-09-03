import QtQuick
import QtQuick.Controls

Button {
    id: control
    property string buttonText: ""
    property real textFontSize: 12
    property color accentColor: ThemeBackend.surface0 || "#313244"
    property color textColor: ThemeBackend.text || "#cdd6f4"
    property real cornerRadius: 8
    property bool isHoveredOrHighlighted: control.hovered || control.pressed

    // Убрали "property real", просто задаем значение встроенному свойству:
    horizontalPadding: 12

    implicitWidth: contentItem.implicitWidth + (horizontalPadding * 2)
    implicitHeight: 32

    background: Rectangle {
        color: control.pressed ? Qt.darker(accentColor, 1.2) : (control.hovered ? Qt.lighter(accentColor, 1.2) : accentColor)
        radius: cornerRadius
        Behavior on color { ColorAnimation { duration: 150 } }
    }
    contentItem: Text {
        text: control.buttonText
        color: control.textColor
        font.pixelSize: control.textFontSize
        font.family: ThemeBackend.fontFamily
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        Behavior on color { ColorAnimation { duration: 150 } }
    }
}
