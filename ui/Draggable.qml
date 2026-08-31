import QtQuick
import QtQuick.Controls

Slider {
    property color backgroundColor: "gray"
    property color accentColor: "blue"
    property color gradColor1: "blue"
    property color gradColor2: "cyan"
    property color gradColor3: "cyan"
    property real cornerRadius: 5
    property real handleSize: 10
    property color handleColor: "white"
    property color handleHoverColor: "white"
    property color handleDragColor: "white"
    property color handleBorderColor: "black"
    property bool showValueBubble: false
    property bool showTooltip: false
    property var valueFormatter: function(v) { return v; }
    property bool isDragging: pressed
}
