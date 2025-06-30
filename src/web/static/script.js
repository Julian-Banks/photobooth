
const eventSource = new EventSource("/stats_feed");

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    document.getElementById('fps').textContent = data.fps;
    document.getElementById('model').textContent = data.model;
    document.getElementById('numPoses').textContent = data.numPoses;
};

eventSource.onerror = function(error) {
    console.error("SSE connection error", error);
};
