import QtQuick
import QtQuick.Controls

Button {
    property string buttonIcon: "X"
    property real iconFontSize: 12
    property color accentColor: "#555"
    property color textColor: "white"
    property real cornerRadius: 4
    property real iconOffsetY: 0
    property bool isHoveredOrHighlighted: hovered || pressed
    text: buttonIcon
    background: Rectangle {
        color: accentColor
        radius: cornerRadius
    }
    contentItem: Text {
        text: parent.text
        color: textColor
        font.pixelSize: iconFontSize
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        y: iconOffsetY
    }
}
