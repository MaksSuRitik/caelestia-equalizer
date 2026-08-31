import QtQuick
import QtQuick.Controls

ComboBox {
    property real fontPixelSize: 12
    property real iconSize: 12
    property color accentColor: "gray"
    property color baseColor: "black"
    property color hoverColor: "gray"
    property color dropdownColor: "black"
    property color borderColor: "gray"
    property color textColor: "white"
    property color activeTextColor: "white"
    property real cornerRadius: 5
    property var options: []
    model: options
    signal valueChanged(int index, string value)
    onActivated: function(index) {
        valueChanged(index, textAt(index))
    }
}
