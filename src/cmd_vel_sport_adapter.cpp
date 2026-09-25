#include <algorithm>
#include <chrono>
#include <cmath>
#include <functional>
#include <iomanip>
#include <locale>
#include <memory>
#include <sstream>
#include <string>

#include "geometry_msgs/msg/twist.hpp"
#include "rclcpp/rclcpp.hpp"
#include "unitree_api/msg/request.hpp"

using namespace std::chrono_literals;

class CmdVelSportAdapter : public rclcpp::Node
{
public:
  CmdVelSportAdapter()
  : Node("go2_cmd_vel_sport_adapter")
  {
    cmd_vel_topic_ = declare_parameter<std::string>("cmd_vel_topic", "/cmd_vel");
    sport_request_topic_ = declare_parameter<std::string>(
      "sport_request_topic", "/api/sport/request");

    max_vx_ = declare_parameter<double>("max_vx", 0.25);
    max_vy_ = declare_parameter<double>("max_vy", 0.15);
    max_vyaw_ = declare_parameter<double>("max_vyaw", 0.40);
    cmd_timeout_ = declare_parameter<double>("cmd_timeout", 0.40);
    zero_epsilon_ = declare_parameter<double>("zero_epsilon", 1.0e-3);
    enable_lateral_motion_ = declare_parameter<bool>("enable_lateral_motion", true);

    request_pub_ = create_publisher<unitree_api::msg::Request>(sport_request_topic_, 10);
    cmd_vel_sub_ = create_subscription<geometry_msgs::msg::Twist>(
      cmd_vel_topic_, 10,
      std::bind(&CmdVelSportAdapter::cmdVelCallback, this, std::placeholders::_1));

    watchdog_timer_ = create_wall_timer(50ms, std::bind(&CmdVelSportAdapter::watchdog, this));

    RCLCPP_INFO(
      get_logger(), "Bridging %s to %s (vx<=%.2f, vy<=%.2f, vyaw<=%.2f)",
      cmd_vel_topic_.c_str(), sport_request_topic_.c_str(), max_vx_, max_vy_, max_vyaw_);
  }

private:
  static constexpr std::uint32_t kApiStopMove = 1003;
  static constexpr std::uint32_t kApiMove = 1008;

  void cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg)
  {
    last_cmd_time_ = now();
    received_command_ = true;

    const double vx = std::clamp(msg->linear.x, -max_vx_, max_vx_);
    const double vy = enable_lateral_motion_ ?
      std::clamp(msg->linear.y, -max_vy_, max_vy_) : 0.0;
    const double vyaw = std::clamp(msg->angular.z, -max_vyaw_, max_vyaw_);

    if (std::abs(vx) <= zero_epsilon_ &&
      std::abs(vy) <= zero_epsilon_ &&
      std::abs(vyaw) <= zero_epsilon_)
    {
      publishStop();
      return;
    }

    publishMove(vx, vy, vyaw);
    stop_sent_ = false;
  }

  void publishMove(double vx, double vy, double vyaw)
  {
    unitree_api::msg::Request request;
    request.header.identity.api_id = kApiMove;

    std::ostringstream json;
    json.imbue(std::locale::classic());
    json << std::fixed << std::setprecision(6)
         << "{\"x\":" << vx
         << ",\"y\":" << vy
         << ",\"z\":" << vyaw << "}";
    request.parameter = json.str();

    request_pub_->publish(request);
  }

  void publishStop()
  {
    if (stop_sent_) {
      return;
    }

    unitree_api::msg::Request request;
    request.header.identity.api_id = kApiStopMove;
    request_pub_->publish(request);
    stop_sent_ = true;
  }

  void watchdog()
  {
    if (!received_command_ || stop_sent_) {
      return;
    }

    if ((now() - last_cmd_time_).seconds() > cmd_timeout_) {
      RCLCPP_WARN(get_logger(), "cmd_vel timeout; sending StopMove");
      publishStop();
    }
  }

  std::string cmd_vel_topic_;
  std::string sport_request_topic_;
  double max_vx_;
  double max_vy_;
  double max_vyaw_;
  double cmd_timeout_;
  double zero_epsilon_;
  bool enable_lateral_motion_;
  bool received_command_{false};
  bool stop_sent_{true};
  rclcpp::Time last_cmd_time_{0, 0, RCL_ROS_TIME};

  rclcpp::Publisher<unitree_api::msg::Request>::SharedPtr request_pub_;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;
  rclcpp::TimerBase::SharedPtr watchdog_timer_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CmdVelSportAdapter>());
  rclcpp::shutdown();
  return 0;
}
