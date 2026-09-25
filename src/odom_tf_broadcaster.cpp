#include <functional>
#include <memory>
#include <string>

#include "geometry_msgs/msg/transform_stamped.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "rclcpp/rclcpp.hpp"
#include "tf2_ros/transform_broadcaster.h"

class OdomTfBroadcaster : public rclcpp::Node
{
public:
  OdomTfBroadcaster()
  : Node("go2_odom_tf_broadcaster")
  {
    odom_topic_ = declare_parameter<std::string>(
      "odom_topic", "/utlidar/robot_odom");
    parent_frame_ = declare_parameter<std::string>("parent_frame", "odom");
    child_frame_ = declare_parameter<std::string>("child_frame", "base_link");
    use_message_frames_ = declare_parameter<bool>("use_message_frames", true);

    tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);

    // Best effort accepts both best-effort sensor publishers and reliable publishers.
    const auto qos = rclcpp::QoS(rclcpp::KeepLast(50)).best_effort();
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
      odom_topic_, qos,
      std::bind(&OdomTfBroadcaster::odomCallback, this, std::placeholders::_1));

    RCLCPP_INFO(
      get_logger(), "Listening to %s and publishing TF %s -> %s",
      odom_topic_.c_str(), parent_frame_.c_str(), child_frame_.c_str());
  }

private:
  void odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg)
  {
    geometry_msgs::msg::TransformStamped transform;
    transform.header.stamp = msg->header.stamp;

    if (use_message_frames_) {
      transform.header.frame_id = msg->header.frame_id.empty() ? parent_frame_ : msg->header.frame_id;
      transform.child_frame_id = msg->child_frame_id.empty() ? child_frame_ : msg->child_frame_id;
    } else {
      transform.header.frame_id = parent_frame_;
      transform.child_frame_id = child_frame_;
    }

    if (transform.header.frame_id.empty() || transform.child_frame_id.empty()) {
      RCLCPP_WARN_THROTTLE(
        get_logger(), *get_clock(), 5000,
        "Odometry has an empty parent or child frame; TF was not published");
      return;
    }

    transform.transform.translation.x = msg->pose.pose.position.x;
    transform.transform.translation.y = msg->pose.pose.position.y;
    transform.transform.translation.z = msg->pose.pose.position.z;
    transform.transform.rotation = msg->pose.pose.orientation;

    tf_broadcaster_->sendTransform(transform);
  }

  std::string odom_topic_;
  std::string parent_frame_;
  std::string child_frame_;
  bool use_message_frames_;

  std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<OdomTfBroadcaster>());
  rclcpp::shutdown();
  return 0;
}
