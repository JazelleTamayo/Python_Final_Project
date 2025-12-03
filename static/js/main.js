document.addEventListener("DOMContentLoaded", function () {
    const qrDiv = document.getElementById("qr-reader");
    const resultBox = document.getElementById("scan-result");
    const statusTextEl = document.getElementById("scanner-status-text");
    const statusDotEl = document.querySelector(".status-dot");

    function setStatus(message, mode = "info") {
        if (statusTextEl) {
            statusTextEl.textContent = message;
        }
        if (statusDotEl) {
            statusDotEl.classList.remove("status-success", "status-error");
            if (mode === "success") {
                statusDotEl.classList.add("status-success");
            } else if (mode === "error") {
                statusDotEl.classList.add("status-error");
            }
            // default "info" uses base yellow color
        }
    }

    if (!qrDiv) {
        console.error("qr-reader element not found");
        setStatus("Scanner element not found.", "error");
        return;
    }

    console.log("Html5Qrcode is:", typeof Html5Qrcode);
    if (typeof Html5Qrcode === "undefined") {
        console.error("Html5Qrcode library NOT loaded.");
        alert("QR library failed to load. Check console for details.");
        setStatus("QR library failed to load.", "error");
        return;
    }

    setStatus("Initializing camera...");

    const qrScanner = new Html5Qrcode("qr-reader");

    function isValidURL(text) {
        try {
            const url = new URL(text);
            return true;
        } catch {
            return false;
        }
    }

    function onSuccess(decodedText) {
        console.log("Scanned:", decodedText);

        if (!resultBox) return;

        // If scanned text is a URL → make clickable link
        if (isValidURL(decodedText)) {
            resultBox.innerHTML =
                `<a href="${decodedText}" target="_blank" class="scan-link">${decodedText}</a>`;
        } else {
            // If not a link, show plain text
            resultBox.innerText = decodedText;
        }

        // briefly show "detected" status then go back to scanning
        setStatus("QR code detected!", "success");
        setTimeout(() => {
            setStatus("Scanning... hold QR code steady.");
        }, 2000);
    }

    function onError(err) {
        // Normal scan errors; keep silent
        // Could log if you want: console.log("Scan error:", err);
    }

    Html5Qrcode.getCameras()
        .then(cameras => {
            if (cameras.length > 0) {
                const id = cameras[0].id;
                setStatus("Scanning... hold QR code steady.");
                qrScanner.start(
                    id,
                    { fps: 10, qrbox: 250 },
                    onSuccess,
                    onError
                ).catch(err => {
                    console.error("Unable to start scanner:", err);
                    alert("Unable to start camera.");
                    setStatus("Unable to start camera.", "error");
                });
            } else {
                alert("No camera found.");
                setStatus("No camera found.", "error");
            }
        })
        .catch(err => {
            console.error("Camera error:", err);
            alert("Error accessing camera.");
            setStatus("Error accessing camera.", "error");
        });
});
