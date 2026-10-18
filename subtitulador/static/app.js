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

  const data = new FormData();
  data.append("file", fileInput.files[0]);

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
    renderCues(document.getElementById("es"), payload.es);

    document.getElementById("dl-srt-en").href = payload.downloads.srt_en;
    document.getElementById("dl-srt-es").href = payload.downloads.srt_es;
    document.getElementById("dl-vtt-es").href = payload.downloads.vtt_es;

    resultEl.classList.remove("hidden");
    downloadsEl.classList.remove("hidden");
    statusEl.textContent = "Listo.";
  } catch (error) {
    statusEl.textContent = `Fallo: ${error.message}`;
  } finally {
    submitBtn.disabled = false;
  }
});
