let mediaRecorder;
let recordedChunks = [];
let currentVideo = null;
let isRecording = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeParticles();
    setupEventListeners();
});

function initializeParticles() {
    const particlesContainer = document.getElementById('particles');
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 6 + 's';
        particle.style.animationDuration = (Math.random() * 4 + 4) + 's';
        particlesContainer.appendChild(particle);
    }
}

function setupEventListeners() {
    // Recording controls
    document.getElementById('startRecord').addEventListener('click', startRecording);
    document.getElementById('stopRecord').addEventListener('click', stopRecording);
    document.getElementById('playRecord').addEventListener('click', playRecording);
    document.getElementById('analyzeRecord').addEventListener('click', analyzeRecording);

    // Upload functionality
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    
    fileInput.addEventListener('change', handleFileSelect);
    document.getElementById('analyzeUpload').addEventListener('click', analyzeUploadedFile);
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 1280, height: 720 }, 
            audio: true 
        });
        
        const preview = document.getElementById('preview');
        const placeholder = document.getElementById('placeholder');
        
        preview.srcObject = stream;
        placeholder.style.display = 'none';
        
        mediaRecorder = new MediaRecorder(stream);
        recordedChunks = [];
        
        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            currentVideo = URL.createObjectURL(blob);
            
            preview.srcObject = null;
            preview.src = currentVideo;
            preview.controls = true;
            
            document.getElementById('playRecord').style.display = 'inline-block';
            document.getElementById('analyzeRecord').style.display = 'inline-block';
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        document.getElementById('startRecord').style.display = 'none';
        document.getElementById('stopRecord').style.display = 'inline-block';
        document.querySelector('.video-preview').classList.add('recording');
        
    } catch (error) {
        alert('Camera access denied. Please allow camera permissions.');
        console.error('Error accessing camera:', error);
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        // Update UI
        document.getElementById('startRecord').style.display = 'inline-block';
        document.getElementById('stopRecord').style.display = 'none';
        document.querySelector('.video-preview').classList.remove('recording');
    }
}

function playRecording() {
    const preview = document.getElementById('preview');
    if (preview.paused) {
        preview.play();
        document.getElementById('playRecord').textContent = '⏸️ Pause';
    } else {
        preview.pause();
        document.getElementById('playRecord').textContent = '▶️ Play';
    }
}

function handleDragOver(e) {
    e.preventDefault();
    document.getElementById('uploadArea').classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    document.getElementById('uploadArea').classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    document.getElementById('uploadArea').classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        processFile(file);
    }
}

function processFile(file) {
    if (!file.type.startsWith('video/')) {
        alert('Please select a video file.');
        return;
    }
    
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const progressFill = document.getElementById('progressFill');
    const preview = document.getElementById('preview');
    const placeholder = document.getElementById('placeholder');
    
    fileName.textContent = `📹 ${file.name} (${formatFileSize(file.size)})`;
    fileInfo.style.display = 'block';
    
    // Create video URL and display in preview
    currentVideo = URL.createObjectURL(file);
    preview.srcObject = null;
    preview.src = currentVideo;
    placeholder.style.display = 'none';
    
    // Add video controls for uploaded video
    preview.controls = true;
    
    // Simulate upload progress
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
        }
        progressFill.style.width = progress + '%';
    }, 200);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function analyzeRecording() {
    analyzeVideo('recorded');
}

function analyzeUploadedFile() {
    analyzeVideo('uploaded');
}

function analyzeVideo(source) {
    // Show loading state
    const analyzeBtn = source === 'recorded' ? 
        document.getElementById('analyzeRecord') : 
        document.getElementById('analyzeUpload');
    
    const originalText = analyzeBtn.innerHTML;
    analyzeBtn.innerHTML = '<span class="status-indicator status-processing"></span>Analyzing...';
    analyzeBtn.disabled = true;
    
    // Simulate AI analysis
    setTimeout(() => {
        generateMockAnalysis();
        document.getElementById('results').style.display = 'block';
        analyzeBtn.innerHTML = originalText;
        analyzeBtn.disabled = false;
        
        // Scroll to results
        document.getElementById('results').scrollIntoView({ 
            behavior: 'smooth' 
        });
    }, 3000);
}

function generateMockAnalysis() {
    // Generate random but realistic metrics
    const clarity = Math.floor(Math.random() * 20 + 75);
    const fillers = Math.floor(Math.random() * 15 + 5);
    const confidence = Math.floor(Math.random() * 25 + 70);
    const engagement = Math.floor(Math.random() * 30 + 65);
    
    document.getElementById('clarityScore').textContent = clarity + '%';
    document.getElementById('fillerCount').textContent = fillers;
    document.getElementById('confidenceScore').textContent = confidence + '%';
    document.getElementById('engagementScore').textContent = engagement + '%';
    
    generateTimeline();
}

function generateTimeline() {
    const timeline = document.getElementById('timeline');
    const issues = [
        { time: '00:15', type: 'filler', text: 'Used "um" - consider pausing instead' },
        { time: '00:32', type: 'clarity', text: 'Spoke too quickly - slow down for clarity' },
        { time: '01:07', type: 'body', text: 'Avoided eye contact - look directly at camera' },
        { time: '01:23', type: 'tone', text: 'Voice pitch dropped - maintain energy' },
        { time: '01:45', type: 'filler', text: 'Multiple "like" usage - practice elimination' },
        { time: '02:12', type: 'clarity', text: 'Mumbled words - articulate more clearly' },
        { time: '02:38', type: 'body', text: 'Fidgeting detected - keep hands steady' },
        { time: '03:01', type: 'tone', text: 'Great confident delivery here!' }
    ];
    
    timeline.innerHTML = '';
    
    issues.forEach((issue, index) => {
        setTimeout(() => {
            const item = document.createElement('div');
            item.className = 'timeline-item';
            item.style.opacity = '0';
            item.style.transform = 'translateX(-20px)';
            
            item.innerHTML = `
                <div class="timestamp">${issue.time}</div>
                <div class="issue-type issue-${issue.type}">${issue.type}</div>
                <div style="flex: 1;">${issue.text}</div>
            `;
            
            timeline.appendChild(item);
            
            // Animate in
            setTimeout(() => {
                item.style.transition = 'all 0.5s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateX(0)';
            }, 50);
        }, index * 200);
    });
}

// Add click handlers for timeline items to jump to video timestamps
document.addEventListener('click', function(e) {
    if (e.target.closest('.timeline-item')) {
        const timestamp = e.target.closest('.timeline-item').querySelector('.timestamp').textContent;
        const [minutes, seconds] = timestamp.split(':').map(Number);
        const totalSeconds = minutes * 60 + seconds;
        
        // If video is available, jump to timestamp
        const preview = document.getElementById('preview');
        if (preview.src || preview.srcObject) {
            preview.currentTime = totalSeconds;
            preview.play();
        }
    }
});

// Add some interactive feedback
document.querySelectorAll('.metric-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-5px) scale(1.05)';
        this.style.boxShadow = '0 15px 40px rgba(102, 126, 234, 0.2)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0) scale(1)';
        this.style.boxShadow = 'none';
    });
});

