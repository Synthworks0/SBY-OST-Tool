import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

Item {
    id: root
    property bool isOpen: false
    property var _renamer: null
    property string currentPath: ""
    property color backgroundColor
    property color textColor
    property color accentColor
    property bool isExtras: false

    signal folderSelected(string folder)

    function setRenamer(renamer) {
        _renamer = renamer
    }

    signal opened()
    signal closed()
    signal requestScroll()

    function open() {
        isOpen = true
        currentPath = ""
        _renamer.set_current_path("")
        opened()
    }

    function close() {
        if (isOpen) {
            isOpen = false
            // Ask parent to handle scrolling animation
            Qt.callLater(requestScroll)
            closed()
        }
    }

    function getContrastColor(color) {
        var r = color.r * 255;
        var g = color.g * 255;
        var b = color.b * 255;
        var yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
        return (yiq >= 128) ? "black" : "white";
    }

    function adjustBrightness(color, amount) {
        var r = color.r * 255;
        var g = color.g * 255;
        var b = color.b * 255;

        r = Math.max(0, Math.min(255, r + amount));
        g = Math.max(0, Math.min(255, g + amount));
        b = Math.max(0, Math.min(255, b + amount));

        return Qt.rgba(r / 255, g / 255, b / 255, color.a);
    }

    function adjustColorForContrast(color) {
        if (!isExtras) return color;
        var r = color.r * 255;
        var g = color.g * 255;
        var b = color.b * 255;
        var luminance = (0.299 * r + 0.587 * g + 0.114 * b);
        var adjustment = luminance > 186 ? -50 : 50;
        return adjustBrightness(color, adjustment);
    }

    Rectangle {
        anchors.fill: parent
        color: adjustColorForContrast(root.backgroundColor)
        opacity: 0.9
        visible: root.isOpen

        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                Layout.margins: 10

                Label {
                    text: currentPath || "Select Folder"
                    color: isExtras ? getContrastColor(root.backgroundColor) : root.textColor
                    font.pixelSize: 14
                    Layout.fillWidth: true
                    elide: Text.ElideMiddle
                }
            }

            ListView {
                id: folderListView
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: _renamer ? _renamer.folder_contents : []

                delegate: ItemDelegate {
                    width: folderListView.width
                    height: 40

                    contentItem: RowLayout {
                        spacing: 10

                        Rectangle {
                            width: 24
                            height: 24
                            color: adjustColorForContrast(root.accentColor)
                            radius: 4

                            Text {
                                anchors.centerIn: parent
                                text: "F"
                                color: getContrastColor(parent.color)
                            }
                        }

                        Label {
                            text: modelData.name
                            color: isExtras ? getContrastColor(root.backgroundColor) : root.textColor
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                    }

                    highlighted: ListView.isCurrentItem

                    onClicked: {
                        if (modelData.isDir) {
                            currentPath = modelData.path
                            _renamer.set_current_path(modelData.path)
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.margins: 10

                TextField {
                    id: newFolderName
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    placeholderText: "New folder name"
                    placeholderTextColor: getContrastColor(root.backgroundColor)
                    color: root.textColor
                    background: Rectangle {
                        color: adjustColorForContrast(root.backgroundColor)
                        border.color: root.accentColor
                        border.width: 1
                        radius: 4
                    }
                }

                Button {
                    text: "New Folder"
                    Layout.preferredHeight: 50
                    enabled: currentPath !== "" && newFolderName.text.trim() !== ""
                    onClicked: {
                        if (_renamer.create_new_folder(currentPath, newFolderName.text.trim())) {
                            var newFolderPath = _renamer.join_paths(currentPath, newFolderName.text.trim())
                            currentPath = newFolderPath
                            _renamer.set_current_path(newFolderPath)
                            newFolderName.text = ""
                        }
                    }
                    background: Rectangle {
                        color: parent.enabled ? adjustColorForContrast(root.accentColor) : Qt.darker(adjustColorForContrast(root.accentColor), 1.5)
                        radius: 4
                    }
                    contentItem: Text {
                        text: parent.text
                        color: isExtras ? "black" : getContrastColor(parent.background.color)
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.margins: 10

                Button {
                    text: "Back"
                    Layout.preferredHeight: 44
                    enabled: currentPath !== ""
                    onClicked: {
                        var parentDir = _renamer.get_parent_directory(currentPath)
                        currentPath = parentDir
                        _renamer.set_current_path(parentDir)
                    }
                    background: Rectangle {
                        color: parent.enabled ? adjustColorForContrast(root.accentColor) : Qt.darker(adjustColorForContrast(root.accentColor), 1.5)
                        radius: 4
                    }
                    contentItem: Text {
                        text: parent.text
                        color: isExtras ? "black" : getContrastColor(parent.background.color)
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "Select"
                    Layout.preferredHeight: 44
                    enabled: currentPath !== ""
                    onClicked: {
                        folderSelected(currentPath)
                        root.close()
                    }
                    background: Rectangle {
                        color: parent.enabled ? adjustColorForContrast(root.accentColor) : Qt.darker(adjustColorForContrast(root.accentColor), 1.5)
                        radius: 4
                    }
                    contentItem: Text {
                        text: parent.text
                        color: isExtras ? "black" : getContrastColor(parent.background.color)
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Button {
                    text: "Cancel"
                    Layout.preferredHeight: 44
                    onClicked: root.close()
                    background: Rectangle {
                        color: adjustColorForContrast(root.accentColor)
                        radius: 4
                    }
                    contentItem: Text {
                        text: parent.text
                        color: isExtras ? "black" : getContrastColor(parent.background.color)
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }
}
