cmake_minimum_required(VERSION 3.16)
project(SBY_OST_Tool VERSION 1.0.0 LANGUAGES CXX)

# Set installation directory to build directory
set(CMAKE_INSTALL_PREFIX ${CMAKE_BINARY_DIR})

# Find required packages
set(Python3_EXECUTABLE "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3")
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(Qt6 COMPONENTS Core Quick Multimedia REQUIRED)
find_package(PkgConfig REQUIRED)

# Use pkg-config to find FFmpeg because cmake couldn't get the modules for some reason
pkg_check_modules(FFMPEG REQUIRED IMPORTED_TARGET
    libavcodec
    libavformat
    libavutil
    libswresample
    libswscale
)

# Set RPATH settings
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)
set(CMAKE_INSTALL_RPATH "@executable_path/../Frameworks")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# C++ wrapper
file(WRITE ${CMAKE_BINARY_DIR}/main.cpp
    "#define PY_SSIZE_T_CLEAN\n"
    "#include <Python.h>\n"
    "\n"
    "int main(int argc, char *argv[]) {\n"
    "    PyStatus status;\n"
    "    PyConfig config;\n"
    "    PyConfig_InitPythonConfig(&config);\n"
    "\n"
    "    // Initialize Python\n"
    "    status = Py_InitializeFromConfig(&config);\n"
    "    if (PyStatus_Exception(status)) {\n"
    "        PyConfig_Clear(&config);\n"
    "        return 1;\n"
    "    }\n"
    "\n"
    "    // Run your Python script\n"
    "    int result = PyRun_SimpleString(\n"
    "        \"import sys\\n\"\n"
    "        \"import os\\n\"\n"
    "        \"sys.path.append(os.path.dirname(os.path.realpath(__file__)))\\n\"\n"
    "        \"import rename\\n\"\n"
    "    );\n"
    "\n"
    "    // Cleanup\n"
    "    if (Py_FinalizeEx() < 0) {\n"
    "        return 120;\n"
    "    }\n"
    "\n"
    "    return result;\n"
    "}\n"
)

# QML and other resources
qt_add_resources(RESOURCES resources.qrc)

# Create the exe
add_executable(${PROJECT_NAME} MACOSX_BUNDLE
    ${CMAKE_BINARY_DIR}/main.cpp
    ${RESOURCES}
)

target_include_directories(${PROJECT_NAME} PRIVATE
    ${Python3_INCLUDE_DIRS}
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    Qt6::Core
    Qt6::Quick
    Qt6::Multimedia
    ${Python3_LIBRARIES}
    PkgConfig::FFMPEG
)

# Bundle properties
set_target_properties(${PROJECT_NAME} PROPERTIES
    MACOSX_BUNDLE TRUE
    MACOSX_BUNDLE_INFO_PLIST ${CMAKE_SOURCE_DIR}/Info.plist.in
    BUILD_WITH_INSTALL_RPATH TRUE
    INSTALL_RPATH "@executable_path/../Frameworks"
)

# Python files and resources
install(FILES 
    ${CMAKE_SOURCE_DIR}/rename.py
    ${CMAKE_SOURCE_DIR}/debug_logger.py
    ${CMAKE_SOURCE_DIR}/main.qml
    ${CMAKE_SOURCE_DIR}/MainContent.qml
    DESTINATION ${CMAKE_INSTALL_PREFIX}/${PROJECT_NAME}.app/Contents/Resources
)

# Python dependencies
execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import site; print(site.getsitepackages()[0])"
    OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

install(DIRECTORY
    ${PYTHON_SITE_PACKAGES}/PySide6
    ${PYTHON_SITE_PACKAGES}/mutagen
    DESTINATION ${CMAKE_INSTALL_PREFIX}/${PROJECT_NAME}.app/Contents/Resources/lib/python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}/site-packages
)

if(APPLE)
    add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E env DYLD_LIBRARY_PATH="${CMAKE_PREFIX_PATH}/lib"
        ${CMAKE_PREFIX_PATH}/bin/macdeployqt 
        $<TARGET_BUNDLE_DIR:${PROJECT_NAME}>
        -qmldir=${CMAKE_SOURCE_DIR}
        -verbose=2
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
        COMMENT "Running macdeployqt..."
    )
endif()