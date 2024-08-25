import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import Qt5Compat.GraphicalEffects
import "./components" as Components

Item {
    anchors.fill: parent

    Item {
        id: backgroundContainer
        anchors.fill: parent

        Image {
            id: backgroundImage
            anchors.fill: parent
            source: renamer ? renamer.cover_image : ""
            fillMode: Image.PreserveAspectCrop
            cache: false
            asynchronous: true
            smooth: true
            mipmap: true

            onStatusChanged: {
                if (status === Image.Ready) {
                    scaleAnimator.start()
                }
            }

            ScaleAnimator {
                id: scaleAnimator
                target: backgroundImage
                from: 1.1
                to: 1.0
                duration: 1000
                easing.type: Easing.OutQuad
            }
        }

        FastBlur {
            anchors.fill: backgroundImage
            source: backgroundImage
            radius: 100
        }

        Rectangle {
            anchors.fill: parent
            color: coverColorAnalyzer.backgroundColor
            opacity: 0.7
        }
    }

    ScrollView {
        id: scrollView
        anchors.fill: parent
        contentWidth: availableWidth

        Item {
            width: scrollView.width
            height: childrenRect.height

            ColumnLayout {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 20
                spacing: 20

                Image {
                    id: coverImage
                    Layout.alignment: Qt.AlignHCenter
                    source: renamer ? renamer.cover_image : ""
                    Layout.preferredWidth: Math.min(scrollView.width - 40, 300)
                    Layout.preferredHeight: Layout.preferredWidth
                    fillMode: Image.PreserveAspectFit

                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.color: coverColorAnalyzer.dominantColor
                        border.width: 2
                        radius: 10
                        visible: coverImage.status !== Image.Ready
                    }

                    Text {
                        anchors.centerIn: parent
                        text: "No cover image"
                        visible: coverImage.status !== Image.Ready
                        color: coverColorAnalyzer.textColor
                    }
                }

                ComboBox {
                    id: albumComboBox
                    Layout.fillWidth: true
                    model: ["Bunny Girl Senpai", "Dreaming Girl", "Sister Venturing Out", "Knapsack Kid"]
                    onCurrentTextChanged: {
                        coverColorAnalyzer.setColors(currentText)
                        renamer.set_current_album(currentText)
                    }

                    background: Rectangle {
                        implicitWidth: 120
                        implicitHeight: 40
                        color: coverColorAnalyzer.backgroundColor
                        border.color: coverColorAnalyzer.dominantColor
                        border.width: 1
                        radius: 5
                    }

                    contentItem: Text {
                        leftPadding: 10
                        rightPadding: albumComboBox.indicator.width + albumComboBox.spacing
                        text: albumComboBox.displayText
                        font: albumComboBox.font
                        color: coverColorAnalyzer.textColor
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }

                    popup: Popup {
                        y: -contentItem.height
                        width: albumComboBox.width
                        implicitHeight: contentItem.implicitHeight
                        padding: 1

                        contentItem: ListView {
                            clip: true
                            implicitHeight: contentHeight
                            model: albumComboBox.popup.visible ? albumComboBox.delegateModel : null
                            currentIndex: albumComboBox.highlightedIndex
                            interactive: false

                            highlight: Rectangle {
                                color: coverColorAnalyzer.accentColor
                            }
                        }

                        background: Rectangle {
                            color: coverColorAnalyzer.backgroundColor
                            border.color: coverColorAnalyzer.dominantColor
                            radius: 5
                        }
                    }

                    delegate: ItemDelegate {
                        width: albumComboBox.width
                        height: albumComboBox.height
                        contentItem: Text {
                            text: modelData
                            color: coverColorAnalyzer.textColor
                            font: albumComboBox.font
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }
                        highlighted: albumComboBox.highlightedIndex === index
                    }
                }

                ComboBox {
                    id: languageComboBox
                    Layout.fillWidth: true
                    model: ["Japanese", "Romaji", "English"]
                    onCurrentTextChanged: renamer.set_current_language(currentText)

                    background: Rectangle {
                        implicitWidth: 120
                        implicitHeight: 40
                        color: coverColorAnalyzer.backgroundColor
                        border.color: coverColorAnalyzer.dominantColor
                        border.width: 1
                        radius: 5
                    }

                    contentItem: Text {
                        leftPadding: 10
                        rightPadding: languageComboBox.indicator.width + languageComboBox.spacing
                        text: languageComboBox.displayText
                        font: languageComboBox.font
                        color: coverColorAnalyzer.textColor
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }

                    popup: Popup {
                        y: -contentItem.height
                        width: languageComboBox.width
                        implicitHeight: contentItem.implicitHeight
                        padding: 1

                        contentItem: ListView {
                            clip: true
                            implicitHeight: contentHeight
                            model: languageComboBox.popup.visible ? languageComboBox.delegateModel : null
                            currentIndex: languageComboBox.highlightedIndex
                            interactive: false

                            highlight: Rectangle {
                                color: coverColorAnalyzer.accentColor
                            }
                        }

                        background: Rectangle {
                            color: coverColorAnalyzer.backgroundColor
                            border.color: coverColorAnalyzer.dominantColor
                            radius: 5
                        }
                    }

                    delegate: ItemDelegate {
                        width: languageComboBox.width
                        height: languageComboBox.height
                        contentItem: Text {
                            text: modelData
                            color: coverColorAnalyzer.textColor
                            font: languageComboBox.font
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }
                        highlighted: languageComboBox.highlightedIndex === index
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Button {
                        id: actionButton
                        Layout.fillWidth: true
                        text: renamer.get_current_album_state() === "extract" ? "Extract Soundtrack" : "Rename Files"
                        onClicked: {
                            if (renamer.get_current_album_state() === "extract") {
                                renamer.extract_soundtrack(albumComboBox.currentText)
                            } else {
                                var result = renamer.rename_files()
                                resultText.text = result
                                resultText.color = result.startsWith("Error:") ? "red" : coverColorAnalyzer.textColor
                                resultDialog.open()
                            }
                        }
                        enabled: renamer.can_extract()

                        contentItem: Text {
                            text: parent.text
                            font: parent.font
                            opacity: enabled ? 1.0 : 0.3
                            color: coverColorAnalyzer.textColor
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }

                        background: Rectangle {
                            implicitWidth: 100
                            implicitHeight: 40
                            opacity: enabled ? 1 : 0.3
                            color: parent.down ? Qt.darker(coverColorAnalyzer.dominantColor, 1.1) : coverColorAnalyzer.dominantColor
                            radius: 5
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Rectangle {
                            id: outputFolderContainer
                            Layout.fillWidth: true
                            height: 40
                            color: coverColorAnalyzer.backgroundColor
                            border.color: coverColorAnalyzer.dominantColor
                            border.width: 1
                            radius: 5

                            Text {
                                id: placeholderText
                                anchors.left: parent.left
                                anchors.leftMargin: 10
                                anchors.verticalCenter: parent.verticalCenter
                                text: "Choose a folder"
                                color: coverColorAnalyzer.textColor
                                opacity: 0.5
                                visible: !outputFolderText.text
                            }

                            Text {
                                id: outputFolderText
                                anchors.fill: parent
                                anchors.margins: 10
                                verticalAlignment: Text.AlignVCenter
                                text: renamer.output_folder
                                color: coverColorAnalyzer.textColor
                                elide: Text.ElideMiddle
                            }
                        }

                        Button {
                            text: "Browse"
                            onClicked: folderExplorer.open()

                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                opacity: enabled ? 1.0 : 0.3
                                color: coverColorAnalyzer.textColor
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }

                            background: Rectangle {
                                implicitWidth: 100
                                implicitHeight: 40
                                opacity: enabled ? 1 : 0.3
                                color: parent.down ? Qt.darker(coverColorAnalyzer.dominantColor, 1.1) : coverColorAnalyzer.dominantColor
                                radius: 5
                            }
                        }
                    }

                    Text {
                        text: "Choose the base folder where the soundtracks are located"
                        font.italic: true
                        color: Material.accent
                    }

                    Components.FolderExplorer {
                        id: folderExplorer
                        Layout.fillWidth: true
                        Layout.preferredHeight: 500

                        Component.onCompleted: {
                            folderExplorer.setRenamer(renamer)
                        }

                        onFolderSelected: function(folder) {
                            renamer.set_output_folder(folder)
                            outputFolderText.text = folder
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: resultDialog
        title: {
            if (resultText.text.startsWith("Error:")) {
                return "Operation Failed"
            } else if (resultText.text.includes("extracted")) {
                return "Extraction Complete"
            } else {
                return "Renaming Complete"
            }
        }
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        width: 300
        height: 200
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        background: Rectangle {
            color: coverColorAnalyzer.backgroundColor
            border.color: coverColorAnalyzer.dominantColor
            border.width: 2
            radius: 10
        }

        header: Rectangle {
            width: parent.width
            height: 40
            color: coverColorAnalyzer.dominantColor
            radius: 8

            Text {
                anchors.centerIn: parent
                text: resultDialog.title
                color: coverColorAnalyzer.textColor
                font.bold: true
            }
        }

        contentItem: Text {
            id: resultText
            color: coverColorAnalyzer.textColor
            wrapMode: Text.WordWrap
            elide: Text.ElideRight
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            padding: 10
        }

        footer: Item {
            height: 50
            Button {
                anchors.centerIn: parent
                text: "OK"
                onClicked: resultDialog.accept()
                contentItem: Text {
                    text: parent.text
                    color: coverColorAnalyzer.textColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    implicitWidth: 80
                    implicitHeight: 30
                    color: coverColorAnalyzer.dominantColor
                    radius: 5
                    opacity: parent.down ? 0.8 : 1
                }
            }
        }
    }

    Connections {
        target: renamer
        function onExtractionFinished(result) {
            resultText.text = result
            resultText.color = result.startsWith("Error:") ? "red" : coverColorAnalyzer.textColor
            resultDialog.open()
        }
        function onAlbumStateChanged() {
            actionButton.text = renamer.get_current_album_state() === "extract" ? "Extract Soundtrack" : "Rename Files"
        }
        function onCanExtractChanged() {
            actionButton.enabled = renamer.can_extract()
        }
    }
}