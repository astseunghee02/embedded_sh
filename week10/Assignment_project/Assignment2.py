import cv2
import numpy as np
import os


def Image_line(image_path, output_path):

    # 이미지 읽기
    img = cv2.imread(image_path)
    
    # 원본 복사
    result = img.copy()
    
    # 노이즈 제거 (가우시안 블러)
    img_blur = cv2.GaussianBlur(img, (5, 5), 0)
    
    # HSV 색상 공간 변환
    hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)
    
    # 노란색 마스크
    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([35, 255, 255])
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # 흰색 마스크
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    mask_white = cv2.inRange(hsv, lower_white, upper_white)
    
    # 노란색 선 → 초록색
    result[mask_yellow > 0] = [0, 255, 0]
    
    # 흰색 선 → 검정색
    result[mask_white > 0] = [0, 0, 0]
    
    # 결과 저장
    cv2.imwrite(output_path, result)
    return True


def main():
    """메인 함수"""
    
    # 입력 이미지 경로
    input_dir = "image"
    image_files = [
        os.path.join(input_dir, "1.jpg"),
        os.path.join(input_dir, "2.jpg"),
        os.path.join(input_dir, "3.jpg"),
        os.path.join(input_dir, "4.jpg")
    ]
    
    # 출력 디렉토리
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    
    
    # 이미지 처리
    for i, img_file in enumerate(image_files, 1):
        output_path = os.path.join(output_dir, f"result_{i}.jpg")
        
        Image_line(img_file, output_path)
           

if __name__ == '__main__':
    main()