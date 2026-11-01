import os
from ultralytics import YOLO

def main():
    base_model = 'yolov8n.pt' 
    model = YOLO(base_model)
  
    dataset_yaml = 'dataset_sensor/data.yaml'
  
    if not os.path.exists(dataset_yaml):
        print(f"[WARNING] File {dataset_yaml} tidak ditemukan!")
        print("Pastikan folder dataset sudah sesuai sebelum menjalankan training.")

    print("Memulai proses training model YOLOv8...")

    results = model.train(
        data=dataset_yaml,   
        epochs=50,           
        imgsz=640,           
        batch=16,            
        name='train-2',      
        workers=2
    )

    print("\nTraining Selesai!")
    print("Model terbaik disimpan di: runs/detect/train-2/weights/best.pt")

if __name__ == '__main__':
    main()
