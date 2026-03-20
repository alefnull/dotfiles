// Bar.qml
import Quickshell

Scope {
  Variants {
    model: Quickshell.screens

    PanelWindow {
      required property var modelData
      screen: modelData

      anchors {
        top: true
        left: true
        right: true
      }

      implicitHeight: 30

      WorkspaceWidget {
        anchors.centerIn: parent
      }
      // ClockWidget {
      //   anchors.centerIn: parent
      // }
    }
  }
}
