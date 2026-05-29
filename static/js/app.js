/* ═══════════════════════════════════════════════════════════════════════════
   Smart Indoor Plant Care System - Application JavaScript
   P.A. College of Engineering, Mangalore | VTU, Belagavi | 2024-2025
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    console.log('🌿 Smart Indoor Plant Care System Initialized');

    // ─── State ────────────────────────────────────────────────────────────────
    let monitorInterval = null;
    let isMonitoring = false;
    let selectedFile = null;
    let reports = [];
    let lastAnalysis = null;

    // ─── DOM Elements ─────────────────────────────────────────────────────────
    const loadingScreen = document.getElementById('loadingScreen');
    const navbar = document.getElementById('navbar');
    const navLinks = document.getElementById('navLinks');
    const hamburger = document.getElementById('hamburger');
    const darkModeToggle = document.getElementById('darkModeToggle');
    const scrollToTopBtn = document.getElementById('scrollToTop');
    const monitorToggle = document.getElementById('monitorToggle');
    const liveIndicator = document.getElementById('liveIndicator');
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const removeImage = document.getElementById('removeImage');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsPlaceholder = document.getElementById('resultsPlaceholder');
    const resultsContent = document.getElementById('resultsContent');
    const analysisLoading = document.getElementById('analysisLoading');
    const toastContainer = document.getElementById('toastContainer');

    // ─── 1. Loading Screen ────────────────────────────────────────────────────
    setTimeout(() => {
        loadingScreen.classList.add('hidden');
    }, 1200);

    // ─── 2. Navbar Scroll Effect ──────────────────────────────────────────────
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        // Scroll to top button
        if (window.scrollY > 300) {
            scrollToTopBtn.classList.add('visible');
        } else {
            scrollToTopBtn.classList.remove('visible');
        }

        // Active nav link
        updateActiveNavLink();
    });

    // ─── 3. Smooth Scroll Navigation ──────────────────────────────────────────
    document.querySelectorAll('.nav-link, .hero-buttons a, .footer-col a').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    const offset = 80;
                    const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
                    window.scrollTo({ top, behavior: 'smooth' });
                }
                // Close mobile menu
                navLinks.classList.remove('active');
                hamburger.classList.remove('active');
            }
        });
    });

    function updateActiveNavLink() {
        const sections = document.querySelectorAll('.section, .hero');
        const navLinkElements = document.querySelectorAll('.nav-link');
        let current = '';

        sections.forEach(section => {
            const rect = section.getBoundingClientRect();
            if (rect.top <= 150) {
                current = section.id;
            }
        });

        navLinkElements.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    }

    // ─── 4. Hamburger Menu ────────────────────────────────────────────────────
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navLinks.classList.toggle('active');
    });

    // ─── 5. Dark Mode Toggle ──────────────────────────────────────────────────
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-mode');
        darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }

    darkModeToggle.addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        const isLight = document.body.classList.contains('light-mode');
        darkModeToggle.innerHTML = isLight ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
        // Redraw chart
        drawBarChart();
    });

    // ─── 6. Scroll to Top ─────────────────────────────────────────────────────
    scrollToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // ─── 7. Animated Counters ─────────────────────────────────────────────────
    let countersAnimated = false;
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !countersAnimated) {
                countersAnimated = true;
                animateCounters();
            }
        });
    }, { threshold: 0.3 });

    const dashboardSection = document.getElementById('dashboard');
    if (dashboardSection) counterObserver.observe(dashboardSection);

    function animateCounters() {
        document.querySelectorAll('.stat-value[data-target]').forEach(counter => {
            const target = parseInt(counter.dataset.target);
            const suffix = counter.dataset.suffix || '';
            const duration = 2000;
            const startTime = performance.now();

            function updateCounter(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                // Ease out cubic
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = Math.floor(eased * target);
                counter.textContent = current + suffix;
                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.textContent = target + suffix;
                }
            }
            requestAnimationFrame(updateCounter);
        });
    }

    // ─── 8. Section Fade In Animations ────────────────────────────────────────
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                sectionObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.section').forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(30px)';
        section.style.transition = 'opacity 0.7s ease, transform 0.7s ease';
        sectionObserver.observe(section);
    });

    // ─── 9. Live Monitoring ───────────────────────────────────────────────────
    monitorToggle.addEventListener('click', () => {
        if (isMonitoring) {
            stopMonitoring();
        } else {
            startMonitoring();
        }
    });

    function startMonitoring() {
        isMonitoring = true;
        monitorToggle.innerHTML = '<i class="fas fa-stop"></i> Stop Monitoring';
        monitorToggle.style.background = 'linear-gradient(135deg, #e17055, #d63031)';
        liveIndicator.classList.add('active');
        liveIndicator.querySelector('.live-text').textContent = 'LIVE';
        showToast('Monitoring started! Fetching sensor data...', 'success');
        fetchSensorData();
        monitorInterval = setInterval(fetchSensorData, 3000);
    }

    function stopMonitoring() {
        isMonitoring = false;
        clearInterval(monitorInterval);
        monitorToggle.innerHTML = '<i class="fas fa-play"></i> Start Monitoring';
        monitorToggle.style.background = '';
        liveIndicator.classList.remove('active');
        liveIndicator.querySelector('.live-text').textContent = 'OFFLINE';
        showToast('Monitoring stopped.', 'info');
    }

    async function fetchSensorData() {
        try {
            const response = await fetch('/api/monitor');
            const data = await response.json();
            updateGauges(data);
            addDataRow(data);
        } catch (err) {
            console.error('Monitor fetch error:', err);
        }
    }

    function updateGauges(data) {
        // Temperature gauge (0-50°C)
        const tempPercent = Math.min((data.temperature / 50) * 100, 100);
        document.getElementById('gaugeTemp').style.setProperty('--percentage', tempPercent);
        document.getElementById('tempValue').textContent = data.temperature;

        // Humidity gauge (0-100%)
        document.getElementById('gaugeHumidity').style.setProperty('--percentage', data.humidity);
        document.getElementById('humidityValue').textContent = data.humidity;

        // Soil Moisture gauge (0-100%)
        document.getElementById('gaugeMoisture').style.setProperty('--percentage', data.soilMoisture);
        document.getElementById('moistureValue').textContent = data.soilMoisture;

        // Light gauge (0-1000 lux)
        const lightPercent = Math.min((data.lightLevel / 1000) * 100, 100);
        document.getElementById('gaugeLight').style.setProperty('--percentage', lightPercent);
        document.getElementById('lightValue').textContent = Math.round(data.lightLevel);
    }

    function addDataRow(data) {
        const tbody = document.getElementById('dataFeedBody');
        // Remove empty row message
        const emptyRow = tbody.querySelector('.empty-row');
        if (emptyRow) emptyRow.remove();

        const row = document.createElement('tr');
        row.style.animation = 'fadeInUp 0.3s ease';
        row.innerHTML = `
            <td>${data.timestamp}</td>
            <td>${data.temperature}°C</td>
            <td>${data.humidity}%</td>
            <td>${data.soilMoisture}%</td>
            <td>${Math.round(data.lightLevel)} lux</td>
        `;
        tbody.insertBefore(row, tbody.firstChild);

        // Keep only last 10 rows
        while (tbody.children.length > 10) {
            tbody.removeChild(tbody.lastChild);
        }
    }

    // ─── 10. Image Upload & Analysis ──────────────────────────────────────────
    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
            handleFile(files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
        }
    });

    function handleFile(file) {
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            imagePreview.style.display = 'block';
            uploadArea.style.display = 'none';
            analyzeBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    removeImage.addEventListener('click', () => {
        selectedFile = null;
        previewImg.src = '';
        imagePreview.style.display = 'none';
        uploadArea.style.display = 'block';
        analyzeBtn.disabled = true;
        fileInput.value = '';
    });

    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // Show loading
        resultsPlaceholder.style.display = 'none';
        resultsContent.style.display = 'none';
        analysisLoading.style.display = 'block';

        const steps = analysisLoading.querySelectorAll('.loading-step');
        steps[0].className = 'loading-step done';
        steps[0].innerHTML = '<i class="fas fa-check-circle"></i> Image captured';
        steps[1].className = 'loading-step active';

        try {
            const formData = new FormData();
            formData.append('image', selectedFile);

            // Simulate delay for realism
            await new Promise(r => setTimeout(r, 1500));
            steps[1].className = 'loading-step done';
            steps[1].innerHTML = '<i class="fas fa-check-circle"></i> CNN model complete';
            steps[2].className = 'loading-step active';

            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            await new Promise(r => setTimeout(r, 800));
            steps[2].className = 'loading-step done';
            steps[2].innerHTML = '<i class="fas fa-check-circle"></i> Report generated';

            const data = await response.json();
            lastAnalysis = data;
            displayResults(data);

            // Add to reports
            reports.unshift(data);
            updateReportsTable();
            drawBarChart();

            // Show toast
            if (data.condition === 'Invalid - Not a Plant') {
                showToast(`❌ ${data.condition}`, 'error');
            } else if (data.condition !== 'Healthy') {
                showToast(`⚠️ ${data.condition} detected! Confidence: ${data.confidence}%`, 'warning');
                
                // Automatically send SMS if it's pest or damage
                if (data.condition === 'Pest Infestation' || data.condition === 'Physical Damage') {
                    autoSendSMS(data);
                }
            } else {
                showToast('✅ Plant appears healthy!', 'success');
            }

        } catch (err) {
            console.error('Analysis error:', err);
            showToast('Analysis failed. Please try again.', 'error');
            resultsPlaceholder.style.display = 'block';
            analysisLoading.style.display = 'none';
        }
    });

    function displayResults(data) {
        analysisLoading.style.display = 'none';
        resultsContent.style.display = 'block';

        document.getElementById('resultCondition').textContent = data.condition;

        const severityBadge = document.getElementById('resultSeverity');
        severityBadge.textContent = data.severity === 'none' ? 'Healthy' : data.severity;
        severityBadge.className = `severity-badge ${data.severity}`;

        document.getElementById('confidencePercent').textContent = data.confidence + '%';
        setTimeout(() => {
            document.getElementById('confidenceBar').style.width = data.confidence + '%';
        }, 100);

        document.getElementById('resultDescription').textContent = data.description;

        if (data.analysisDetails) {
            document.getElementById('resultModel').textContent = data.analysisDetails.modelUsed;
            document.getElementById('resultTime').textContent = data.analysisDetails.processingTime;
        }

        const recsList = document.getElementById('recommendationsList');
        recsList.innerHTML = '';
        data.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            recsList.appendChild(li);
        });
    }

    // Download Report
    document.getElementById('downloadReportBtn').addEventListener('click', async () => {
        if (!lastAnalysis) return;

        try {
            const response = await fetch('/api/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    plantName: lastAnalysis.filename || 'Unknown',
                    condition: lastAnalysis.condition,
                    confidence: lastAnalysis.confidence,
                    severity: lastAnalysis.severity,
                    recommendations: lastAnalysis.recommendations
                })
            });
            const report = await response.json();

            // Download as text file
            const blob = new Blob([report.reportText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `plant_report_${report.id}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('Report downloaded successfully!', 'success');
        } catch (err) {
            showToast('Failed to download report.', 'error');
        }
    });

    // Auto Send SMS Function
    async function autoSendSMS(data) {
        try {
            const phoneVal = document.getElementById('alertPhoneInput').value || 'Unknown';
            const response = await fetch('/api/alert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    condition: data.condition,
                    confidence: data.confidence,
                    severity: data.severity,
                    phone: phoneVal
                })
            });
            const alert = await response.json();
            // Add a small delay so it doesn't overlap perfectly with the analysis toast
            setTimeout(() => {
                showToast(`📱 Auto-SMS sent to ${phoneVal}: "${alert.message.substring(0, 45)}..."`, 'success');
            }, 800);
        } catch (err) {
            console.error('Failed to auto-send SMS', err);
        }
    }

    // Send Alert Button (Manual)
    document.getElementById('sendAlertBtn').addEventListener('click', async () => {
        if (!lastAnalysis) return;

        try {
            const phoneVal = document.getElementById('alertPhoneInput').value || 'Unknown';
            const response = await fetch('/api/alert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    condition: lastAnalysis.condition,
                    confidence: lastAnalysis.confidence,
                    severity: lastAnalysis.severity,
                    phone: phoneVal
                })
            });
            const alert = await response.json();
            showToast(`📱 SMS Alert sent to ${phoneVal}! "${alert.message.substring(0, 45)}..."`, 'success');
        } catch (err) {
            showToast('Failed to send alert.', 'error');
        }
    });

    // ─── 11. Plants Display ───────────────────────────────────────────────────
    async function loadPlants() {
        try {
            const response = await fetch('/api/plants');
            const data = await response.json();
            renderPlants(data.plants);
        } catch (err) {
            console.error('Failed to load plants:', err);
        }
    }

    function renderPlants(plants) {
        const grid = document.getElementById('plantGrid');
        grid.innerHTML = '';

        plants.forEach(plant => {
            const card = document.createElement('div');
            card.className = 'plant-card';
            card.innerHTML = `
                <div class="plant-card-image" style="background: ${plant.gradient}">
                    <i class="fas fa-leaf"></i>
                </div>
                <div class="plant-card-body">
                    <div class="plant-card-name">${plant.name}</div>
                    <div class="plant-card-species">${plant.species}</div>
                    <div class="plant-card-meta">
                        <span>
                            <span class="health-indicator ${plant.health}"></span>
                            <span class="plant-health-score">${plant.healthScore}%</span>
                        </span>
                        <span><i class="fas fa-tint"></i> ${plant.lastWatered}</span>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    // Add Plant button
    document.getElementById('addPlantBtn').addEventListener('click', () => {
        showToast('🌱 Add Plant feature coming soon!', 'info');
    });

    loadPlants();

    // ─── 12. Reports Table ────────────────────────────────────────────────────
    function updateReportsTable() {
        const tbody = document.getElementById('reportTableBody');
        tbody.innerHTML = '';

        if (reports.length === 0) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="6">No reports yet. Analyze a plant to generate reports.</td></tr>';
            return;
        }

        reports.forEach(report => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>#${report.id}</td>
                <td>${formatDate(report.timestamp)}</td>
                <td>${report.condition}</td>
                <td>${report.confidence}%</td>
                <td><span class="severity-badge ${report.severity}">${report.severity === 'none' ? 'Healthy' : report.severity}</span></td>
                <td><button class="btn-secondary btn-sm" onclick="downloadSingleReport('${report.id}')"><i class="fas fa-download"></i></button></td>
            `;
            tbody.appendChild(row);
        });
    }

    // Make downloadSingleReport global
    window.downloadSingleReport = (id) => {
        const report = reports.find(r => r.id === id);
        if (!report) return;
        const text = `Plant Health Report #${report.id}\nDate: ${report.timestamp}\nCondition: ${report.condition}\nConfidence: ${report.confidence}%\nSeverity: ${report.severity}\n\nRecommendations:\n${report.recommendations.map(r => '- ' + r).join('\n')}`;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${id}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    };

    // ─── 13. Bar Chart ────────────────────────────────────────────────────────
    function drawBarChart() {
        const canvas = document.getElementById('healthChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        // Calculate from reports
        let healthy = 65, mild = 20, moderate = 10, severe = 5;
        if (reports.length > 0) {
            const total = reports.length;
            healthy = Math.round((reports.filter(r => r.condition === 'Healthy').length / total) * 100) || 10;
            mild = Math.round((reports.filter(r => r.severity === 'medium').length / total) * 100) || 15;
            moderate = Math.round((reports.filter(r => r.severity === 'high').length / total) * 100) || 10;
            severe = Math.round((reports.filter(r => r.severity === 'critical').length / total) * 100) || 5;
        }

        const data = [healthy, mild, moderate, severe];
        const labels = ['Healthy', 'Mild', 'Moderate', 'Severe'];
        const colors = ['#00b894', '#fdcb6e', '#e17055', '#e84393'];

        const isLight = document.body.classList.contains('light-mode');
        const textColor = isLight ? '#333' : 'rgba(255,255,255,0.7)';
        const gridColor = isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.05)';

        // Set canvas size for HiDPI
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);

        const w = rect.width;
        const h = rect.height;
        const padding = { top: 30, right: 20, bottom: 50, left: 40 };
        const chartW = w - padding.left - padding.right;
        const chartH = h - padding.top - padding.bottom;

        ctx.clearRect(0, 0, w, h);

        // Grid lines
        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + (chartH / 4) * i;
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(w - padding.right, y);
            ctx.stroke();

            ctx.fillStyle = textColor;
            ctx.font = '11px Inter';
            ctx.textAlign = 'right';
            ctx.fillText(Math.round(100 - (100 / 4) * i) + '%', padding.left - 8, y + 4);
        }

        // Bars
        const barWidth = chartW / data.length * 0.55;
        const gap = chartW / data.length;

        data.forEach((val, i) => {
            const x = padding.left + gap * i + (gap - barWidth) / 2;
            const barH = (val / 100) * chartH;
            const y = padding.top + chartH - barH;

            // Bar gradient
            const grad = ctx.createLinearGradient(x, y, x, padding.top + chartH);
            grad.addColorStop(0, colors[i]);
            grad.addColorStop(1, colors[i] + '44');
            ctx.fillStyle = grad;

            // Rounded top bar
            const radius = 6;
            ctx.beginPath();
            ctx.moveTo(x + radius, y);
            ctx.lineTo(x + barWidth - radius, y);
            ctx.quadraticCurveTo(x + barWidth, y, x + barWidth, y + radius);
            ctx.lineTo(x + barWidth, padding.top + chartH);
            ctx.lineTo(x, padding.top + chartH);
            ctx.lineTo(x, y + radius);
            ctx.quadraticCurveTo(x, y, x + radius, y);
            ctx.closePath();
            ctx.fill();

            // Value on top
            ctx.fillStyle = textColor;
            ctx.font = 'bold 13px Inter';
            ctx.textAlign = 'center';
            ctx.fillText(val + '%', x + barWidth / 2, y - 10);

            // Label below
            ctx.fillStyle = textColor;
            ctx.font = '12px Inter';
            ctx.fillText(labels[i], x + barWidth / 2, padding.top + chartH + 24);
        });
    }

    // Initial chart draw
    setTimeout(drawBarChart, 500);
    window.addEventListener('resize', drawBarChart);

    // ─── 14. Toast Notifications ──────────────────────────────────────────────
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert-toast ${type}`;

        const icons = {
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle',
            info: 'fa-info-circle'
        };

        toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> <span>${message}</span>`;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('hiding');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    // ─── 15. Utility Functions ────────────────────────────────────────────────
    function formatDate(dateStr) {
        try {
            const d = new Date(dateStr);
            return d.toLocaleDateString('en-IN', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateStr;
        }
    }

    function getHealthColor(score) {
        if (score >= 80) return '#00b894';
        if (score >= 50) return '#fdcb6e';
        return '#e17055';
    }

    function generateId() {
        return Math.random().toString(36).substring(2, 10);
    }
});
