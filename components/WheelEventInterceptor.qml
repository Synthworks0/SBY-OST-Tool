import QtQuick
import QtQuick.Controls

MouseArea {
    id: wheelInterceptor
    anchors.fill: parent
    acceptedButtons: Qt.NoButton 
    propagateComposedEvents: true
    hoverEnabled: true // Enable hover to ensure wheel events are captured
    
    property var targetList: null
    property bool enableParentScrollFirst: true
    
    function findParentScrollView() {
        var parent = wheelInterceptor.parent
        while (parent) {
            if (parent instanceof ScrollView) {
                return parent
            }
            parent = parent.parent
        }
        return null
    }
    
    onWheel: function(wheel) {
        if (!enableParentScrollFirst) {
            wheel.accepted = false
            return
        }

        var parentScrollView = findParentScrollView()
        if (!parentScrollView) {
            wheel.accepted = false
            return
        }

        // Get parent ScrollView's Flickable
        var parentFlickable = parentScrollView.contentItem

        // Calculate if parent can scroll
        var scrollUp = wheel.angleDelta.y > 0
        var parentCanScroll = scrollUp ? 
            parentFlickable.contentY > 0 : 
            parentFlickable.contentY < (parentFlickable.contentHeight - parentFlickable.height)

        if (parentCanScroll) {
            // Scroll parent first
            wheel.accepted = true
            parentFlickable.contentY -= wheel.angleDelta.y / 2
        } else if (targetList) {
            // Let list scroll only when parent can't
            wheel.accepted = false
            if ((scrollUp && targetList.atYBeginning) || 
                (!scrollUp && targetList.atYEnd)) {
                wheel.accepted = true // Prevent bounce
            }
        }
    }
}