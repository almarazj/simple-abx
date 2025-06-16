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
        this.volume = 0.7;
        this.crossfadeDuration = 0.2; // 100ms crossfade
        this.gainNodes = {}; // Will be initialized when context is created

        this.responseTimeoutActive = false; // Prevent rapid response clicks
        this.setupEventListeners();
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

    async loadAudioFiles(stimulusA, stimulusB, stimulusX) {
        await this.initializeAudioContext(); // Initialize context first
        
        const basePath = '/static/audio/test_files/';
        const files = { A: stimulusA, B: stimulusB, X: stimulusX };

        // Stop any current playback and reset
        this.stopAllSources();

        for (const key of Object.keys(files)) {
            const response = await fetch(basePath + files[key]);
            const arrayBuffer = await response.arrayBuffer();
            this.buffers[key] = await this.context.decodeAudioData(arrayBuffer);
            console.log(`Audio cargado: ${files[key]}`);
        }

        this.resetPlayback();
        this.updateButtonStates();
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
        this.crossfadeToStimulus(stimulus);
        this.currentStimulus = stimulus;
        this.updateButtonStates();
    }

    crossfadeToStimulus(targetStimulus) {
        const now = this.context.currentTime;
        const fadeDuration = this.crossfadeDuration;

        // Fade out current stimulus
        Object.keys(this.gainNodes).forEach(stimulus => {
            if (stimulus !== targetStimulus) {
                this.gainNodes[stimulus].gain.linearRampToValueAtTime(0, now + fadeDuration);
            }
        });

        // Fade in target stimulus
        this.gainNodes[targetStimulus].gain.linearRampToValueAtTime(this.volume, now + fadeDuration);
    }

    stopAllSources() {
        if (this.sources) {
            Object.values(this.sources).forEach(source => {
                try {
                    source.stop();
                    source.disconnect();
                } catch (e) {}
            });
        }
        this.sources = {};
        this.isPlaying = false;

        // Reset all gains to silent
        if (this.gainNodes) {
            Object.keys(this.gainNodes).forEach(stimulus => {
                this.gainNodes[stimulus].gain.value = 0;
            });
        }
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

    submitResponse(response) {
        if (this.responseTimeoutActive) {
            console.log('Response timeout active - ignoring click');
            return;
        }

        if (!window.comparisonData && !this.pendingComparison) {
            console.error('No comparison data available - cannot submit response');
            alert('Error: No hay datos de comparación disponibles. Por favor recarga la página.');
            return;
        }

        this.responseTimeoutActive = true;
        this.resetPlayback();
        // No mostrar confirmación aquí, esperar a la respuesta del backend
        // this.showResponseConfirmation(response);
        
        // Deshabilita los botones de estímulo
        ['btn-a', 'btn-b', 'btn-x'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.disabled = true;
        });

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
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            } else if (data.status === "continue") {
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
            setTimeout(() => {
                this.responseTimeoutActive = false;
            }, 500);
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
            }, 200); // Wait for button fade out
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
                    ['btn-a', 'btn-b', 'btn-x'].forEach(id => {
                        const btn = document.getElementById(id);
                        if (btn) btn.disabled = false;
                    });
                }, 50); // Small delay for smooth transition
            }, 200); // Wait for confirmation fade out
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
        setTimeout(() => {
            // Hide confirmation and show response buttons again
            this.hideResponseConfirmation();
            // Clear response timeout to allow new responses
            this.responseTimeoutActive = false;
        }, 500);
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
    // Prevent multiple controller instances
    if (window.abxController) {
        console.warn('ABX Controller already initialized');
        return;
    }
    
    let abxController = null;

    const isTestPage = document.getElementById('btn-a') !== null;
    if (isTestPage && window.comparisonData && window.abxController) {
        // Precarga automática de los audios de la primera comparación
        await window.abxController.loadAudioFiles(
            window.comparisonData.stimulus_a,
            window.comparisonData.stimulus_b,
            window.comparisonData.stimulus_x
        );
    }
    const isCalibrationPage = document.getElementById('start-test-btn') !== null;
    
    if (isTestPage || isCalibrationPage) {
        abxController = new ABXAudioController();
        window.abxController = abxController;
        
        if (isTestPage) {

            const comparisonData = window.comparisonData;
            if (comparisonData) {
                abxController.pendingComparison = comparisonData;
            } else {
                // No comparison data available - disable response buttons and show warning
                console.warn('No comparison data available - disabling response buttons');
                
                // Disable all response buttons
                ['response-a', 'response-b', 'response-tie'].forEach(id => {
                    const btn = document.getElementById(id);
                    if (btn) {
                        btn.disabled = true;
                        btn.style.opacity = '0.5';
                        btn.style.cursor = 'not-allowed';
                        btn.title = 'No hay datos de comparación disponibles';
                    }
                });
                
                // Disable audio buttons too
                ['btn-a', 'btn-b', 'btn-x'].forEach(id => {
                    const btn = document.getElementById(id);
                    if (btn) {
                        btn.disabled = true;
                        btn.style.opacity = '0.5';
                        btn.style.cursor = 'not-allowed';
                        btn.title = 'No hay datos de comparación disponibles';
                    }
                });
                
                // Show error message to user
                const testContent = document.querySelector('.test-container');
                if (testContent) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'alert alert-warning';
                    errorDiv.style.cssText = 'background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;';
                    errorDiv.innerHTML = '<strong>⚠️ Error:</strong> No hay datos de comparación disponibles. Por favor, <a href="/" style="color: #856404; text-decoration: underline;">vuelve al inicio</a> e inicia el test correctamente.';
                    testContent.insertBefore(errorDiv, testContent.firstChild);
                }
            }
        }
    }

    // --- CALIBRACIÓN SOLO WEB AUDIO API ---
    const playCalibrationBtn = document.getElementById('play-calibration');
    if (playCalibrationBtn) {
        let calibrationBuffer = null;
        let calibrationSource = null;
        let calibrationContext = null;
        let isPlaying = false;

        async function loadCalibrationBuffer() {
            if (calibrationBuffer) return calibrationBuffer;
            if (!calibrationContext) {
                calibrationContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            const response = await fetch('/static/audio/calibration/calibration_tone.wav');
            const arrayBuffer = await response.arrayBuffer();
            calibrationBuffer = await calibrationContext.decodeAudioData(arrayBuffer);
            return calibrationBuffer;
        }

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
                const buffer = await loadCalibrationBuffer();
                calibrationSource = calibrationContext.createBufferSource();
                calibrationSource.buffer = buffer;
                calibrationSource.connect(calibrationContext.destination);
                calibrationSource.start(0);
                isPlaying = true;
                calibrationSource.onended = function() {
                    playCalibrationBtn.textContent = 'Reproducir Audio de Calibración';
                    isPlaying = false;
                };
            } catch (error) {
                console.error('Error playing calibration:', error);
                playCalibrationBtn.textContent = 'Reproducir Audio de Calibración';
                isPlaying = false;
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
