"""Portable entry point based on the saved train13 training configuration."""
import argparse
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', required=True, type=Path)
    p.add_argument('--model', default='yolov8n.pt')
    p.add_argument('--device', default='0')
    p.add_argument('--epochs', type=int, default=88)
    p.add_argument('--imgsz', type=int, default=960)
    p.add_argument('--batch', type=int, default=16)
    p.add_argument('--project', default='runs/detect')
    args = p.parse_args()
    if not args.data.is_file():
        p.error('data YAML not found')
    from ultralytics import YOLO
    result = YOLO(args.model).train(data=str(args.data.resolve()), epochs=args.epochs,
        imgsz=args.imgsz, batch=args.batch, device=args.device, project=args.project)
    print('Training finished:', result)

if __name__ == '__main__':
    main()
