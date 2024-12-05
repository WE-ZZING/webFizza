#!/bin/bash

# 애니메이션 프레임 파일 경로 설정
frames_forward=("Fizza_loading/pizza.txt" "Fizza_loading/pizza2.txt" "Fizza_loading/pizza3.txt" "Fizza_loading/pizza4.txt" "Fizza_loading/pizza5.txt" "Fizza_loading/pizza6.txt" "Fizza_loading/pizza7.txt" "Fizza_loading/pizza8.txt")
frames_backward=("Fizza_loading/pizza7.txt" "Fizza_loading/pizza6.txt" "Fizza_loading/pizza5.txt" "Fizza_loading/pizza4.txt" "Fizza_loading/pizza3.txt" "Fizza_loading/pizza2.txt" "Fizza_loading/pizza.txt")

while true; do
    # 정순 애니메이션
    for frame in "${frames_forward[@]}"; do
        clear
        cat "$frame"
        sleep 0.1  # 각 프레임 사이의 지연 시간 (초)
    done

    # 역순 애니메이션
    for frame in "${frames_backward[@]}"; do
        clear
        cat "$frame"
        sleep 0.13  # 각 프레임 사이의 지연 시간 (초)
    done
done

