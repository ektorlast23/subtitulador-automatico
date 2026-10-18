const form = document.getElementById("form");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit");
const resultEl = document.getElementById("result");
const downloadsEl = document.getElementById("downloads");

function renderCues(container, cues) {
  container.innerHTML = "";
  cues.forEach((cue) => {
    const div = document.createElement("div");
    div.className = "cue";
    const time = document.createElement("span");
    time.className = "time";
    time.textContent = `${cue.start.toFixed(2)}s - ${cue.end.toFixed(2)}s`;
    const text = document.createElement("p");
    text.textContent = cue.lines.join(" ");
    div.appendChild(time);
    div.appendChild(text);
    container.appendChild(div);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fileInput = document.getElementById("file");
  if (!fileInput.files.length) return;

  const target = document.getElementById("direction").value;

  const data = new FormData();
  data.append("file", fileInput.files[0]);
  data.append("target", target);

  submitBtn.disabled = true;
  statusEl.textContent = "Procesando... esto puede tardar.";
  resultEl.classList.add("hidden");
  downloadsEl.classList.add("hidden");

  try {
    const response = await fetch("/api/transcribe", { method: "POST", body: data });
    if (!response.ok) {
      throw new Error(`Error HTTP ${response.status}`);
    }
    const payload = await response.json();
    renderCues(document.getElementById("en"), payload.en);

    const translated = Boolean(payload.translated);
    document.getElementById("col-es").classList.toggle("hidden", !translated);
    if (translated) {
      renderCues(document.getElementById("es"), payload.es);
    }

    const downloads = payload.downloads || {};
    const links = {
      "dl-srt-en": "srt_en",
      "dl-vtt-en": "vtt_en",
      "dl-srt-es": "srt_es",
      "dl-vtt-es": "vtt_es",
    };
    Object.entries(links).forEach(([id, kind]) => {
      const el = document.getElementById(id);
      const href = downloads[kind];
      el.href = href || "#";
      el.classList.toggle("hidden", !href);
    });

    resultEl.classList.remove("hidden");
    downloadsEl.classList.remove("hidden");
    statusEl.textContent = "Listo.";
  } catch (error) {
    statusEl.textContent = `Fallo: ${error.message}`;
  } finally {
    submitBtn.disabled = false;
  }
});
