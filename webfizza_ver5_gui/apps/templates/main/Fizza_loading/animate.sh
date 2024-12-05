#!/bin/bash

# 애니메이션 프레임 파일 경로 설정
frames_forward=("pizza.txt" "pizza2.txt" "pizza3.txt" "pizza4.txt" "pizza5.txt" "pizza6.txt" "pizza7.txt" "pizza8.txt")
frames_backward=("pizza7.txt" "pizza6.txt" "pizza5.txt" "pizza4.txt" "pizza3.txt" "pizza2.txt" "pizza.txt")

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

