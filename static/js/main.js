document.addEventListener("DOMContentLoaded", function () {

    // ==========================
    // QR SCANNER (index.html)
    // ==========================
    const qrDiv = document.getElementById("qr-reader");
    // const resultBox = document.getElementById("scan-result"); // no longer used
    const statusTextEl = document.getElementById("scanner-status-text");
    const statusDotEl = document.querySelector(".status-dot");

    // Elements for modal student info (index.html)
    const scanModal = document.getElementById("scan-modal");
    const scanPhotoEl = document.getElementById("scan-photo");
    const scanIdnoEl = document.getElementById("scan-idno");
    const scanLastNameEl = document.getElementById("scan-last-name");
    const scanFirstNameEl = document.getElementById("scan-first-name");
    const scanCourseEl = document.getElementById("scan-course");
    const scanLevelEl = document.getElementById("scan-level");
    const scanInfoMessage = document.getElementById("scan-info-message");

    // Error modal elements
    const scanErrorModal = document.getElementById("scan-error-modal");
    const scanErrorText = document.getElementById("scan-error-text");
    const scanErrorClose = document.getElementById("scan-error-close");

    let scanHideTimer = null;

    // === Audio + rate-limit state ===
    let audioCtx = null;
    let lastScanTime = 0;
    const SCAN_COOLDOWN_MS = 4000; // 4 seconds between scans
    let isProcessingScan = false;

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
        }
    }

    // Simple beep sound (success/error)
    function playBeep(type) {
        try {
            if (!window.AudioContext && !window.webkitAudioContext) {
                return; // browser doesn't support Web Audio
            }
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }

            const osc = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();

            // Different frequencies for success vs error
            if (type === "success") {
                osc.frequency.value = 850; // higher tone
            } else {
                osc.frequency.value = 350; // lower tone
            }

            // Very short beep
            const now = audioCtx.currentTime;
            gainNode.gain.setValueAtTime(0.001, now);
            gainNode.gain.exponentialRampToValueAtTime(0.2, now + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.18);

            osc.connect(gainNode);
            gainNode.connect(audioCtx.destination);

            osc.start(now);
            osc.stop(now + 0.2);
        } catch (e) {
            console.warn("Beep error:", e);
        }
    }

    // Show student modal for 10 seconds (success case)
    function showStudentModal(student, timeIn, created) {
        if (!scanModal) return;

        if (scanIdnoEl) scanIdnoEl.textContent = student.student_id || "";
        if (scanLastNameEl) scanLastNameEl.textContent = student.last_name || "";
        if (scanFirstNameEl) scanFirstNameEl.textContent = student.first_name || "";
        if (scanCourseEl) scanCourseEl.textContent = student.course || "";
        if (scanLevelEl) scanLevelEl.textContent = student.level || "";

        if (scanPhotoEl) {
            if (student.photo_url) {
                scanPhotoEl.src = student.photo_url;
                scanPhotoEl.style.display = "block";
            } else {
                scanPhotoEl.style.display = "none";
            }
        }

        if (scanInfoMessage) {
            scanInfoMessage.textContent = created
                ? `Attendance recorded at ${timeIn}.`
                : `Already recorded today at ${timeIn}.`;
        }

        scanModal.classList.add("show");

        if (scanHideTimer) clearTimeout(scanHideTimer);
        scanHideTimer = setTimeout(() => {
            scanModal.classList.remove("show");
            if (scanInfoMessage) scanInfoMessage.textContent = "";
            setStatus("Scanning... hold QR code steady.");
        }, 10000); // you can change 10000 -> 4000 if you want faster close
    }

    // Error modal (for not_found, errors, server issues)
    function showErrorModal(message) {
        if (!scanErrorModal || !scanErrorText) return;
        scanErrorText.textContent = message || "Unknown error.";
        scanErrorModal.classList.add("show");
    }

    // Error modal close handlers + reset status
    if (scanErrorModal) {
        if (scanErrorClose) {
            scanErrorClose.addEventListener("click", () => {
                scanErrorModal.classList.remove("show");
                setStatus("Scanning... hold QR code steady.");
            });
        }

        scanErrorModal.addEventListener("click", (e) => {
            if (e.target === scanErrorModal) {
                scanErrorModal.classList.remove("show");
                setStatus("Scanning... hold QR code steady.");
            }
        });

        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && scanErrorModal.classList.contains("show")) {
                scanErrorModal.classList.remove("show");
                setStatus("Scanning... hold QR code steady.");
            }
        });
    }

    if (qrDiv) {
        console.log("Html5Qrcode is:", typeof Html5Qrcode);

        if (typeof Html5Qrcode === "undefined") {
            console.error("Html5Qrcode library NOT loaded.");
            alert("QR library failed to load. Check console for details.");
            setStatus("QR library failed to load.", "error");

        } else {
            setStatus("Initializing camera...");

            const qrScanner = new Html5Qrcode("qr-reader");

            function onSuccess(decodedText) {
                // Rate-limit duplicate scans
                const now = Date.now();
                if (isProcessingScan || (now - lastScanTime) < SCAN_COOLDOWN_MS) {
                    return; // ignore repeated triggers too quickly
                }
                lastScanTime = now;
                isProcessingScan = true;

                console.log("Scanned:", decodedText);
                setStatus("QR detected, checking student...", "info");

                fetch("/scan", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ qr_text: decodedText })
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === "ok") {
                            const student = data.student;
                            const timeIn = data.time_in;
                            const created = data.created;

                            setStatus("Attendance saved!", "success");
                            playBeep("success");
                            showStudentModal(student, timeIn, created);

                        } else if (data.status === "not_found") {
                            setStatus("Student not found for this QR.", "error");
                            playBeep("error");
                            showErrorModal("Student does not exist or QR is not registered.");

                        } else {
                            const msg = data.message || "Unknown error.";
                            setStatus("Error saving scan.", "error");
                            playBeep("error");
                            showErrorModal(msg);
                        }
                    })
                    .catch(err => {
                        console.error("Scan error:", err);
                        setStatus("Server error.", "error");
                        playBeep("error");
                        showErrorModal("Server error while processing QR. Please try again.");
                    })
                    .finally(() => {
                        // allow scanning again after the cooldown window passes
                        setTimeout(() => {
                            isProcessingScan = false;
                            setStatus("Scanning... hold QR code steady.");
                        }, SCAN_COOLDOWN_MS);
                    });
            }

            function onError(err) {
                // ignore continuous minor scan errors
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
        }
    }

    // ==========================
    // LOGIN / REGISTER TABS (login.html)
    // ==========================
    const tabs = document.querySelectorAll(".auth-tab");
    const forms = document.querySelectorAll(".auth-form");

    if (tabs.length > 0 && forms.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener("click", () => {
                const targetSelector = tab.getAttribute("data-target");
                const targetForm = document.querySelector(targetSelector);

                tabs.forEach(t => t.classList.remove("active"));
                tab.classList.add("active");

                forms.forEach(f => f.classList.add("auth-form-hidden"));
                if (targetForm) {
                    targetForm.classList.remove("auth-form-hidden");
                }
            });
        });
    }

    // ==========================
    // PASSWORD TOGGLE (eye icon)
    // ==========================
    const toggleButtons = document.querySelectorAll(".password-toggle-btn");

    toggleButtons.forEach(btn => {
        const targetId = btn.getAttribute("data-password-toggle");
        if (!targetId) return;

        const input = document.getElementById(targetId);
        if (!input) return;

        btn.addEventListener("click", () => {
            if (input.type === "password") {
                input.type = "text";
                btn.textContent = "🙈";
            } else {
                input.type = "password";
                btn.textContent = "👁";
            }
        });
    });

    // ==========================
    // ADMIN INLINE EDIT (admin.html)
    // ==========================
    const adminForm = document.querySelector(".admin-user-form form");

    if (adminForm) {
        const idInput = adminForm.querySelector("#admin-user-id");
        const emailInput = adminForm.querySelector("input[name='email']");
        const passwordInput = adminForm.querySelector("input[name='password']");
        const submitBtn = adminForm.querySelector("#admin-submit-btn");
        const titleEl = document.getElementById("admin-form-title");

        const editButtons = document.querySelectorAll(".edit-user-btn");

        editButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                const id = btn.getAttribute("data-id");
                const email = btn.getAttribute("data-email");
                const password = btn.getAttribute("data-password");

                if (idInput) idInput.value = id || "";
                if (emailInput) emailInput.value = email || "";
                if (passwordInput) passwordInput.value = password || "";

                if (submitBtn) submitBtn.textContent = "UPDATE";
                if (titleEl) titleEl.textContent = "EDIT USER";
            });
        });
    }

    // ==========================
    // STUDENT VIEWER (studentmngt.html)
    // ==========================
    const viewButtons = document.querySelectorAll(".view-student-btn");
    const viewerIdno = document.getElementById("view-student-idno");
    const viewerLastName = document.getElementById("view-last-name");
    const viewerFirstName = document.getElementById("view-first-name");
    const viewerCourse = document.getElementById("view-course");
    const viewerLevel = document.getElementById("view-level");
    const viewerPhoto = document.getElementById("viewer-photo");

    if (
        viewButtons.length > 0 &&
        viewerIdno &&
        viewerLastName &&
        viewerFirstName &&
        viewerCourse &&
        viewerLevel &&
        viewerPhoto
    ) {
        viewButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                const idno = btn.getAttribute("data-student-id") || "";
                const lastName = btn.getAttribute("data-last-name") || "";
                const firstName = btn.getAttribute("data-first-name") || "";
                const course = btn.getAttribute("data-course") || "";
                const level = btn.getAttribute("data-level") || "";
                const photoUrl = btn.getAttribute("data-photo") || "";

                viewerIdno.value = idno;
                viewerLastName.value = lastName;
                viewerFirstName.value = firstName;
                viewerCourse.value = course;
                viewerLevel.value = level;

                if (photoUrl) {
                    viewerPhoto.src = photoUrl;
                }
            });
        });
    }

    // ==========================
    // STUDENT FORM (student.html)
    // ==========================
    const cameraViewer = document.getElementById("camera-viewer");
    const captureBtn = document.getElementById("capture-btn");
    const photoImg = document.getElementById("photo-result");
    const photoPlaceholder = document.getElementById("photo-placeholder");
    const photoDataInput = document.getElementById("photo-data-input");

    if (cameraViewer && typeof Webcam !== "undefined") {
        Webcam.set({
            width: 320,
            height: 240,
            image_format: "jpeg",
            jpeg_quality: 90
        });
        Webcam.attach("#camera-viewer");

        if (captureBtn && photoImg) {
            captureBtn.addEventListener("click", () => {
                Webcam.snap(function (dataUri) {
                    photoImg.src = dataUri;
                    photoImg.style.display = "block";

                    if (photoPlaceholder) {
                        photoPlaceholder.style.display = "none";
                    }

                    if (photoDataInput) {
                        photoDataInput.value = dataUri;
                    }
                });
            });
        }
    }

    // QR code generation (IDNO -> QR) on student form
    const studentIdInput = document.querySelector("input[name='student_id']");
    const qrBoxStudent = document.getElementById("qrcode-box");

    function generateStudentQR(text) {
        if (!qrBoxStudent || typeof QRCode === "undefined") return;
        qrBoxStudent.innerHTML = "";
        if (!text) return;
        new QRCode(qrBoxStudent, {
            text: text,
            width: 180,
            height: 180
        });
    }

    if (studentIdInput && qrBoxStudent) {
        generateStudentQR(studentIdInput.value.trim());
        studentIdInput.addEventListener("input", () => {
            generateStudentQR(studentIdInput.value.trim());
        });
    }

