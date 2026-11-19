
"use strict";

// IRON FLIGHT — JARVIS VOICE ASSISTANT

(() => {
  const voiceSupported =
    "speechSynthesis" in window &&
    "SpeechSynthesisUtterance" in window;

  let voiceEnabled = false;
  let selectedVoice = null;
  let lastAnnouncement = "";
  let lastAnnouncementTime = 0;

  function selectVoice() {
    if (!voiceSupported) return;

    const voices = window.speechSynthesis.getVoices();

    selectedVoice =
      voices.find(v =>
        v.lang.toLowerCase() === "en-gb" &&
        /ryan|george|daniel|male/i.test(v.name)
      ) ||
      voices.find(v =>
        v.lang.toLowerCase().startsWith("en-gb")
      ) ||
      voices.find(v =>
        v.lang.toLowerCase().startsWith("en")
      ) ||
      null;
  }

  function speak(message) {
    if (!voiceEnabled || !voiceSupported || !message) return;

    const now = Date.now();

    // Prevent rapid duplicate announcements.
    if (
      message === lastAnnouncement &&
      now - lastAnnouncementTime < 1200
    ) {
      return;
    }

    lastAnnouncement = message;
    lastAnnouncementTime = now;

    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(message);

    speech.lang = "en-GB";
    speech.rate = 0.94;
    speech.pitch = 0.85;
    speech.volume = 1;

    selectVoice();

    if (selectedVoice) {
      speech.voice = selectedVoice;
    }

    window.speechSynthesis.speak(speech);
  }

  function announce(message) {
    speak(message);
  }

  function setVoiceEnabled(enabled) {
    voiceEnabled = Boolean(enabled) && voiceSupported;

    if (!voiceEnabled && voiceSupported) {
      window.speechSynthesis.cancel();
    }

    updateVoiceButton();

    if (voiceEnabled) {
      speak("JARVIS online. All systems operational.");
    }
  }

  function updateVoiceButton() {
    const button = document.getElementById("jarvis-voice");

    if (!button) return;

    button.textContent = voiceEnabled
      ? "VOICE ON"
      : "VOICE OFF";

    button.setAttribute(
      "aria-pressed",
      String(voiceEnabled)
    );
  }

  function createVoiceButton() {
    let button = document.getElementById("jarvis-voice");

    if (!button) {
      button = document.createElement("button");
      button.id = "jarvis-voice";
      button.type = "button";
      button.textContent = "VOICE OFF";

      Object.assign(button.style, {
        position: "fixed",
        right: "20px",
        bottom: "20px",
        zIndex: "9999",
        padding: "12px 18px",
        background: "rgba(5, 20, 38, 0.92)",
        color: "#8beeff",
        border: "1px solid #39cfff",
        borderRadius: "8px",
        fontFamily: "Arial, sans-serif",
        fontWeight: "bold",
        cursor: "pointer"
      });

      document.body.appendChild(button);
    }

    button.addEventListener("click", () => {
      setVoiceEnabled(!voiceEnabled);
    });

    updateVoiceButton();
  }

  // Announcements from advanced combat systems.
  window.addEventListener("ironflight:combat", event => {
    const message = event.detail?.message;

    if (message) announce(message);
  });

  // Browser voices may load asynchronously.
  if (voiceSupported) {
    selectVoice();

    window.speechSynthesis.addEventListener(
      "voiceschanged",
      selectVoice
    );
  }

  // Make JARVIS available to other scripts.
  window.IronFlightJarvis = {
    speak,
    announce,
    enable: () => setVoiceEnabled(true),
    disable: () => setVoiceEnabled(false),
    isEnabled: () => voiceEnabled
  };

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      createVoiceButton,
      { once: true }
    );
  } else {
    createVoiceButton();
  }
})();
