import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtMultimedia
import QtQuick.Controls.Material 2.15

Item {
    id: root
    property bool isOpen: false
    property var renamerObject: null
    property bool isExtras: false
    property color backgroundColor
    property color textColor
    property color accentColor
    property string iconsPath: "../resources/icons/"

    signal opened()
    signal closed()

    function open() {
        isOpen = true;
        opened();
    }

    function close() {
        if (isOpen) {
            isOpen = false
            // Wait for opacity animation to start
            Qt.callLater(scrollTimer.start)
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

    function getIconUrl(iconName) {
        return Qt.resolvedUrl("../resources/icons/" + iconName)
    }

    function updateSongList() {
        songModel.clear();
        if (renamerObject && renamerObject.songList) {
            for (var i = 0; i < renamerObject.songList.length; i++) {
                var song = renamerObject.songList[i];
                songModel.append({
                    title: song.title,
                    length: song.length,
                    filePath: Qt.resolvedUrl(song.filePath)
                });
            }
        }
    }

    property var songList: renamerObject ? renamerObject.songList : []

    MediaPlayer {
        id: mediaPlayer
        audioOutput: audioOutput
    }

    AudioOutput {
        id: audioOutput
    }

    Rectangle {
        anchors.fill: parent
        color: adjustColorForContrast(root.backgroundColor)
        opacity: 0.9
        visible: root.isOpen

        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            Layout.minimumHeight: 0
            Layout.maximumHeight: parent.height

            ListView {
                id: songListView
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: songModel

                delegate: Item {
                    width: songListView.width
                    height: 40

                    property bool isPlaying: mediaPlayer.source === model.filePath && mediaPlayer.playbackState === MediaPlayer.PlayingState

                    RowLayout {
                        anchors {
                            fill: parent
                            leftMargin: 10
                            rightMargin: 10
                        }
                        spacing: 15

                        Button {
                            id: playButton
                            width: 32
                            height: 32
                            icon.width: 16
                            icon.height: 16
                            icon.source: isPlaying ? getIconUrl("pause_icon.png") : getIconUrl("play_icon.png")
                            onClicked: {
                                if (isPlaying) {
                                    mediaPlayer.pause();
                                } else {
                                    mediaPlayer.source = model.filePath;
                                    mediaPlayer.play();
                                }
                            }
                            background: Rectangle {
                                color: adjustColorForContrast(root.accentColor)
                                radius: 4
                            }
                        }

                        Text {
                            text: model.title
                            color: isExtras ? getContrastColor(root.backgroundColor) : root.textColor
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }

                        Text {
                            text: model.length
                            color: isExtras ? getContrastColor(root.backgroundColor) : root.textColor
                            Layout.minimumWidth: 45
                            horizontalAlignment: Text.AlignRight
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                Layout.margins: 15
                spacing: 15

                Button {
                    id: playPauseButton
                    width: 32
                    height: 32
                    icon.width: 16
                    icon.height: 16
                    icon.source: mediaPlayer.playbackState === MediaPlayer.PlayingState ? getIconUrl("pause_icon.png") : getIconUrl("play_icon.png")
                    onClicked: {
                        if (mediaPlayer.playbackState === MediaPlayer.PlayingState) {
                            mediaPlayer.pause();
                        } else {
                            mediaPlayer.play();
                        }
                    }
                    background: Rectangle {
                        color: adjustColorForContrast(root.accentColor)
                        radius: 4
                    }
                }

                Slider {
                    id: progressSlider
                    Layout.fillWidth: true
                    from: 0
                    to: mediaPlayer.duration
                    value: mediaPlayer.position
                    enabled: mediaPlayer.playbackState === MediaPlayer.PlayingState || mediaPlayer.playbackState === MediaPlayer.PausedState
                    onMoved: {
                        mediaPlayer.position = value
                    }

                    background: Rectangle {
                        x: progressSlider.leftPadding
                        y: progressSlider.topPadding + progressSlider.availableHeight / 2 - height / 2
                        width: progressSlider.availableWidth
                        height: 4
                        radius: 2
                        color: Qt.rgba(0, 0, 0, 0.26)

                        Rectangle {
                            width: progressSlider.visualPosition * parent.width
                            height: parent.height
                            radius: 2
                            color: root.accentColor
                        }
                    }

                    handle: Rectangle {
                        x: progressSlider.leftPadding + progressSlider.visualPosition * (progressSlider.availableWidth - width)
                        y: progressSlider.topPadding + progressSlider.availableHeight / 2 - height / 2
                        width: 16
                        height: 16
                        radius: 8
                        color: root.accentColor
                    }
                }

                Button {
                    id: volumeButton
                    width: 32
                    height: 32
                    icon.width: 16
                    icon.height: 16
                    icon.source: getIconUrl("volume_icon.png")
                    onClicked: {
                        volumePopup.open();
                    }
                    background: Rectangle {
                        color: adjustColorForContrast(root.accentColor)
                        radius: 4
                    }
                }

                Popup {
                    id: volumePopup
                    x: volumeButton.x - (width - volumeButton.width) / 2
                    y: volumeButton.y - 100
                    width: 50
                    height: 100
                    modal: false
                    focus: true
                    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

                    background: Rectangle {
                        color: root.isExtras 
                            ? adjustColorForContrast(root.backgroundColor)
                            : root.backgroundColor
                        radius: 4
                        border.color: root.isExtras
                            ? adjustColorForContrast(root.accentColor)
                            : root.accentColor
                        border.width: 1
                    }

                    contentItem: Slider {
                        id: volumeSlider
                        anchors.fill: parent
                        anchors.margins: 5
                        from: 0
                        to: 1
                        orientation: Qt.Vertical
                        value: audioOutput.volume 
                        onValueChanged: {
                            if (value === 0) {
                                audioOutput.volume = 0
                                mediaPlayer.pause()
                            } else {
                                // Only start playing if it was previously playing
                                var wasPlaying = mediaPlayer.playbackState === MediaPlayer.PlayingState
                                var scaledValue = Math.exp(value * Math.log(101)) / 100
                                audioOutput.volume = scaledValue
                                if (wasPlaying && mediaPlayer.playbackState === MediaPlayer.PausedState) {
                                    mediaPlayer.play()
                                }
                            }
                        }

                        Component.onCompleted: {
                            value = audioOutput.volume === 0 ? 0 : Math.log(audioOutput.volume * 100 + 1) / Math.log(101) // Volume is adjusted logarithmically to allign with how our ears work
                        }

                        background: Item {
                            id: sliderBackground
                            anchors.fill: parent

                            Rectangle {
                                id: groove
                                // Background line (maximum volume)
                                anchors.horizontalCenter: parent.horizontalCenter
                                y: 0
                                width: 4
                                height: parent.height
                                radius: 2
                                color: Qt.rgba(0, 0, 0, 0.26)
                            }

                            Rectangle {
                                id: fill
                                // Foreground line (current volume level)
                                anchors.horizontalCenter: groove.horizontalCenter
                                y: groove.y + groove.height * volumeSlider.visualPosition
                                width: groove.width
                                height: groove.height * (1 - volumeSlider.visualPosition)
                                radius: groove.radius
                                color: root.accentColor // Match playback slider color
                            }
                        }

                        handle: Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter
                            y: volumeSlider.topPadding + volumeSlider.visualPosition * volumeSlider.availableHeight - height / 2
                            width: 16
                            height: 16
                            radius: 8
                            color: root.accentColor // Match playback slider color
                        }
                    }
                }
            }
        }
    }

    ListModel {
        id: songModel
    }

    Component.onCompleted: {
        if (renamerObject && renamerObject.songList) {
            updateSongList();
        }
    }

    Connections {
        target: renamerObject
        function onSongListChanged() {
            updateSongList()
        }
        function onCurrentLanguageChanged() {
            updateSongList()
        }
        function onCurrentAlbumChanged() {
            updateSongList()
        }
    }
}
