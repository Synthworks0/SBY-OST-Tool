import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

Item {
    id: root
    property bool isOpen: false
    property var _renamer: null
    property string currentPath: ""

    signal folderSelected(string folder)

    function setRenamer(renamer) {
        _renamer = renamer
    }

    function open() {
        isOpen = true
        currentPath = ""
        _renamer.set_current_path("")
    }

    function close() {
        isOpen = false
    }

    Rectangle {
        anchors.fill: parent
        color: Material.background
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
                    color: Material.foreground
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
                            color: Material.accent
                            radius: 4

                            Text {
                                anchors.centerIn: parent
                                text: "F"
                                color: Material.foreground
                            }
                        }

                        Label {
                            text: modelData.name
                            color: Material.foreground
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
                    placeholderText: "New folder name"
                }

                Button {
                    text: "New Folder"
                    enabled: currentPath !== "" && newFolderName.text.trim() !== ""
                    onClicked: {
                        if (_renamer.create_new_folder(currentPath, newFolderName.text.trim())) {
                            var newFolderPath = _renamer.join_paths(currentPath, newFolderName.text.trim())
                            currentPath = newFolderPath
                            _renamer.set_current_path(newFolderPath)
                            newFolderName.text = ""
                        }
                    }
                    Material.background: Material.accent
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.margins: 10

                Button {
                    text: "Back"
                    enabled: currentPath !== ""
                    onClicked: {
                        var parentDir = _renamer.get_parent_directory(currentPath)
                        currentPath = parentDir
                        _renamer.set_current_path(parentDir)
                    }
                    Material.background: Material.accent
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "Select"
                    enabled: currentPath !== ""
                    onClicked: {
                        folderSelected(currentPath)
                        root.close()
                    }
                    Material.background: Material.accent
                }

                Button {
                    text: "Cancel"
                    onClicked: root.close()
                    Material.background: Material.accent
                }
            }
        }
    }
}