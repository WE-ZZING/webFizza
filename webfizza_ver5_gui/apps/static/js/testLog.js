document.addEventListener("DOMContentLoaded", function () {
    const logContainer = document.getElementById("log-container");
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/logs/");

    ws.onopen = function () {
        console.log("WebSocket connection opened");
    };

    ws.onmessage = function (event) {
        // 수신된 원본 데이터 출력
        console.log("Raw message data from server:", event.data);

        try {
            const data = JSON.parse(event.data);  // JSON 형식의 데이터 파싱 시도
            const message = data.message;
            console.log("Parsed message:", message);  // 파싱된 메시지 확인

            if (logContainer) {
                const logElement = document.createElement("p");
                logElement.textContent = message;
                logContainer.appendChild(logElement);
            } else {
                console.error("Log container not found in DOM.");
            }
        } catch (error) {
            console.error("Error parsing message:", error, "Original data:", event.data);
        }
    };

    ws.onclose = function () {
        console.log("WebSocket connection closed");
    };

    ws.onerror = function (error) {
        console.error("WebSocket error:", error);
    };
});