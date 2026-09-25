cmake_minimum_required(VERSION 3.5)
project(go2_nav_bridge)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(unitree_api REQUIRED)

add_executable(odom_tf_broadcaster src/odom_tf_broadcaster.cpp)
ament_target_dependencies(odom_tf_broadcaster
  geometry_msgs
  nav_msgs
  rclcpp
  tf2_ros
)

add_executable(cmd_vel_sport_adapter src/cmd_vel_sport_adapter.cpp)
ament_target_dependencies(cmd_vel_sport_adapter
  geometry_msgs
  rclcpp
  unitree_api
)

install(TARGETS
  odom_tf_broadcaster
  cmd_vel_sport_adapter
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  config
  launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
