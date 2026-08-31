import QtQuick
import QtQuick.Controls

Button {
    property string buttonText: "Btn"
    property real textFontSize: 12
    property color accentColor: "#555"
    property color textColor: "white"
    property real cornerRadius: 4
    property bool isHoveredOrHighlighted: hovered || pressed
    text: buttonText
    background: Rectangle {
        color: accentColor
        radius: cornerRadius
    }
    contentItem: Text {
        text: parent.text
        color: textColor
        font.pixelSize: textFontSize
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