// ==========================
// DELETE CONFIRMATION MODAL
// ==========================
const deleteModal = document.getElementById("delete-modal");
const modalCancelBtn = document.getElementById("modal-cancel-btn");
const modalConfirmBtn = document.getElementById("modal-confirm-btn");
const deleteButtons = document.querySelectorAll(".delete-user-btn");

let pendingDeleteUrl = null;

if (deleteModal && modalCancelBtn && modalConfirmBtn && deleteButtons.length > 0) {

    // Open modal
    deleteButtons.forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();

            const urlAttr = btn.getAttribute("data-delete-url");
            const hrefAttr = btn.getAttribute("href");

            pendingDeleteUrl = urlAttr || hrefAttr || null;

            if (!pendingDeleteUrl) {
                console.error("No delete URL found on button:", btn);
                return;
            }

            deleteModal.classList.add("show");
        });
    });

    // CLOSE only when clicking CANCEL
    modalCancelBtn.addEventListener("click", () => {
        deleteModal.classList.remove("show");
        pendingDeleteUrl = null;
    });

    // CONFIRM delete
    modalConfirmBtn.addEventListener("click", () => {
        if (!pendingDeleteUrl) {
            console.error("No pending delete URL when confirming delete.");
            deleteModal.classList.remove("show");
            return;
        }

        // Redirect to delete URL
        window.location.href = pendingDeleteUrl;
    });

    // No click-outside or ESC behavior (as you requested)
}



    // ==========================
    // AUTO-HIDE FLASH MESSAGES
    // ==========================
    const flashMessages = document.querySelectorAll(".flash-message");

    if (flashMessages.length > 0) {
        flashMessages.forEach((msg, index) => {
            // show for 3.5s + a small stagger per message
            const visibleTime = 3500 + index * 500;

            setTimeout(() => {
                msg.classList.add("flash-hide");

                // remove from DOM after animation
                setTimeout(() => {
                    if (msg && msg.parentNode) {
                        msg.parentNode.removeChild(msg);
                    }
                }, 500); // match CSS transition
            }, visibleTime);
        });
    }



});
