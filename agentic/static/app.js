const area = document.getElementById("chatArea");
const composer = document.getElementById("composer");
const input = document.getElementById("message");
const sendBtn = document.getElementById("sendBtn");
const welcome = document.getElementById("welcome");
const newChat = document.getElementById("newChat");
const clearChat = document.getElementById("clearChat");
const STORAGE_KEY = "datazoic_ai_v42_conversation";
const HISTORY_KEY = "datazoic_ai_v42_history";
let messages = loadMessages();

function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c])); }
function formatText(s) { return escapeHtml(s).replace(/\n/g, "<br>"); }
function toolLabel(details) {
  if (!details) return null;
  if (details.type === "action_result") return details.tool.replaceAll("_", " ");
  if (details.source === "RAG") return "knowledge base";
  if (details.source === "SYSTEM_SEARCH") return "system search";
  if (details.type === "knowledge_context") return "knowledge + Gemini";
  return null;
}
function appendMessage(role, text, details=null, loading=false, save=true) {
  if (welcome) welcome.style.display = "none";
  let wrap = document.getElementById("messages");
  if (!wrap) { wrap = document.createElement("div"); wrap.id="messages"; wrap.className="messages"; area.appendChild(wrap); }
  const el = document.createElement("div"); el.className = `msg ${role}`;
  const avatar = role === "assistant" ? "✦" : "Y";
  const time = new Date().toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"});
  let card = ""; const label = toolLabel(details);
  if (label && !loading) {
    let extra = "";
    if (details.type === "action_result" && details.result) extra = `<div class="details">${escapeHtml(JSON.stringify(details.result, null, 2))}</div>`;
    else if (details.source === "SYSTEM_SEARCH" && details.results?.length) extra = `<div class="details">${details.results.length} record(s) returned</div>`;
    else if (details.type === "knowledge_context" && details.results?.length) extra = `<div class="details">${details.results.length} knowledge item(s supplied to Gemini)</div>`;
    card = `<div class="tool-card"><div class="tool-head"><span>${escapeHtml(label)}</span><span class="pill">completed</span></div>${extra}</div>`;
  }
  const body = loading ? `<span class="typing"><i></i><i></i><i></i></span>` : formatText(text);
  el.innerHTML = `<div class="avatar">${avatar}</div><div><div class="bubble">${body}</div><div class="meta">${time}</div>${card}</div>`;
  wrap.appendChild(el); area.scrollTo({top: area.scrollHeight, behavior:"smooth"});
  if (save && !loading) persistMessage(role, text, details);
  return el;
}
async function send(message) {
  const text = message.trim(); if (!text || sendBtn.disabled) return;
  input.value = ""; input.style.height = "auto";
  appendMessage("user", text);
  const loading = appendMessage("assistant", "", null, true); sendBtn.disabled = true;
  try {
    const history = messages.filter(x => x.role === "user" || x.role === "model").slice(-12);
    const res = await fetch("/chat", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({message:text, history})});
    if (!res.ok) throw new Error(`Request failed (${res.status})`);
    const data = await res.json(); loading.remove(); appendMessage("assistant", data.message || "I could not process that request.", data.details || null);
  } catch (err) { loading.remove(); appendMessage("assistant", "I couldn't reach the Datazoic AI service. Please check that the server is running and try again."); }
  finally { sendBtn.disabled = false; input.focus(); }
}
function persistMessage(role, content, details) {
  const modelRole = role === "assistant" ? "model" : "user";
  messages.push({role:modelRole, content, details, at:Date.now()});
  messages = messages.slice(-30); localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  if (role === "user") localStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
}
function loadMessages() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch { return []; } }
function restore() {
  const wrap = document.getElementById("messages"); if (wrap) wrap.remove();
  if (!messages.length) { if (welcome) welcome.style.display = ""; return; }
  if (welcome) welcome.style.display = "none";
  messages.forEach(x => appendMessage(x.role === "model" ? "assistant" : "user", x.content, x.details, false, false));
}
function reset() { messages = []; localStorage.removeItem(STORAGE_KEY); localStorage.removeItem(HISTORY_KEY); const m=document.getElementById("messages"); if(m)m.remove(); if(welcome)welcome.style.display=""; input.focus(); }
composer.addEventListener("submit", e => { e.preventDefault(); send(input.value); });
input.addEventListener("input", () => { input.style.height="auto"; input.style.height=Math.min(input.scrollHeight,120)+"px"; });
input.addEventListener("keydown", e => { if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();composer.requestSubmit();} });
document.querySelectorAll(".suggestion").forEach(btn => btn.addEventListener("click", () => send(btn.dataset.prompt)));
newChat.addEventListener("click", reset); clearChat.addEventListener("click", reset);
window.addEventListener("pageshow", restore); window.addEventListener("popstate", restore);
restore(); input.focus();
