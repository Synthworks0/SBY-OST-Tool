import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import Qt5Compat.GraphicalEffects

ApplicationWindow {
    id: window
    visible: true
    width: 600
    height: 1200
    minimumWidth: 600
    maximumWidth: 600
    minimumHeight: 1200
    maximumHeight: 1200
    title: "SBY OST Tool"
    
    Material.theme: Material.Dark
    Material.accent: coverColorAnalyzer.dominantColor
    Material.background: coverColorAnalyzer.backgroundColor
    Material.foreground: coverColorAnalyzer.textColor

    QtObject {
        id: coverColorAnalyzer
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
    }

    Loader {
        id: mainLoader
        anchors.fill: parent
        source: "MainContent.qml"
    }
}