
document.addEventListener("DOMContentLoaded", () => {
    const logContainer = document.getElementById("logContainer");

    // WebSocket 연결
    const socket = new WebSocket("ws://127.0.0.1:8000/ws/logs/");

    socket.onopen = () => {
        console.log("WebSocket connection opened");
    };

    socket.onmessage = (event) => {
        const message = JSON.parse(event.data).message;
        displayLogMessage(message);
    };

    socket.onclose = () => {
        console.log("WebSocket connection closed");
    };

    function displayLogMessage(message) {
        const logItem = document.createElement("p");
        logItem.textContent = message;
        logContainer.appendChild(logItem);
    }
});

