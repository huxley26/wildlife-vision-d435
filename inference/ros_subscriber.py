"""Display the portfolio JSON protocol; no flight-control commands are sent."""
import argparse
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--topic', default='/animal_detections')
    args = parser.parse_args()
    import rospy
    from std_msgs.msg import String
    def callback(msg):
        try:
            data = json.loads(msg.data)
            if data['schema_version'] != 1:
                raise ValueError('unsupported schema')
            for item in data['animals']:
                print(item['code'], item['name'], item['count'], item['mean_offset_cm'])
        except (ValueError, KeyError, TypeError) as exc:
            rospy.logwarn('Invalid detection message: %s', exc)
    rospy.init_node('wildlife_display', anonymous=True)
    rospy.Subscriber(args.topic, String, callback)
    rospy.spin()

if __name__ == '__main__':
    main()
