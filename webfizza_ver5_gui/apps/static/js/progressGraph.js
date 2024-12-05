document.addEventListener("DOMContentLoaded", function () {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/logs/");

    // 그래프 데이터 초기화
    let xssDataPoints = [];
    let sqliDataPoints = [];
    let reflectedCountXSS = 0; // XSS 누적 개수
    let reflectedCountSQLi = 0; // SQLi 누적 개수
    let xValueXSS = 0;         // XSS X축 진행값
    let xValueSQLi = 0;        // SQLi X축 진행값
    let currentCycle = "XSS";  // 현재 사이클 모드
    let currentMode = "XSS";   // 현재 그래프 모드 (토글 상태)
    let lastPayloadInfo = "";  // Reflected payload 이전 JSON 정보

    // CanvasJS Chart 초기화
    const chart = new CanvasJS.Chart("chartContainer", {
        animationEnabled: true,
        theme: "light2",
        title: {
            text: "Fuzzing Progress"
        },
        axisX: {
            title: "Cycle",
            interval: 1
        },
        axisY: {
            title: "Reflected Payload Count",
            minimum: 0
        },
        data: [
            {
                type: "spline", // 곡선 그래프 설정
                markerType: "circle",
                markerSize: 8,
                showInLegend: true,
                name: "XSS",
                dataPoints: xssDataPoints
            },
            {
                type: "spline", // 곡선 그래프 설정
                markerType: "circle",
                markerSize: 8,
                showInLegend: true,
                name: "SQLi",
                dataPoints: sqliDataPoints
            }
        ]
    });

    ws.onopen = function () {
        console.log("WebSocket connection opened");
    };

    ws.onmessage = function (event) {
        console.log("Raw message data from server:", event.data);

        try {
            const data = JSON.parse(event.data); // JSON 형식의 데이터 파싱
            const message = data.message;       // 메시지 추출
            console.log("Parsed message:", message);

            // 사이클 변경 감지 및 자동 토글 전환
            if (message.startsWith("Starting XSS fuzzing cycle")) {
                currentCycle = "XSS";
                switchToXSS(); // XSS 토글로 자동 전환
                console.log("Current cycle set to XSS.");
            } else if (message.startsWith("Starting sqli fuzzing cycle")) {
                currentCycle = "SQLi";
                switchToSQLi(); // SQLi 토글로 자동 전환
                console.log("Current cycle set to SQLi.");
            }

            // 데이터 포인트 추가
            if (message.startsWith("[")) {
                // Reflected payload 이전 데이터를 저장
                lastPayloadInfo = message; // JSON 메시지 저장
                if (currentCycle === "XSS") {
                    xValueXSS++;
                    xssDataPoints.push({
                        x: xValueXSS,
                        y: reflectedCountXSS,
                        toolTipContent: `Cycle: ${xValueXSS}<br>Payload: ${lastPayloadInfo}`,
                        markerType: "none"
                    });
                } else if (currentCycle === "SQLi") {
                    xValueSQLi++;
                    sqliDataPoints.push({
                        x: xValueSQLi,
                        y: reflectedCountSQLi,
                        toolTipContent: `Cycle: ${xValueSQLi}<br>Payload: ${lastPayloadInfo}`,
                        markerType: "none"
                    });
                }
            } else if (message.startsWith("Reflected payload:")) {
                // Reflected Payload 감지
                if (currentCycle === "XSS") {
                    reflectedCountXSS++;
                    xssDataPoints[xssDataPoints.length - 1].y = reflectedCountXSS;
                    xssDataPoints[xssDataPoints.length - 1].toolTipContent = `
                        Cycle: ${xValueXSS}<br>
                        Payload: ${lastPayloadInfo}`;
                    xssDataPoints[xssDataPoints.length - 1].markerType = "circle";
                } else if (currentCycle === "SQLi") {
                    reflectedCountSQLi++;
                    sqliDataPoints[sqliDataPoints.length - 1].y = reflectedCountSQLi;
                    sqliDataPoints[sqliDataPoints.length - 1].toolTipContent = `
                        Cycle: ${xValueSQLi}<br>
                        Payload: ${lastPayloadInfo}`;
                    sqliDataPoints[sqliDataPoints.length - 1].markerType = "circle";
                }
            }

            // 현재 토글 상태에 따라 그래프 렌더링
            if (currentMode === "XSS") {
                chart.options.data[0].dataPoints = xssDataPoints;
                chart.options.data[1].dataPoints = [];
            } else if (currentMode === "SQLi") {
                chart.options.data[1].dataPoints = sqliDataPoints;
                chart.options.data[0].dataPoints = [];
            }

            chart.render();
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

    // XSS 토글 버튼 클릭 처리
    function switchToXSS() {
        currentMode = "XSS";
        chart.options.title.text = "Fuzzing Progress - XSS";
        chart.options.data[0].dataPoints = xssDataPoints;
        chart.options.data[1].dataPoints = [];
        document.getElementById("xss-toggle").classList.add("btn-primary");
        document.getElementById("xss-toggle").classList.remove("btn-secondary");
        document.getElementById("sqli-toggle").classList.add("btn-secondary");
        document.getElementById("sqli-toggle").classList.remove("btn-primary");
        chart.render();
    }

    // SQLi 토글 버튼 클릭 처리
    function switchToSQLi() {
        currentMode = "SQLi";
        chart.options.title.text = "Fuzzing Progress - SQLi";
        chart.options.data[1].dataPoints = sqliDataPoints;
        chart.options.data[0].dataPoints = [];
        document.getElementById("sqli-toggle").classList.add("btn-primary");
        document.getElementById("sqli-toggle").classList.remove("btn-secondary");
        document.getElementById("xss-toggle").classList.add("btn-secondary");
        document.getElementById("xss-toggle").classList.remove("btn-primary");
        chart.render();
    }

    document.getElementById("xss-toggle").addEventListener("click", switchToXSS);
    document.getElementById("sqli-toggle").addEventListener("click", switchToSQLi);
});

  