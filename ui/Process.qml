import QtQuick

Item {
    property var command: []
    property bool running: false
    property var stdout: null
    signal exited(int exitCode)
    onRunningChanged: {
        if(running) {
            let res = SysBridge.exec_cmd_list(command);
            if(stdout) { stdout.text = res; stdout.streamFinished(); }
            running = false;
            exited(0);
        }
    }
}
