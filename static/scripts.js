// Handle recording logic
let mediaRecorder;
let audioChunks = [];
const startButton = document.getElementById('start-recording');
const stopButton = document.getElementById('stop-recording');

startButton.addEventListener('click', async () => {
    startButton.disabled = true;
    stopButton.disabled = false;

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            audioChunks = []; // Clear previous data
            uploadRecordedAudio(audioBlob);
        };

        mediaRecorder.start();
        console.log("Recording started...");
    } catch (err) {
        console.error("Error accessing microphone:", err);
        startButton.disabled = false;
        stopButton.disabled = true;
    }
});

stopButton.addEventListener('click', () => {
    startButton.disabled = false;
    stopButton.disabled = true;

    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        console.log("Recording stopped...");
    }
});

// Upload recorded audio to the server
function uploadRecordedAudio(audioBlob) {
    const formData = new FormData();
    formData.append('audio_data', audioBlob, 'recorded_audio.wav');

    fetch('/record', {
        method: 'POST',
        body: formData,
    })
        .then(response => response.text())
        .then(data => {
            document.body.innerHTML = data; // Display results
        })
        .catch(error => console.error('Error uploading audio:', error));
}
const form = document.querySelector('form');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress-bar');

form.addEventListener('submit', (event) => {
    progressContainer.style.display = 'block';
    let width = 0;
    const interval = setInterval(() => {
        if (width >= 100) {
            clearInterval(interval);
        } else {
            width += 10;
            progressBar.style.width = width + '%';
        }
    }, 300);
});
