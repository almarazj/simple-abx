// abx_controller.js

class ABXAudioController {
    constructor() {
        this.context = null; // Lazy-load AudioContext
        this.buffers = {};  // A, B, X
        this.currentSource = null;
        this.currentStimulus = null; // No default selection
        this.playbackStartTime = 0;
        this.audioOffset = 0;
        this.isPlaying = false;
        this.volume = 1;
        this.crossfadeDuration = 0.1; // 100ms crossfade
        this.gainNodes = {}; // Will be initialized when context is created
        this.setupEventListeners();
    }

    getButtonsContainer() {
        const a = document.getElementById('btn-a');
        const b = document.getElementById('btn-b');
        const x = document.getElementById('btn-x');
        if (!a) return document.body;

        let container = a.parentElement;
        const containsAll = (el) => el && el.contains(a) && (!b || el.contains(b)) && (!x || el.contains(x));
        while (container && !containsAll(container)) {
            container = container.parentElement;
        }
        return container || document.body;
    }

    setLoading(isLoading, message = 'Cargando audios...', options = {}) {
        // Unificar: permite targetear contenedor y controles específicos
        const defaultIds = ['btn-a', 'btn-b', 'btn-x', 'response-a', 'response-b', 'response-tie'];
        const disableIds = Array.isArray(options.disableIds) ? options.disableIds : defaultIds;
        const hideIds = Array.isArray(options.hideIds) ? options.hideIds : [];
        const container = options.container instanceof HTMLElement ? options.container : this.getButtonsContainer();

        // Deshabilitar controles solicitados
        disableIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.disabled = isLoading;
        });

        // Ocultar/mostrar elementos solicitados (sin romper layout)
        hideIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.visibility = isLoading ? 'hidden' : '';
        });

        // Crear el overlay si no existe
    if (!this.loadingOverlayEl) {
            const pos = window.getComputedStyle(container).position;
            if (pos === 'static' || !pos) container.style.position = 'relative';

            const overlay = document.createElement('div');
            overlay.id = 'audio-loading-overlay';
            overlay.className = 'audio-loading-overlay';

            const label = document.createElement('div');
            label.id = 'audio-loading-label';
            label.textContent = message;
            overlay.appendChild(label);

            container.appendChild(overlay);
            this.loadingOverlayEl = overlay;
            this.loadingOverlayLabel = label;
        } else if (this.loadingOverlayEl.parentElement !== container) {
            // Mover overlay si el contenedor cambió
            const pos = window.getComputedStyle(container).position;
            if (pos === 'static' || !pos) container.style.position = 'relative';
            this.loadingOverlayEl.parentElement.removeChild(this.loadingOverlayEl);
            container.appendChild(this.loadingOverlayEl);
        }

        // Actualiza el mensaje si cambia
        if (this.loadingOverlayLabel && typeof message === 'string') {
            this.loadingOverlayLabel.textContent = message;
        }

        // Transiciones controladas por CSS mediante la clase .show
    if (isLoading) {
            this.loadingOverlayEl.classList.add('show');
        } else {
            this.loadingOverlayEl.classList.remove('show');
        }
    }

    async initializeAudioContext() {
        if (!this.context) {
            this.context = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create separate gain nodes for each stimulus for crossfading
            this.gainNodes = {
                A: this.context.createGain(),
                B: this.context.createGain(),
                X: this.context.createGain()
            };

            // Initialize all gain nodes to 0 (silent)
            Object.values(this.gainNodes).forEach(gainNode => {
                gainNode.gain.value = 0;
                gainNode.connect(this.context.destination);
            });
        }
    }

    updateButtonStates() {
        // Update stimulus buttons
        ['btn-a', 'btn-b', 'btn-x'].forEach(btnId => {
            const btn = document.getElementById(btnId);
            if (!btn) return;

            const stimulus = btnId.split('-')[1].toUpperCase();
            const isCurrentStimulus = this.currentStimulus === stimulus;

            btn.classList.toggle('current-stimulus', isCurrentStimulus);
        });
    }

    startAllSources() {
        const now = this.context.currentTime;
        this.sources = {};

        // Create and start all audio sources simultaneously
        ['A', 'B', 'X'].forEach(stimulus => {
            if (this.buffers[stimulus]) {
                const bufferSource = this.context.createBufferSource();
                bufferSource.buffer = this.buffers[stimulus];
                bufferSource.connect(this.gainNodes[stimulus]);
                
                bufferSource.start(0, this.audioOffset);
                this.sources[stimulus] = bufferSource;

                // Handle source ending
                bufferSource.onended = () => {
                    this.handleSourceEnded();
                };
            }
        });

        this.playbackStartTime = now;
    }

    handleSourceEnded() {
        this.isPlaying = false;
        this.sources = {};
        this.currentStimulus = null;
        this.updateButtonStates();
    }

    async switchToStimulus(stimulus) {
        // Cargar archivos en el primer clic si no están cargados
        if (this.pendingComparison && Object.keys(this.buffers).length === 0) {
            await this.loadAudioFiles(
                this.pendingComparison.stimulus_a,
                this.pendingComparison.stimulus_b,
                this.pendingComparison.stimulus_x
            );
            this.pendingComparison = null; // Limpiar después de cargar
        }

        if (!this.buffers[stimulus]) return;

        // Si el usuario presiona el mismo botón que ya está reproduciendo, detener y volver al principio
        if (this.isPlaying && this.currentStimulus === stimulus) {
            this.resetPlayback();
            this.isPlaying = false;
            this.updateButtonStates();
            // Limpia la clase de todos los botones (por si acaso)
            ['btn-a', 'btn-b', 'btn-x'].forEach(id => {
                const btn = document.getElementById(id);
                if (btn) btn.classList.remove('current-stimulus');
            });
            return;
        }

        // Si no está reproduciendo, iniciar reproducción
        if (!this.isPlaying) {
            this.startAllSources();
            this.isPlaying = true;
        }

        // Cambiar de estímulo normalmente
        this.currentStimulus = stimulus;
        this.crossfadeToStimulus(stimulus);
        this.updateButtonStates();
    }

    crossfadeToStimulus(targetStimulus) {
        const now = this.context.currentTime;
        const fadeDuration = this.crossfadeDuration;

        // Fade out current stimulus
        Object.keys(this.gainNodes).forEach(stimulus => {
            const gainNode = this.gainNodes[stimulus];
            gainNode.gain.setValueAtTime(gainNode.gain.value, now);
            if (stimulus !== targetStimulus) {
                this.gainNodes[stimulus].gain.linearRampToValueAtTime(0, now + fadeDuration);
            }
        });

        // Fade in target stimulus
        const targetGain = this.gainNodes[targetStimulus].gain;
        targetGain.setValueAtTime(targetGain.value, now);
        targetGain.linearRampToValueAtTime(this.volume, now + fadeDuration);
    }

    stopAllSources() {
        if (!this.sources || !this.gainNodes) return;

        const fadeOutTime = 0.05; // segundos
        const now = this.context.currentTime;
        const stopTime = now + fadeOutTime;

        // Fade-out con precisión
        for (const stimulus of Object.keys(this.gainNodes)) {
            const gainNode = this.gainNodes[stimulus].gain;
            gainNode.cancelScheduledValues(now);
            gainNode.setValueAtTime(gainNode.value, now);
            gainNode.linearRampToValueAtTime(0.0, stopTime);
        }

        // Detener los sources justo después del fade-out
        for (const [stimulus, source] of Object.entries(this.sources)) {
            try {
                // Programar stop exactamente al final del fade
                source.stop(stopTime);
            } catch (e) {
                console.warn(`Error al detener source de ${stimulus}:`, e);
            }
        }

        // Limpiar después del stopTime con un pequeño margen
        setTimeout(() => {
            for (const source of Object.values(this.sources)) {
                try {
                    source.disconnect();
                } catch (e) {}
            }
            this.sources = {};
        }, (fadeOutTime + 0.05) * 1000);

        this.isPlaying = false;
        this.currentStimulus = null;
    }

    resetPlayback() {
        this.stopAllSources();
        this.audioOffset = 0;
        this.currentStimulus = null; // No default selection
        // Reset gains - all should be silent initially
        if (this.gainNodes) {
            Object.keys(this.gainNodes).forEach(stimulus => {
                this.gainNodes[stimulus].gain.value = 0;
            });
        }
        // Limpia la clase de todos los botones
        ['btn-a', 'btn-b', 'btn-x'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.classList.remove('current-stimulus');
        });
    }

    setVolume(volume) {
        this.volume = volume;
        // Update the gain of the currently active stimulus
        if (this.gainNodes[this.currentStimulus]) {
            this.gainNodes[this.currentStimulus].gain.value = volume;
        }
    }

    async loadAudioFiles(stimulusA, stimulusB, stimulusX) {
        await this.initializeAudioContext();

        this.stopAllSources();
        this.setLoading(true);

        try {
            const [audioA, audioB, audioX] = await Promise.all([
                this.fetchAndDecodeAudio(stimulusA),
                this.fetchAndDecodeAudio(stimulusB),
                this.fetchAndDecodeAudio(stimulusX)
            ]);

            this.buffers = {
                A: audioA,
                B: audioB,
                X: audioX
            };

            console.log("Audios cargados en buffers:", this.buffers);

            this.resetPlayback();
            this.updateButtonStates();
        } catch (error) {
            console.error("Error cargando archivos de audio:", error);
            alert("Hubo un problema al cargar los audios. Por favor, recarga la página.");
        } finally {
            this.setLoading(false); // Rehabilita botones y oculta indicador
        }
    }

    async fetchAndDecodeAudio(filename) {
        const signedUrlResponse = await fetch(`/audio-url?filename=test_files/${filename}`);
        const { url } = await signedUrlResponse.json();

        const audioResponse = await fetch(url);
        const arrayBuffer = await audioResponse.arrayBuffer();

        return await this.context.decodeAudioData(arrayBuffer);
    }

    preloadNextAudio(comparison) {
        if (!comparison) return;

        Promise.all([
            this.fetchAndDecodeAudio(comparison.stimulus_a),
            this.fetchAndDecodeAudio(comparison.stimulus_b),
            this.fetchAndDecodeAudio(comparison.stimulus_x)
        ]).then(([audioA, audioB, audioX]) => {
            this.nextAudioBuffer = {
                a: audioA,
                b: audioB,
                x: audioX
            };
        }).catch(error => {
            console.error("Error pre-cargando audios:", error);
        });
    }

    submitResponse(response) {

        if (!window.comparisonData && !this.pendingComparison) {
            console.error('No comparison data available - cannot submit response');
            alert('Error: No hay datos de comparación disponibles. Por favor recarga la página.');
            return;
        }

    this.resetPlayback();
    // Unificado: muestra overlay y deshabilita botones de audio
    this.setLoading(true, 'Cargando audios...');

        // Obtén el user_id de la URL
        const params = new URLSearchParams(window.location.search);
        const userId = params.get('user_id');

        fetch('/submit_response', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                response: response,
                user_id: userId // Asegúrate de enviar el user_id al backend
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
    .then(data => {
            // Mostrar confirmación y avanzar barra de progreso al mismo tiempo
            if (data.status === "completed" && data.redirect) {
                window.testFinished = true; // Evita el warning en el último submit
                this.showResponseConfirmation(response, data.current || 1, data.total || 1);
        // Oculta overlay ya que no cargaremos más audios
        this.setLoading(false);
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            } else if (data.status === "continue") {
                this.preloadNextAudio(data.next_comparison);
                this.showResponseConfirmation(response, data.current, data.total);
                setTimeout(() => {
                    this.loadNextComparison(data.next_comparison, data.current, data.total);
                }, 1000);
            }
        })
    .catch(error => {
            console.error('Error enviando respuesta:', error);
            alert('Error enviando respuesta. Por favor intenta nuevamente.');
            this.hideResponseConfirmation();
        // Rehabilitar UI si falló
        this.setLoading(false);
        });
    }

    showResponseConfirmation(response, current, total) {
        const responseOptions = document.querySelector('.response-options');
        const confirmationDiv = document.getElementById('response-confirmation');
        const confirmationText = document.getElementById('confirmation-text');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        
        if (responseOptions && confirmationDiv && confirmationText) {
            // Fade out buttons first
            responseOptions.style.transition = 'opacity 0.3s ease-out';
            responseOptions.style.opacity = '0';
            
            setTimeout(() => {
                // Hide buttons completely
                responseOptions.style.display = 'none';
                
                // Update confirmation message based on response
                let message = 'Respuesta registrada';
                switch(response) {
                    case 'a':
                        message = 'Respuesta registrada: Audio A = X';
                        break;
                    case 'b':
                        message = 'Respuesta registrada: Audio B = X';
                        break;
                    case 'tie':
                        message = 'Respuesta registrada: No logro identificarlo';
                        break;
                }
                confirmationText.textContent = message;
                
                // Show confirmation with fade in
                confirmationDiv.classList.add('show');

                // Avanza la barra de progreso y el texto al mismo tiempo
                if (progressFill && progressText && typeof current === "number" && typeof total === "number") {
                    const percentage = (current / total) * 100;
                    progressFill.style.width = percentage + '%';
                    progressText.textContent = `Comparación ${current} de ${total}`;
                }
            }, 300); // Wait for button fade out
        }
    }

    hideResponseConfirmation() {
        const responseOptions = document.querySelector('.response-options');
        const confirmationDiv = document.getElementById('response-confirmation');
        
        if (responseOptions && confirmationDiv) {
            // Fade out confirmation
            confirmationDiv.style.transition = 'opacity 0.3s ease-out';
            confirmationDiv.style.opacity = '0';
            
            setTimeout(() => {
                // Hide confirmation completely
                confirmationDiv.classList.remove('show');
                confirmationDiv.style.opacity = ''; // Reset opacity
                
                // Show buttons with fade in
                responseOptions.style.display = 'flex';
                responseOptions.style.opacity = '0';
                
                setTimeout(() => {
                    responseOptions.style.opacity = '1';
                }, 50); // Small delay for smooth transition
            }, 300); // Wait for confirmation fade out
        }
    }

    async loadNextComparison(comparison, current, total) {
        await this.loadAudioFiles(comparison.stimulus_a, comparison.stimulus_b, comparison.stimulus_x);
        // El avance de barra y texto ahora ocurre en showResponseConfirmation
        // Limpia la clase de todos los botones al cargar la nueva comparación
        ['btn-a', 'btn-b', 'btn-x'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.classList.remove('current-stimulus');
        });
        // Oculta confirmación; los botones se rehabilitan cuando setLoading(false)
        this.hideResponseConfirmation();
    }

    setupEventListeners() {
        // Stimulus selection listeners (A, B, X buttons)
        ['btn-a', 'btn-b', 'btn-x'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.addEventListener('click', async () => {
                    await this.initializeAudioContext();
                    const stimulus = id.split('-')[1].toUpperCase();
                    this.switchToStimulus(stimulus);
                });
            }
        });

        // Response buttons
        ['response-a', 'response-b', 'response-tie'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.addEventListener('click', () => this.submitResponse(id.split('-')[1]));
            }
        });
    }

}

