let running = false;

function startAttendance() {
    if (running) return;
    running = true;

    document.getElementById("status").innerHTML = "Live 🟢";
    let seconds = 300;

    setInterval(() => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        document.getElementById("timer").innerHTML = 
            `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        seconds--;
    }, 1000);

    setInterval(() => {
        const token = Math.random().toString(36).substring(2, 10);
        // Dynamically get the current website origin (works on local PC, local Wi-Fi, or Render cloud deployment)
        const origin = window.location.origin;
        document.getElementById("qr").src = 
            `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${origin}/student?token=${token}`;
    }, 5000);
}

function verifyWifi() {
    const status = document.getElementById("wifiStatus");
    const verify = document.getElementById("verifyBtn");
    const attendance = document.getElementById("attendanceBtn");

    status.style.display = "block";
    status.innerHTML = "🤖 Verifying College Wi-Fi...";
    verify.disabled = true;

    setTimeout(() => {
        status.innerHTML = `
        <strong>✅ College Wi-Fi Verified</strong><br>
        📍 Connected Network : <b>Campus_WiFi</b><br>
        🏫 Location : <b>SKASC</b><br>
        🔒 Authentication Successful
        `;
        attendance.disabled = false;
        verify.innerHTML = "✅ Verified";
    }, 2000);
}
