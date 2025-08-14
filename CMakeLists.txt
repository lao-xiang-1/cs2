cmake_minimum_required(VERSION 3.10)

project(yolov8)

add_definitions(-DNOMINMAX) # 解决opencv报错问题
add_definitions(-std=c++11)
add_definitions(-DAPI_EXPORTS)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_CUDA_ARCHITECTURES "89")

MESSAGE(STATUS "operation system is ${CMAKE_SYSTEM}") 
IF (CMAKE_SYSTEM_NAME MATCHES "Linux")
    MESSAGE(STATUS "current platform: Linux ")
    set(CUDA_COMPILER_PATH "/usr/local/cuda/bin/nvcc")
    set(TENSORRT_PATH "/home/benol/Package/TensorRT-8.6.1.6")
    include_directories(/usr/local/cuda/include)
    link_directories(/usr/local/cuda/lib64)
    link_directories(/usr/local/cuda/lib)
ELSEIF (CMAKE_SYSTEM_NAME MATCHES "Windows")
    MESSAGE(STATUS "current platform: Windows")
    set(CUDA_COMPILER_PATH "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.8/bin/nvcc.exe")
    set(TENSORRT_PATH "D:\\code\\TensorRT-8.6.1.6")
    set(OpenCV_DIR "D:\\code\\opencv-4.8.1\\opencv\\build\\x64\\vc16\\lib")
    # include_directories(${PROJECT_SOURCE_DIR}/windows)
    find_package(CUDA REQUIRED)
    include_directories(${CUDA_INCLUDE_DIRS})
    link_directories(${CUDA_LIBRARIES})
ELSE (CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64")
    MESSAGE(STATUS "other platform: ${CMAKE_SYSTEM_PROCESSOR}")
    include_directories(/usr/local/cuda/targets/aarch64-linux/include)
    link_directories(/usr/local/cuda/targets/aarch64-linux/lib)
ENDIF (CMAKE_SYSTEM_NAME MATCHES "Linux")
set(CMAKE_CUDA_COMPILER ${CUDA_COMPILER_PATH})
enable_language(CUDA)

# tensorrt
include_directories(${TENSORRT_PATH}/include)
link_directories(${TENSORRT_PATH}/lib)

find_package(OpenCV)
include_directories(${OpenCV_INCLUDE_DIRS})

include_directories(${PROJECT_SOURCE_DIR}/include)
include_directories(${PROJECT_SOURCE_DIR}/plugin)

add_library(myplugins SHARED ${PROJECT_SOURCE_DIR}/plugin/yololayer.cu)
target_link_libraries(myplugins nvinfer cudart)

file(GLOB_RECURSE SRCS ${PROJECT_SOURCE_DIR}/src/*.cpp ${PROJECT_SOURCE_DIR}/src/*.cu)

 add_executable(cs2_det ${PROJECT_SOURCE_DIR}/cs2_det.cpp ${SRCS})
 target_link_libraries(cs2_det nvinfer cudart myplugins ${OpenCV_LIBS})

add_executable(yolov8_det ${PROJECT_SOURCE_DIR}/yolov8_det.cpp ${SRCS})

target_link_libraries(yolov8_det nvinfer)
target_link_libraries(yolov8_det cudart)
target_link_libraries(yolov8_det myplugins)
target_link_libraries(yolov8_det ${OpenCV_LIBS})

# add_executable(yolov8_5u_det ${PROJECT_SOURCE_DIR}/yolov8_5u_det.cpp ${SRCS})
# target_link_libraries(yolov8_5u_det nvinfer cudart myplugins ${OpenCV_LIBS})
