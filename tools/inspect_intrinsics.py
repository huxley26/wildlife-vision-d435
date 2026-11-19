"""Read native color intrinsics for the same profile used by the publisher."""
def main():
    import pyrealsense2 as rs
    pipe = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
    profile = pipe.start(config)
    try:
        print(profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics())
    finally:
        pipe.stop()

if __name__ == '__main__':
    main()
