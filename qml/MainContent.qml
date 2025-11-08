import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import Qt5Compat.GraphicalEffects
import "./components" as Components

// To anyone trying to read this. I apologize.

Item {
    id: root
    anchors.fill: parent

    MouseArea {
        anchors.fill: parent
        propagateComposedEvents: true
        onPressed: function(mouse) {
            if (outputFolderText && outputFolderText.activeFocus) {
                outputFolderText.focus = false
            }
            mouse.accepted = false
        }
    }

    // Fallback to avoid undefined access during loading
    property var coverColorAnalyzer: ({
        dominantColor: "#5cc4f1",
        backgroundColor: "#182f74",
        accentColor: "#063c94",
        textColor: "#ffffff",
        extraColors: ["#e5eef3", "#f8f4c4", "#ecd4e2", "#d5ebdc", "#fbd3c9", "#fcfcf4"],
        setColors: function(album) {}
    })

    property int colorIndex: 0
    property color currentColor: coverColorAnalyzer.extraColors[colorIndex]
    property color nextColor: coverColorAnalyzer.extraColors[(colorIndex + 1) % coverColorAnalyzer.extraColors.length]
    property real colorProgress: 0
    property bool isExtras: albumComboBox.currentText === "Extras"
    readonly property bool isRemote: renamer ? renamer.is_remote_enabled : false

    function getContrastColor(color) {
        var r = color.r * 255;
        var g = color.g * 255;
        var b = color.b * 255;
        var luminance = (0.299 * r + 0.587 * g + 0.114 * b);
        return luminance > 186 ? "#000000" : "#FFFFFF";
    }

    function lerpColor(color1, color2, t) {
        var r1 = parseInt(color1.toString().substr(1, 2), 16);
        var g1 = parseInt(color1.toString().substr(3, 2), 16);
        var b1 = parseInt(color1.toString().substr(5, 2), 16);
        var r2 = parseInt(color2.toString().substr(1, 2), 16);
        var g2 = parseInt(color2.toString().substr(3, 2), 16);
        var b2 = parseInt(color2.toString().substr(5, 2), 16);

        var r = Math.round(r1 + (r2 - r1) * t);
        var g = Math.round(g1 + (g2 - g1) * t);
        var b = Math.round(b1 + (b2 - b1) * t);

        return Qt.rgba(r / 255, g / 255, b / 255, 1);
    }

    function adjustBrightness(color, amount) {
        var r = parseInt(color.toString().substr(1, 2), 16);
        var g = parseInt(color.toString().substr(3, 2), 16);
        var b = parseInt(color.toString().substr(5, 2), 16);

        r = Math.max(0, Math.min(255, r + amount));
        g = Math.max(0, Math.min(255, g + amount));
        b = Math.max(0, Math.min(255, b + amount));

        return Qt.rgba(r / 255, g / 255, b / 255, 1);
    }

    function getRandomColor() {
        var baseColor = coverColorAnalyzer.extraColors[Math.floor(Math.random() * coverColorAnalyzer.extraColors.length)];
        var brightnessAdjustment = Math.floor(Math.random() * 41) - 20;
        return adjustBrightness(baseColor, brightnessAdjustment);
    }

    Timer {
        id: colorTimer
        interval: 50
        running: isExtras
        repeat: true
        onTriggered: {
            colorProgress += 0.02
            if (colorProgress >= 1) {
                colorProgress = 0
                currentColor = nextColor
                nextColor = getRandomColor()
                while (Qt.colorEqual(nextColor, currentColor)) {
                    nextColor = getRandomColor()
                }
            }
            root.Material.accent = lerpColor(currentColor, nextColor, colorProgress)
            root.Material.background = adjustBrightness(lerpColor(currentColor, nextColor, colorProgress), -20)
        }
    }

    Item {
        id: backgroundContainer
        anchors.fill: parent

        Image {
            id: backgroundImage
            anchors.fill: parent
            source: renamer ? renamer.cover_image : ""
            fillMode: Image.PreserveAspectCrop
            cache: true
            asynchronous: true
            smooth: true
            mipmap: true
            antialiasing: true
            sourceSize: Qt.size(1200, 1200)
            layer.enabled: true
            layer.smooth: true

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
            color: albumComboBox.currentText === "Extras"
                ? lerpColor(currentColor, nextColor, colorProgress)
                : coverColorAnalyzer.backgroundColor
            opacity: 0.7
        }
    }

    Item {
        id: remoteProgressBackdrop
        anchors.fill: parent
        z: 999
        opacity: remoteProgressDialog.visible ? 1 : 0
        Behavior on opacity {
            NumberAnimation { duration: 200 }
        }

        readonly property color overlayColor: albumComboBox.currentText === "Extras"
            ? lerpColor(currentColor, nextColor, colorProgress)
            : coverColorAnalyzer.backgroundColor

        ShaderEffectSource {
            id: remoteBlurSource
            anchors.fill: parent
            sourceItem: backgroundContainer
            smooth: true
            recursive: true
            live: remoteProgressDialog.visible
            visible: remoteProgressDialog.visible
        }

        FastBlur {
            anchors.fill: parent
            source: remoteBlurSource
            radius: 64
            transparentBorder: true
            visible: remoteProgressDialog.visible
        }

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0; color: Qt.rgba(remoteProgressBackdrop.overlayColor.r, remoteProgressBackdrop.overlayColor.g, remoteProgressBackdrop.overlayColor.b, 0.55) }
                GradientStop { position: 1; color: Qt.rgba(0, 0, 0, 0.55) }
            }
            visible: remoteProgressDialog.visible
        }

        MouseArea {
            anchors.fill: parent
            enabled: remoteProgressDialog.visible
            acceptedButtons: Qt.AllButtons
            hoverEnabled: true
        }

        onVisibleChanged: if (visible) remoteBlurSource.scheduleUpdate()
    }

    Popup {
        id: remoteProgressDialog
        modal: false
        focus: true
        padding: 0
        closePolicy: Popup.NoAutoClose
        parent: root
        implicitWidth: Math.min(360 * (window.scaleFactor || 1), root.width - 40)
        implicitHeight: 220 * (window.scaleFactor || 1)
        width: implicitWidth
        height: implicitHeight
        x: Math.round((root.width - width) / 2)
        y: Math.round((root.height - height) / 2)
        property real popupScale: window.scaleFactor || 1
        readonly property color cardColor: albumComboBox.currentText === "Extras"
            ? Qt.rgba(0.95, 0.95, 0.95, 0.95)
            : coverColorAnalyzer.backgroundColor
        readonly property color cardBorderColor: albumComboBox.currentText === "Extras"
            ? lerpColor(currentColor, nextColor, colorProgress)
            : coverColorAnalyzer.dominantColor
        readonly property color cardTextColor: albumComboBox.currentText === "Extras"
            ? Qt.rgba(0.1, 0.1, 0.1, 1)
            : coverColorAnalyzer.textColor

        property bool closing: false

        function openWithSnapshot() {
            if (!root.isRemote) {
                return
            }
            closing = false
            if (remoteBlurSource) {
                remoteBlurSource.scheduleUpdate()
            }
            open()
        }

        function closeIfOpen() {
            if (!visible || closing) {
                return
            }
            closing = true
            // Rely on exit transition for smooth fade-out
            close()
        }

        onOpened: busyIndicator.running = true
        onClosed: {
            busyIndicator.running = false
            closing = false
        }

        enter: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 200; easing.type: Easing.InOutQuad }
        }
        exit: Transition {
            NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 250; easing.type: Easing.InOutQuad }
        }

        background: Item {
            width: remoteProgressDialog.implicitWidth
            height: remoteProgressDialog.implicitHeight

            Rectangle {
                id: dialogCard
                anchors.centerIn: parent
                width: parent.width
                height: parent.height
                radius: 16 * remoteProgressDialog.popupScale
                color: remoteProgressDialog.cardColor
                border.width: 2
                border.color: remoteProgressDialog.cardBorderColor
                layer.enabled: true
                layer.effect: DropShadow {
                    horizontalOffset: 0
                    verticalOffset: 8 * remoteProgressDialog.popupScale
                    radius: 24 * remoteProgressDialog.popupScale
                    samples: 32
                    color: Qt.rgba(0, 0, 0, 0.5)
                }
            }
        }

        contentItem: ColumnLayout {
            anchors.fill: parent
            anchors.margins: 32 * remoteProgressDialog.popupScale
            spacing: 16 * remoteProgressDialog.popupScale

            BusyIndicator {
                id: busyIndicator
                Layout.alignment: Qt.AlignHCenter
                implicitWidth: 64 * remoteProgressDialog.popupScale
                implicitHeight: 64 * remoteProgressDialog.popupScale
                running: false
                visible: running
                Material.accent: coverColorAnalyzer.accentColor
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.fillWidth: true
                Layout.maximumWidth: remoteProgressDialog.implicitWidth - 64 * remoteProgressDialog.popupScale
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 18 * remoteProgressDialog.popupScale
                font.weight: Font.Medium
                text: progressTitle.text
                color: albumComboBox.currentText === "Extras"
                    ? "#000000"
                    : remoteProgressDialog.cardTextColor
                wrapMode: Text.WordWrap
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.fillWidth: true
                Layout.maximumWidth: remoteProgressDialog.implicitWidth - 64 * remoteProgressDialog.popupScale
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 13 * remoteProgressDialog.popupScale
                opacity: 0.75
                text: progressDetail.text
                color: albumComboBox.currentText === "Extras"
                    ? "#000000"
                    : remoteProgressDialog.cardTextColor
                wrapMode: Text.WordWrap
            }

            // Hidden text elements to simplify dynamic binding updates
            Text { id: progressTitle; visible: false; text: "Downloading soundtrack." }
            Text { id: progressDetail; visible: false; text: "This may take a minute." }
        }
    }

    ScrollView {
        id: scrollView
        anchors.fill: parent
        anchors.leftMargin: 28
        anchors.rightMargin: 28
        anchors.topMargin: 10
        anchors.bottomMargin: 10
        clip: true

        ColumnLayout {
            width: scrollView.width
            spacing: 20

            Item {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: Math.min(root.width - 40, 300)
                Layout.preferredHeight: Layout.preferredWidth

                Image {
                    id: coverImage
                    width: parent.width
                    height: parent.height
                    source: renamer ? renamer.cover_image : ""
                    cache: true
                    asynchronous: true
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                    antialiasing: true
                    sourceSize: Qt.size(600, 600)
                    layer.enabled: true
                    layer.smooth: true

                    onStatusChanged: {
                        if (status === Image.Ready) {
                            imageBorder.width = coverImage.paintedWidth
                            imageBorder.height = coverImage.paintedHeight
                            imageBorder.x = (parent.width - paintedWidth) / 2
                            imageBorder.y = (parent.height - paintedHeight) / 2
                        }
                    }
                }

                Rectangle {
                    id: imageBorder
                    color: "transparent"
                    border.color: albumComboBox.currentText === "Extras"
                        ? lerpColor(currentColor, nextColor, colorProgress)
                        : coverColorAnalyzer.dominantColor
                    border.width: 2
                }
            }

            ComboBox {
                id: albumComboBox
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                model: renamer.album_list
                onCurrentTextChanged: {
                    coverColorAnalyzer.setColors(currentText)
                    renamer.set_current_album(currentText)
                    audioExplorer.updateSongList()
                    trackNumberCheckBox.visible = currentText !== "Extras"
                }

                popup: Popup {
                    y: albumComboBox.height
                    width: albumComboBox.width
                    implicitHeight: contentItem.implicitHeight
                    padding: 1

                    contentItem: ListView {
                        clip: true
                        implicitHeight: contentHeight
                        interactive: false
                        model: albumComboBox.popup.visible ? albumComboBox.delegateModel : null
                        currentIndex: albumComboBox.highlightedIndex
                    }

                    background: Rectangle {
                        color: albumComboBox.currentText === "Extras"
                            ? lerpColor(currentColor, nextColor, colorProgress)
                            : coverColorAnalyzer.backgroundColor
                        border.color: albumComboBox.currentText === "Extras"
                            ? "#000000"
                            : coverColorAnalyzer.dominantColor
                        border.width: 1
                        radius: 5
                    }

                    Rectangle {
                        visible: albumComboBox.currentText === "Extras"
                        anchors.fill: parent
                        color: "transparent"
                        border.color: lerpColor(currentColor, nextColor, colorProgress)
                        border.width: 2
                        radius: 5
                        opacity: 0.5
                    }
                }

                contentItem: Text {
                    leftPadding: 10
                    rightPadding: albumComboBox.indicator.width + albumComboBox.spacing
                    text: albumComboBox.displayText
                    font.pixelSize: 14
                    font.family: "Noto Sans JP"
                    color: albumComboBox.currentText === "Extras"
                        ? "#000000"
                        : coverColorAnalyzer.textColor
                    verticalAlignment: Text.AlignVCenter
                    renderType: Text.QtRendering
                    antialiasing: true
                }

                delegate: ItemDelegate {
                    width: albumComboBox.width
                    contentItem: Text {
                        text: modelData
                        color: albumComboBox.currentText === "Extras"
                            ? getContrastColor(lerpColor(currentColor, nextColor, colorProgress))
                            : coverColorAnalyzer.textColor
                        font.pixelSize: 14
                        font.family: "Noto Sans JP"
                        elide: Text.ElideRight
                        verticalAlignment: Text.AlignVCenter
                        renderType: Text.QtRendering
                        antialiasing: true
                    }
                    highlighted: albumComboBox.highlightedIndex === index
                    background: Rectangle {
                        color: parent.highlighted
                            ? (albumComboBox.currentText === "Extras"
                                ? Qt.lighter(lerpColor(currentColor, nextColor, colorProgress), 1.2)
                                : Qt.lighter(coverColorAnalyzer.dominantColor, 1.2))
                            : "transparent"
                        opacity: parent.highlighted ? 0.3 : 1
                    }
                }
            }

            ComboBox {
                id: languageComboBox
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                model: ["Japanese", "Romaji", "English"]
                onCurrentTextChanged: {
                    renamer.set_current_language(currentText)
                    audioExplorer.updateSongList()
                }

                popup: Popup {
                    y: languageComboBox.height
                    width: languageComboBox.width
                    implicitHeight: contentItem.implicitHeight
                    padding: 1

                    contentItem: ListView {
                        clip: true
                        implicitHeight: contentHeight
                        interactive: false  // Disables scrolling
                        model: languageComboBox.popup.visible ? languageComboBox.delegateModel : null
                        currentIndex: languageComboBox.highlightedIndex
                    }

                    background: Rectangle {
                        color: albumComboBox.currentText === "Extras"
                            ? lerpColor(currentColor, nextColor, colorProgress)
                            : coverColorAnalyzer.backgroundColor
                        border.color: albumComboBox.currentText === "Extras"
                            ? lerpColor(currentColor, nextColor, colorProgress)
                            : coverColorAnalyzer.dominantColor
                        border.width: 1
                        radius: 5
                    }

                    Rectangle {
                        visible: albumComboBox.currentText === "Extras"
                        anchors.fill: parent
                        color: "transparent"
                        border.color: lerpColor(currentColor, nextColor, colorProgress)
                        border.width: 2
                        radius: 5
                        opacity: 0.5
                    }
                }

                contentItem: Text {
                    leftPadding: 10
                    rightPadding: languageComboBox.indicator.width + languageComboBox.spacing
                    text: languageComboBox.displayText
                    font.pixelSize: 14
                    font.family: "Noto Sans JP"
                    color: albumComboBox.currentText === "Extras"
                        ? "#000000"
                        : coverColorAnalyzer.textColor
                    verticalAlignment: Text.AlignVCenter
                    renderType: Text.QtRendering
                    antialiasing: true
                }

                delegate: ItemDelegate {
                    width: languageComboBox.width
                    contentItem: Text {
                        text: modelData
                        color: albumComboBox.currentText === "Extras"
                            ? getContrastColor(lerpColor(currentColor, nextColor, colorProgress))
                            : coverColorAnalyzer.textColor
                        font.pixelSize: 14
                        font.family: "Noto Sans JP"
                        elide: Text.ElideRight
                        verticalAlignment: Text.AlignVCenter
                        renderType: Text.QtRendering
                        antialiasing: true
                    }
                    highlighted: languageComboBox.highlightedIndex === index
                    background: Rectangle {
                        color: parent.highlighted
                            ? (albumComboBox.currentText === "Extras"
                                ? Qt.lighter(lerpColor(currentColor, nextColor, colorProgress), 1.2)
                                : Qt.lighter(coverColorAnalyzer.dominantColor, 1.2))
                            : "transparent"
                        opacity: parent.highlighted ? 0.3 : 1
                    }
                }
            }

            CheckBox {
                id: trackNumberCheckBox
                Layout.fillWidth: true
                Layout.preferredHeight: 30
                text: "Include track numbers in filenames"
                checked: true
                visible: albumComboBox.currentText !== "Extras"
                
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 14
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: parent.indicator.width + parent.spacing
                    color: albumComboBox.currentText === "Extras"
                        ? "#000000"
                        : coverColorAnalyzer.textColor
                }
                
                indicator: Rectangle {
                    implicitWidth: 20
                    implicitHeight: 20
                    x: parent.leftPadding
                    y: parent.height / 2 - height / 2
                    radius: 3
                    color: "transparent"
                    border.color: parent.checked 
                        ? (albumComboBox.currentText === "Extras"
                            ? "#000000"
                            : coverColorAnalyzer.dominantColor)
                        : "gray"
                    
                    Rectangle {
                        width: 14
                        height: 14
                        x: 3
                        y: 3
                        radius: 2
                        color: parent.border.color
                        visible: parent.parent.checked
                    }
                }
                
                onCheckedChanged: {
                    renamer.set_include_track_numbers(checked)
                }
            }

            Button {
                id: actionButton
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                text: renamer.get_current_album_state() === "extract" ? "Extract Soundtrack" : "Rename Files"
                onClicked: {
                    if (renamer.get_current_album_state() === "extract") {
                        renamer.extract_soundtrack(albumComboBox.currentText)
                    } else {
                        var result = renamer.rename_files()
                        resultText.text = result
                        resultText.color = result.startsWith("Error:")
                            ? "red"
                            : (albumComboBox.currentText === "Extras"
                                ? "#000000"
                                : coverColorAnalyzer.textColor)
                        resultDialog.open()
                    }
                }
                enabled: renamer.can_extract() && (!renamer.is_extracting || renamer.get_current_album_state() !== "extract")

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 14
                    opacity: enabled ? 1.0 : 0.3
                    color: albumComboBox.currentText === "Extras"
                        ? "#000000"
                        : coverColorAnalyzer.textColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }

                background: Rectangle {
                    implicitWidth: 100
                    implicitHeight: 50
                    opacity: enabled ? 1 : 0.3
                    color: parent.down
                        ? (albumComboBox.currentText === "Extras"
                            ? Qt.darker(lerpColor(currentColor, nextColor, colorProgress), 1.1)
                            : Qt.darker(coverColorAnalyzer.dominantColor, 1.1))
                        : (albumComboBox.currentText === "Extras"
                            ? lerpColor(currentColor, nextColor, colorProgress)
                            : coverColorAnalyzer.dominantColor)
                    radius: 5
                }
            }

            Rectangle {
                id: outputFolderContainer
                Layout.fillWidth: true
                height: 40
                color: albumComboBox.currentText === "Extras"
                    ? lerpColor(currentColor, nextColor, colorProgress)
                    : coverColorAnalyzer.backgroundColor
                border.color: albumComboBox.currentText === "Extras"
                    ? lerpColor(currentColor, nextColor, colorProgress)
                    : coverColorAnalyzer.dominantColor
                border.width: 1
                radius: 5

                Text {
                    id: placeholderText
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Choose a folder"
                    color: albumComboBox.currentText === "Extras"
                        ? "#000000"
                        : coverColorAnalyzer.textColor
                    opacity: 0.5
                    visible: !outputFolderText.text
                }

                TextInput {
                    id: outputFolderText
                    anchors.fill: parent
                    anchors.margins: 10
                    verticalAlignment: TextInput.AlignVCenter
                    text: renamer.output_folder
                    color: albumComboBox.currentText === "Extras"
                        ? "#000000"
                        : coverColorAnalyzer.textColor
                    selectByMouse: true
                    selectionColor: albumComboBox.currentText === "Extras"
                        ? lerpColor(currentColor, nextColor, colorProgress)
                        : coverColorAnalyzer.accentColor
                    selectedTextColor: albumComboBox.currentText === "Extras"
                        ? "#000000"
                        : coverColorAnalyzer.textColor
                    clip: true
                    
                    Keys.onEscapePressed: {
                        outputFolderText.focus = false
                    }
                    
                    Keys.onReturnPressed: {
                        outputFolderText.focus = false
                    }
                    
                    onEditingFinished: {
                        renamer.set_output_directory(text)
                        outputFolderText.focus = false
                    }
                }
            }

            Button {
                text: "Browse"
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                onClicked: {
                    folderExplorer.open()
                    // Wait for component to load before scrolling
                    scrollTimer.start()
                }
                enabled: !folderExplorer.isOpen

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 14
                    opacity: enabled ? 1.0 : 0.3
                    color: albumComboBox.currentText === "Extras"
                        ? "#000000"
                        : coverColorAnalyzer.textColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }

                background: Rectangle {
                    implicitWidth: 100
                    implicitHeight: 40
                    opacity: enabled ? 1 : 0.3
                    color: parent.down
                        ? (albumComboBox.currentText === "Extras"
                            ? Qt.darker(lerpColor(currentColor, nextColor, colorProgress), 1.1)
                            : Qt.darker(coverColorAnalyzer.dominantColor, 1.1))
                        : (albumComboBox.currentText === "Extras"
                            ? lerpColor(currentColor, nextColor, colorProgress)
                            : coverColorAnalyzer.dominantColor)
                    radius: 5
                }
            }

            Text {
                text: "Choose the base folder where the soundtracks are located"
                font.pixelSize: 12
                font.italic: true
                color: albumComboBox.currentText === "Extras"
                    ? getContrastColor(lerpColor(currentColor, nextColor, colorProgress))
                    : getContrastColor(coverColorAnalyzer.accentColor)
            }

            Button {
                text: "Tracks"
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                onClicked: {
                    audioExplorer.open()
                    // Wait for component to load before scrolling
                    scrollTimer.start()
                }
                enabled: !audioExplorer.isOpen

                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 14
                    opacity: enabled ? 1.0 : 0.3
                    color: albumComboBox.currentText === "Extras"
                        ? "#000000"
                        : coverColorAnalyzer.textColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }

                background: Rectangle {
                    implicitWidth: 100
                    implicitHeight: 40
                    opacity: enabled ? 1 : 0.3
                    color: parent.down
                        ? (albumComboBox.currentText === "Extras"
                            ? Qt.darker(lerpColor(currentColor, nextColor, colorProgress), 1.1)
                            : Qt.darker(coverColorAnalyzer.dominantColor, 1.1))
                        : (albumComboBox.currentText === "Extras"
                            ? lerpColor(currentColor, nextColor, colorProgress)
                            : coverColorAnalyzer.dominantColor)
                    radius: 5
                }
            }

            Components.FolderExplorer {
                id: folderExplorer
                Layout.fillWidth: true
                Layout.preferredHeight: 500
                isExtras: albumComboBox.currentText === "Extras"
                backgroundColor: albumComboBox.currentText === "Extras"
                    ? lerpColor(currentColor, nextColor, colorProgress)
                    : coverColorAnalyzer.backgroundColor
                textColor: albumComboBox.currentText === "Extras"
                    ? "#000000"
                    : coverColorAnalyzer.textColor
                accentColor: albumComboBox.currentText === "Extras"
                    ? lerpColor(currentColor, nextColor, colorProgress)
                    : coverColorAnalyzer.accentColor
                visible: folderExplorer.isOpen
                opacity: folderExplorer.isOpen ? 1 : 0
                Behavior on opacity {
                    NumberAnimation {
                        duration: 300
                    }
                }

                Component.onCompleted: {
                    folderExplorer.setRenamer(renamer)
                }

                onFolderSelected: function(folder) {
                    renamer.set_output_folder(folder)
                    outputFolderText.text = folder
                }

                onOpened: { audioExplorer.close() }

                onRequestScroll: scrollTimer.start()
                onClosed: {}
            }


            Components.AudioExplorer {
                id: audioExplorer
                Layout.fillWidth: true
                Layout.preferredHeight: 500
                isExtras: albumComboBox.currentText === "Extras"
                backgroundColor: albumComboBox.currentText === "Extras"
                    ? lerpColor(currentColor, nextColor, colorProgress)
                    : coverColorAnalyzer.backgroundColor
                textColor: albumComboBox.currentText === "Extras"
                    ? "#000000"
                    : coverColorAnalyzer.textColor
                accentColor: albumComboBox.currentText === "Extras"
                    ? lerpColor(currentColor, nextColor, colorProgress)
                    : coverColorAnalyzer.accentColor
                renamerObject: typeof renamer !== "undefined" ? renamer : null
                visible: audioExplorer.isOpen
                opacity: audioExplorer.isOpen ? 1 : 0
                Behavior on opacity {
                    NumberAnimation {
                        duration: 300
                    }
                }

                onOpened: folderExplorer.close()
                onRequestScroll: scrollTimer.start()
                onClosed: {}
            }
        }

        ScrollBar.vertical: ScrollBar {
            id: verticalScrollBar
            anchors {
                right: parent.right
                top: parent.top
                bottom: parent.bottom
                margins: 2
            }
            policy: ScrollBar.AsNeeded
            active: false
            visible: size < 1.0
            
            contentItem: Rectangle {
                implicitWidth: 12
                radius: width / 2
                color: albumComboBox.currentText === "Extras" 
                    ? lerpColor(currentColor, nextColor, colorProgress)
                    : coverColorAnalyzer.accentColor
                opacity: parent.active || parent.pressed ? 1 : 0.3

                Behavior on opacity {
                    NumberAnimation { duration: 200 }
                }
            }

            background: Rectangle {
                implicitWidth: 12
                radius: width / 2
                color: albumComboBox.currentText === "Extras"
                    ? Qt.darker(lerpColor(currentColor, nextColor, colorProgress), 1.2)
                    : Qt.darker(coverColorAnalyzer.backgroundColor, 1.2)
                opacity: 0.1
            }
        }
    }

    Dialog {
        id: resultDialog
        title: {
            if (resultText.text.startsWith("Error:")) {
                return "Operation Failed"
            } else if (root.isRemote && resultText.text.includes("downloaded")) {
                return "Download Complete"
            } else if (resultText.text.includes("extracted")) {
                return "Extraction Complete"
            } else {
                return "Renaming Complete"
            }
        }
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        width: Math.min(parent.width * 0.7, 400 * window.scaleFactor)
        height: Math.min(parent.height * 0.5, 300 * window.scaleFactor)
        modal: false
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        property color dialogBackgroundColor: isExtras 
            ? lerpColor(currentColor, nextColor, colorProgress)
            : coverColorAnalyzer.backgroundColor
        property color dialogHeaderColor: isExtras 
            ? adjustBrightness(lerpColor(currentColor, nextColor, colorProgress), 20)
            : coverColorAnalyzer.dominantColor
        property color dialogButtonColor: isExtras 
            ? adjustBrightness(lerpColor(currentColor, nextColor, colorProgress), 40)
            : coverColorAnalyzer.accentColor

        background: Item {
            anchors.fill: parent

            Rectangle {
                id: dialogBackground
                anchors.fill: parent
                color: resultDialog.dialogBackgroundColor
                border.width: 2 * window.scaleFactor
                border.color: Qt.darker(resultDialog.dialogHeaderColor, 1.3)
                radius: 10 * window.scaleFactor
                layer.enabled: true
                layer.effect: DropShadow {
                    horizontalOffset: 0
                    verticalOffset: 8 * window.scaleFactor
                    radius: 24 * window.scaleFactor
                    samples: 32
                    color: Qt.rgba(0, 0, 0, 0.5)
                }
            }

            Rectangle {
                id: headerBackground
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 50 * window.scaleFactor
                color: resultDialog.dialogHeaderColor
                radius: dialogBackground.radius
            }

            Rectangle {
                anchors.top: headerBackground.bottom
                anchors.bottom: footerBackground.top
                anchors.left: parent.left
                anchors.right: parent.right
                color: resultDialog.dialogBackgroundColor
            }

            Rectangle {
                id: footerBackground
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                height: 60 * window.scaleFactor
                color: resultDialog.dialogBackgroundColor
                radius: dialogBackground.radius
            }

            Rectangle {
                anchors.left: parent.left
                anchors.top: headerBackground.bottom
                anchors.bottom: footerBackground.top
                width: dialogBackground.radius
                color: resultDialog.dialogBackgroundColor
            }

            Rectangle {
                anchors.right: parent.right
                anchors.top: headerBackground.bottom
                anchors.bottom: footerBackground.top
                width: dialogBackground.radius
                color: resultDialog.dialogBackgroundColor
            }
        }

        header: Rectangle {
            width: parent.width
            height: 50 * window.scaleFactor
            color: resultDialog.dialogHeaderColor
            radius: dialogBackground.radius

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: parent.radius
                color: parent.color
            }

            Text {
                anchors.centerIn: parent
                text: resultDialog.title
                color: getContrastColor(resultDialog.dialogHeaderColor)
                font.pixelSize: 16 * window.scaleFactor
                font.family: "Noto Sans JP"
                font.weight: Font.Medium
                renderType: Text.QtRendering
                antialiasing: true
            }
        }

        contentItem: Item {
            ColumnLayout {
                anchors.fill: parent
                anchors.topMargin: 10 * window.scaleFactor
                anchors.bottomMargin: 10 * window.scaleFactor

                Text {
                    id: resultText
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 14 * window.scaleFactor
                    font.family: "Noto Sans JP"
                    color: getContrastColor(resultDialog.dialogBackgroundColor)
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    renderType: Text.QtRendering
                    antialiasing: true
                }
            }
        }

        footer: Rectangle {
            width: parent.width
            height: 60 * window.scaleFactor
            color: resultDialog.dialogBackgroundColor
            radius: dialogBackground.radius

            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: parent.radius
                color: parent.color
            }

            Button {
                anchors.centerIn: parent
                text: "OK"
                font.pixelSize: 14 * window.scaleFactor
                implicitHeight: 40 * window.scaleFactor
                implicitWidth: 100 * window.scaleFactor
                onClicked: resultDialog.accept()

                background: Rectangle {
                    color: resultDialog.dialogButtonColor
                    radius: 5 * window.scaleFactor
                    opacity: parent.down ? 0.8 : 1
                }

                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: isExtras 
                        ? getContrastColor(resultDialog.dialogButtonColor)
                        : coverColorAnalyzer.textColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    Dialog {
        id: permissionErrorDialog
        title: "Permission Denied"
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        width: Math.min(parent.width * 0.6, 350 * window.scaleFactor)
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        
        property string messageText: ""
        
        background: Rectangle {
            color: isExtras 
                ? lerpColor(currentColor, nextColor, colorProgress)
                : coverColorAnalyzer.backgroundColor
            border.width: 2 * window.scaleFactor
            border.color: "#e74c3c"
            radius: 10 * window.scaleFactor
        }
        
        contentItem: ColumnLayout {
            spacing: 15 * window.scaleFactor
            
            Text {
                text: "Permission Error"
                font.pixelSize: 16 * window.scaleFactor
                font.bold: true
                color: isExtras ? "#000000" : coverColorAnalyzer.textColor
                Layout.alignment: Qt.AlignHCenter
            }
            
            Text {
                text: permissionErrorDialog.messageText
                font.pixelSize: 14 * window.scaleFactor
                color: isExtras ? "#000000" : coverColorAnalyzer.textColor
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                horizontalAlignment: Text.AlignHCenter
            }
            
            Button {
                text: "OK"
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 100 * window.scaleFactor
                onClicked: permissionErrorDialog.close()
                
                background: Rectangle {
                    color: parent.pressed ? Qt.darker("#e74c3c", 1.2) : "#e74c3c"
                    radius: 5 * window.scaleFactor
                }
                
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: "#ffffff"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    Connections {
        target: typeof renamer !== "undefined" ? renamer : null
        function onExtractionFinished(result) {
            if (remoteProgressDialog.visible) {
                remoteProgressDialog.closeIfOpen()
            }
            resultText.text = result
            resultText.color = result.startsWith("Error:") ? "red" :
                (albumComboBox.currentText === "Extras" ?
                    "#000000" :
                    coverColorAnalyzer.textColor)
            resultDialog.open()
            progressPoller.stop()           
            if (typeof renamer !== "undefined" && renamer) {
                var currentState = renamer.get_current_album_state()
                actionButton.text = currentState === "extract" ? "Extract Soundtrack" : "Rename Files"
                actionButton.enabled = renamer.can_extract() && (!renamer.is_extracting || currentState !== "extract")
            }
        }
        function onPermissionError(message) {
            permissionErrorDialog.messageText = message
            permissionErrorDialog.open()
        }
        function onExtractionStateChanged(isExtracting) {
            if (!root.isRemote) {
                return
            }
            if (isExtracting) {
                remoteProgressDialog.openWithSnapshot()
                progressTitle.text = "Downloading soundtrack."
                progressDetail.text = "This may take a minute depending on your connection."
                progressPoller.restart()
            } else {
                remoteProgressDialog.closeIfOpen()
                progressPoller.stop()
            }
        }
        function onAlbumStateChanged() {
            if (typeof renamer !== "undefined" && renamer) {
                var currentState = renamer.get_current_album_state()
                actionButton.text = currentState === "extract" ? "Extract Soundtrack" : "Rename Files"
            }
        }
        function onCanExtractChanged() {
            if (typeof renamer !== "undefined" && renamer) {
                actionButton.enabled = renamer.can_extract()
            }
        }
    }

    // Poller to detect local completion in remote mode by checking files and integrity
    Timer {
        id: progressPoller
        interval: 1000
        repeat: true
        running: false
        onTriggered: {
            if (!renamer || !root.isRemote) { return }
            var progress = renamer.get_current_album_progress()
            if (progress && progress.complete) {
                progressTitle.text = "Download complete."
                progressDetail.text = "All files are present and renamed."
                progressPoller.stop()
                // Sync backend state to ensure button/state update immediately
                renamer.sync_with_local_completion()
                // Start fade-out transition
                remoteProgressDialog.closeIfOpen()
                // Wait for fade-out animation to complete before showing success dialog
                fadeTransitionTimer.start()
            } else if (progress && progress.expected > 0) {
                progressTitle.text = "Downloading soundtrack... (" + progress.found + "/" + progress.expected + ")"
                progressDetail.text = "Files are being saved and renamed."
            } else {
                progressTitle.text = "Downloading soundtrack."
                progressDetail.text = "This may take a minute depending on your connection."
            }
        }
        function restart() { stop(); start() }
    }

    // Timer to delay showing result dialog after download completes, allowing smooth fade-out
    Timer {
        id: fadeTransitionTimer
        interval: 300  // Match the exit animation duration
        repeat: false
        onTriggered: {
            resultText.text = "Soundtrack '" + (renamer ? renamer.current_album_localized : albumComboBox.currentText) + "' processed successfully"
            resultText.color = albumComboBox.currentText === "Extras" ?
                "#000000" :
                coverColorAnalyzer.textColor
            resultDialog.open()
        }
    }

    // Ensure backend operations are cancelled if the window is closed mid-extraction
    Component.onDestruction: {
        if (renamer && renamer.is_extracting) {
            renamer.cancel_operations()
        }
    }

    Timer {
        id: scrollTimer
        interval: 300 
        repeat: false
        onTriggered: {
            // Only animate if there's enough content to scroll
            var canScroll = scrollView.contentHeight > scrollView.height
            
            if (folderExplorer.isOpen || audioExplorer.isOpen) {
                if (canScroll) {
                    scrollToBottomAnimation.start()
                }
            } else {
                // Only scroll to top if we're not already there
                if (scrollView.contentItem.contentY > 0) {
                    scrollToTopAnimation.start()
                }
            }
        }
    }

    NumberAnimation {
        id: scrollToBottomAnimation
        target: scrollView.contentItem
        property: "contentY"
        to: scrollView.contentHeight - scrollView.height
        duration: 1000
        easing.type: Easing.InOutQuad
    }

    NumberAnimation {
        id: scrollToTopAnimation
        target: scrollView.contentItem
        property: "contentY"
        to: 0
        duration: 1000
        easing.type: Easing.InOutQuad
    }
}







