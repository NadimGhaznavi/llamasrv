"use strict";

const data = JSON.parse(document.getElementById("page-data").textContent);
const t = (key) => data.messages[`ui.${key}`];
const form = document.getElementById("configuration-form");
const fields = document.getElementById("configuration-fields");
const feedback = document.getElementById("feedback");
const restart = document.getElementById("restart");
const refresh = document.getElementById("refresh");
const dialog = document.getElementById("restart-dialog");
let busy = false;
let checking = false;

function settings() {
  return {
    http_port: Number(form.elements.http_port.value),
    llm_port: Number(form.elements.llm_port.value),
    context_size: Number(form.elements.context_size.value),
    metrics: form.elements.metrics.checked,
    jinja: form.elements.jinja.checked,
    model: form.elements.model.value,
    mmproj: form.elements.mmproj.value || null,
  };
}
let saved = JSON.stringify(settings());

function updateDirty() {
  const dirty = JSON.stringify(settings()) !== saved;
  document.getElementById("dirty-state").hidden = !dirty;
  restart.disabled = dirty || busy;
}
function showFeedback(message, error = false) {
  feedback.textContent = message;
  feedback.classList.toggle("error", error);
}
function setBusy(value) {
  busy = value;
  fields.disabled = value;
  form.setAttribute("aria-busy", String(value));
  updateDirty();
}
function url(path) {
  const target = new URL(path, location.origin);
  target.searchParams.set("lang", data.locale);
  return target;
}
async function request(path, values) {
  let response, result;
  try {
    response = await fetch(url(path), {
      method: "POST",
      headers: { "Content-Type": "application/json", [data.request_header]: data.request_marker },
      body: JSON.stringify(values),
      signal: AbortSignal.timeout(data.timeout_ms),
    });
    result = await response.json();
  } catch {
    throw new Error(t("request_failed"));
  }
  if (!response.ok) throw new Error(result.error || t("operation_failed"));
  return result;
}
async function checkStatus() {
  if (checking) return;
  checking = true;
  refresh.disabled = true;
  try {
    const response = await fetch(url(data.status_url), { cache: "no-store", signal: AbortSignal.timeout(data.timeout_ms) });
    const result = await response.json();
    if (![200, 503].includes(response.status) || !result.components) throw new Error();
    for (const component of ["llm", "http"]) {
      const element = document.getElementById(`${component}-state`);
      const ready = result.components[component] === "ok";
      element.dataset.state = ready ? "ok" : "error";
      element.textContent = t(ready ? "running" : "unavailable");
    }
    // The server supplies its local wall time, including the timezone label.
    document.getElementById("checked-at").textContent = `${result.checked_at} ${result.timezone}`;
  } catch {
    for (const component of ["llm", "http"]) {
      const element = document.getElementById(`${component}-state`);
      element.dataset.state = "error";
      element.textContent = t("disconnected");
    }
  } finally {
    checking = false;
    refresh.disabled = false;
  }
}
form.addEventListener("input", updateDirty);
form.addEventListener("change", updateDirty);
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy || !form.reportValidity()) return;
  const values = settings();
  setBusy(true);
  showFeedback(t("saving"));
  try {
    const result = await request(data.configuration_url, values);
    saved = JSON.stringify(values);
    document.getElementById("http-pending").hidden = !result.http_restart_required;
    showFeedback(result.message);
  } catch (error) {
    showFeedback(error.message, true);
  } finally {
    setBusy(false);
  }
});
restart.addEventListener("click", () => {
  if (!busy && !restart.disabled) dialog.showModal();
});
dialog.addEventListener("close", async () => {
  if (dialog.returnValue !== "restart" || busy) return;
  setBusy(true);
  showFeedback(t("restarting"));
  try {
    const result = await request(data.restart_url, {});
    showFeedback(result.message);
    await checkStatus();
  } catch (error) {
    showFeedback(error.message, true);
  } finally {
    setBusy(false);
  }
});
refresh.addEventListener("click", checkStatus);
fields.disabled = false;
updateDirty();
checkStatus();
setInterval(() => { if (!document.hidden) checkStatus(); }, data.refresh_ms);