document.addEventListener('DOMContentLoaded', async function() {
    if (window.abxController) {
        console.warn('ABX Controller already initialized');
        return;
    }

    let abxController = null;
    let calibrationBuffer = null;
    let calibrationContext = null;

    async function loadCalibrationBuffer() {
        if (calibrationBuffer) return calibrationBuffer;
        if (!calibrationContext) {
            calibrationContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        const res = await fetch('/audio-url?filename=calibration/calibration_tone.wav');
        const { url } = await res.json();
        const response = await fetch(url);

        const arrayBuffer = await response.arrayBuffer();
        calibrationBuffer = await calibrationContext.decodeAudioData(arrayBuffer);
        return calibrationBuffer;
    }

    const isTestPage = document.getElementById('btn-a') !== null;
    const isCalibrationPage = document.getElementById('start-test-btn') !== null;

    if (isTestPage && window.comparisonData && !window.abxController) {
        abxController = new ABXAudioController();
        window.abxController = abxController;
        abxController.pendingComparison = window.comparisonData;

        await abxController.loadAudioFiles(
            window.comparisonData.stimulus_a,
            window.comparisonData.stimulus_b,
            window.comparisonData.stimulus_x
        );
    }

    if (isCalibrationPage) {
        abxController = new ABXAudioController();
        window.abxController = abxController;

        // Oculta el botón de calibración mientras carga el buffer por primera vez
        const calibrationBtn = document.getElementById('play-calibration');
        if (calibrationBtn) {
            abxController.setLoading(true, 'Cargando audios...', {
                container: calibrationBtn.parentElement || document.body,
                disableIds: [],
                hideIds: ['play-calibration']
            });
        }

        loadCalibrationBuffer().then(() => {
            console.log("Audio de calibración precargado.");
            if (calibrationBtn) {
                abxController.setLoading(false, undefined, {
                    container: calibrationBtn.parentElement || document.body,
                    disableIds: [],
                    hideIds: ['play-calibration']
                });
            }
        }).catch(err => {
            console.error("Error al precargar el audio de calibración:", err);
            if (calibrationBtn) {
                abxController.setLoading(false, undefined, {
                    container: calibrationBtn.parentElement || document.body,
                    disableIds: [],
                    hideIds: ['play-calibration']
                });
            }
        });
    }

    // --- Botón de calibración ---
    const playCalibrationBtn = document.getElementById('play-calibration');
    if (playCalibrationBtn) {
        let calibrationSource = null;
        let isPlaying = false;

        async function playCalibration() {
            if (isPlaying) {
                if (calibrationSource) {
                    calibrationSource.stop();
                }
                playCalibrationBtn.textContent = 'Reproducir Audio de Calibración';
                isPlaying = false;
                return;
            }

            try {
                playCalibrationBtn.textContent = 'Pausar Audio de Calibración';

                if (!calibrationContext) {
                    calibrationContext = new (window.AudioContext || window.webkitAudioContext)();
                }
                // Ocultar el botón mientras se prepara el audio
                abxController.setLoading(true, 'Cargando audios...', {
                    container: playCalibrationBtn.parentElement || document.body,
                    disableIds: [],
                    hideIds: ['play-calibration']
                });

                const buffer = await loadCalibrationBuffer();
                calibrationSource = calibrationContext.createBufferSource();
                calibrationSource.buffer = buffer;
                calibrationSource.connect(calibrationContext.destination);
                calibrationSource.start(0);
                isPlaying = true;

                // Mostrar nuevamente el botón durante la reproducción
                abxController.setLoading(false, undefined, {
                    container: playCalibrationBtn.parentElement || document.body,
                    disableIds: [],
                    hideIds: ['play-calibration']
                });

                calibrationSource.onended = function() {
                    playCalibrationBtn.textContent = 'Reproducir Audio de Calibración';
                    isPlaying = false;
                };
            } catch (error) {
                console.error('Error playing calibration:', error);
                playCalibrationBtn.textContent = 'Reproducir Audio de Calibración';
                isPlaying = false;
                abxController.setLoading(false, undefined, {
                    container: playCalibrationBtn.parentElement || document.body,
                    disableIds: [],
                    hideIds: ['play-calibration']
                });
            }
        }

        playCalibrationBtn.addEventListener('click', playCalibration);
    }
});


document.addEventListener('DOMContentLoaded', function() {
    const startTestBtn = document.getElementById('start-test-btn');
    if (startTestBtn) {
        startTestBtn.addEventListener('click', function() {
            const params = new URLSearchParams(window.location.search);
            const userId = params.get('user_id');
            if (userId) {
                window.location.href = `/test?user_id=${userId}`;
            } else {
                alert("No se encontró el identificador de usuario.");
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const shareBtn = document.getElementById('share-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', async function() {
            const shareData = {
                title: 'Test ABX',
                text: 'Ayúdame completando este test de percepción auditiva! (duración máx: 10 min):',
                url: window.location.origin + '/'
            };
            if (navigator.share) {
                try {
                    await navigator.share(shareData);
                } catch (err) {
                    // Usuario canceló o error
                }
            } else {
                // Copia mensaje + enlace al portapapeles
                const textToCopy = `${shareData.text}\n${shareData.url}`;
                try {
                    await navigator.clipboard.writeText(textToCopy);
                    alert('¡Enlace copiados al portapapeles!');
                } catch (err) {
                    alert('No se pudo copiar el mensaje. Copia manualmente:\n' + textToCopy);
                }
            }
        });
    }
});
