const chatMessages = document.getElementById("chat-messages");
const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");
const riskStatus = document.getElementById("risk-status");

let chatHistory = [
  {
    role: "assistant",
    content: "I'm here. We can go slow. Tell me what is happening, and I will meet you where you are.",
  },
];
let isProcessing = false;

userInput.addEventListener("input", function () {
  this.style.height = "auto";
  this.style.height = `${this.scrollHeight}px`;
});

userInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

sendButton.addEventListener("click", sendMessage);

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message || isProcessing) return;

  isProcessing = true;
  userInput.disabled = true;
  sendButton.disabled = true;

  addMessageToChat("user", message);
  chatHistory.push({ role: "user", content: message });
  userInput.value = "";
  userInput.style.height = "auto";

  const assistantMessageEl = addMessageToChat("assistant", "");
  const assistantTextEl = assistantMessageEl.querySelector("p");

  let responseText = "";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: chatHistory }),
    });

    if (!response.ok || !response.body) {
      throw new Error("Failed to get response");
    }

    updateRiskStatus(response.headers.get("x-rrt-risk-level"));

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        const parsed = consumeSseEvents(`${buffer}\n\n`);
        responseText = appendEvents(parsed.events, responseText, assistantTextEl);
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const parsed = consumeSseEvents(buffer);
      buffer = parsed.buffer;
      responseText = appendEvents(parsed.events, responseText, assistantTextEl);
    }

  } catch (error) {
    console.error("Error:", error);
    if (responseText) {
      assistantTextEl.textContent = `${responseText}\n\nConnection dropped. Take one breath with me, then try again.`;
    } else {
      assistantTextEl.textContent = "I hit a connection error. Take one breath with me, then try again.";
    }
  } finally {
    const finalText = assistantTextEl.textContent.trim();
    if (finalText) {
      chatHistory.push({ role: "assistant", content: finalText });
    }
    isProcessing = false;
    userInput.disabled = false;
    sendButton.disabled = false;
    userInput.focus();
  }
}

function addMessageToChat(role, content) {
  const messageEl = document.createElement("div");
  messageEl.className = `message ${role}-message`;
  const paragraph = document.createElement("p");
  paragraph.textContent = content;
  messageEl.appendChild(paragraph);
  chatMessages.appendChild(messageEl);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return messageEl;
}

function appendEvents(events, responseText, assistantTextEl) {
  let nextText = responseText;
  for (const data of events) {
    if (data === "[DONE]") break;
    try {
      const jsonData = JSON.parse(data);
      const content = jsonData.response || jsonData.choices?.[0]?.delta?.content || "";
      if (content) {
        nextText += content;
        assistantTextEl.textContent = nextText;
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    } catch (error) {
      console.error("Error parsing SSE data:", error, data);
    }
  }
  return nextText;
}

function consumeSseEvents(buffer) {
  let normalized = buffer.replace(/\r/g, "");
  const events = [];
  let eventEndIndex;

  while ((eventEndIndex = normalized.indexOf("\n\n")) !== -1) {
    const rawEvent = normalized.slice(0, eventEndIndex);
    normalized = normalized.slice(eventEndIndex + 2);

    const dataLines = rawEvent
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice("data:".length).trimStart());

    if (dataLines.length > 0) {
      events.push(dataLines.join("\n"));
    }
  }

  return { events, buffer: normalized };
}

function updateRiskStatus(level) {
  const safeLevel = level || "stable";
  riskStatus.textContent = `local pre-check: ${safeLevel}`;
  riskStatus.classList.toggle("critical", safeLevel === "critical");
}
