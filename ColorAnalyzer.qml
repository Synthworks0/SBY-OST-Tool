import QtQuick 2.15

Item {
    id: root
    property string currentAlbum: "Bunny Girl Senpai"
    property color dominantColor: "#5cc4f1"
    property color backgroundColor: "#182f74"
    property color accentColor: "#063c94"
    property color textColor: "#ffffff"

    function setColors(album) {
        switch (album) {
            case "Bunny Girl Senpai":
                dominantColor = "#5cc4f1"
                backgroundColor = "#182f74"
                accentColor = "#063c94"
                textColor = "#ffffff"
                break
            case "Dreaming Girl":
                dominantColor = "#e53975"
                backgroundColor = "#463758"
                accentColor = "#ec86ac"
                textColor = "#ffffff"
                break
            case "Sister Venturing Out":
                dominantColor = "#e7534f"
                backgroundColor = "#ec9f99"
                accentColor = "#cb7166"
                textColor = "#ffffff"
                break
            case "Knapsack Kid":
                dominantColor = "#98403d"
                backgroundColor = "#c68384"
                accentColor = "#f2a99a"
                textColor = "#ffffff"
                break
        }
    }

    Component.onCompleted: {
        setColors(currentAlbum)
    }
}