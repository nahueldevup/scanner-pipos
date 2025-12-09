import { useEffect, useState, useRef, useCallback } from 'react';
import { Html5Qrcode } from "html5-qrcode";
import './App.css';

function App() {
  const [ultimoEscaneo, setUltimoEscaneo] = useState(null);
  const [camaraActiva, setCamaraActiva] = useState(false);
  const [codigoDetectado, setCodigoDetectado] = useState(null);
  const [error, setError] = useState(null);
  const scannerRef = useRef(null);

  // Función para iniciar cámara
  const iniciarCamara = useCallback(async () => {
    if (!scannerRef.current) return;
    
    try {
      await scannerRef.current.start(
        { facingMode: "environment" },
        {
          fps: 10,
          qrbox: { width: 280, height: 120 },
        },
        (decodedText) => {
          setCodigoDetectado(decodedText);
        },
        () => {}
      );
      setCamaraActiva(true);
      setError(null);
    } catch (err) {
      console.error("Error cámara:", err);
      setError("No se pudo acceder a la cámara");
    }
  }, []);

  useEffect(() => {
    const scanner = new Html5Qrcode("reader");
    scannerRef.current = scanner;

    // Iniciar cámara automáticamente
    iniciarCamara();

    return () => {
      if (scanner.isScanning) {
        scanner.stop().catch(console.error);
      }
    };
  }, [iniciarCamara]);

  // --- FUNCIÓN DEL BOTÓN "DISPARAR" ---
  const dispararEscaneo = async () => {
    if (!codigoDetectado) {
      if (navigator.vibrate) navigator.vibrate([50, 50, 50]);
      return;
    }

    try {
      if (navigator.vibrate) navigator.vibrate([100, 50, 100]);

      console.log("Disparo:", codigoDetectado);
      
      await fetch(`/api/escanear/${codigoDetectado}`, { method: 'POST' });
      
      const nuevoEscaneo = {
        codigo: codigoDetectado,
        hora: new Date().toLocaleTimeString(),
        id: Date.now()
      };
      
      setUltimoEscaneo(nuevoEscaneo);
      setCodigoDetectado(null);
      
      setTimeout(() => setUltimoEscaneo(null), 2000);

    } catch (err) {
      console.error("Error disparando:", err);
    }
  };
  return (
    <div className="scanner-container">
      {/* Header */}
      <header className="scanner-header">
        <div className="header-logo"></div>
        <h1>Scanner Pipos</h1>
        <div className="status-indicator">
          <span className={`status-dot ${camaraActiva ? 'active' : ''}`}></span>
          {camaraActiva ? 'Listo' : 'Iniciando...'}
        </div>
      </header>

      {/* Área del escáner con guía */}
      <div className="scanner-area">
        <div id="reader"></div>

        {/* Código detectado en tiempo real */}
        {codigoDetectado && (
          <div className="detected-code">
            <span className="detected-label">Código detectado:</span>
            <span className="detected-value">{codigoDetectado}</span>
          </div>
        )}

        {/* Feedback del último escaneo enviado */}
        {ultimoEscaneo && (
          <div className="scan-feedback">
            <span className="check-icon">✓</span>
            <span className="scan-code">{ultimoEscaneo.codigo}</span>
          </div>
        )}

        {error && <div className="error-message">{error}</div>}
      </div>

      {/* Botón de disparo tipo cámara */}
      <div className="shutter-container">
        <button 
          className={`shutter-button ${codigoDetectado ? 'ready' : ''}`}
          onClick={dispararEscaneo}
          disabled={!camaraActiva}
        >
          <span className="shutter-inner"></span>
        </button>
        <p className="shutter-hint">
          {codigoDetectado ? '¡Toca para enviar!' : 'Apunta a un código'}
        </p>
      </div>
    </div>
  );
}

export default App;