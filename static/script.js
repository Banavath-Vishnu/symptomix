
  const chatBox = document.getElementById("chatBox");
  const chatForm = document.getElementById("chatForm");
  const userInput = document.getElementById("userInput");
  const mainContainer = document.getElementById("mainContainer");
  const header = document.getElementById("chatHeader");

  // Static chat ID for now (can be user-specific or session-based)
  const chatId = "user123";

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = userInput.value.trim();
    if (!msg) return;

    if (chatBox.classList.contains("hidden")) {
      chatBox.classList.remove("hidden");
      chatBox.classList.add("fade-in");
      mainContainer.classList.remove("justify-center", "items-center", "text-center");
      mainContainer.classList.add("items-start", "text-left");
      header.classList.add("mb-4");
    }

    const userMsgHTML = `
      <div class="flex justify-end items-start gap-3">
        <div class="bg-blue-600 text-white px-4 py-3 rounded-2xl max-w-sm shadow-md">${msg}</div>
        <img src="https://cdn-icons-png.flaticon.com/512/3177/3177440.png" class="w-8 h-8 rounded-full" alt="User">
      </div>`;
    chatBox.insertAdjacentHTML("beforeend", userMsgHTML);
    chatBox.scrollTop = chatBox.scrollHeight;
    userInput.value = "";

    const thinkingEl = document.createElement("div");
    thinkingEl.className = "flex items-start gap-3 animate-pulse";
    thinkingEl.innerHTML = `
      <img src="https://cdn2.iconfinder.com/data/icons/robot-29/100/doctor-robot-robot-medical-ai-doctor-nurse-stethoscope-256.png" class="w-8 h-8 rounded-full" alt="Bot">
      <div class="dot-flashing relative"></div>`;
    chatBox.appendChild(thinkingEl);
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
      const res = await fetch("/get", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ msg, chat_id: chatId })
      });

      const data = await res.json();
      chatBox.removeChild(thinkingEl);

      const botReplyHTML = `
        <div class="flex items-start gap-3">
          <img src="https://cdn2.iconfinder.com/data/icons/robot-29/100/doctor-robot-robot-medical-ai-doctor-nurse-stethoscope-256.png" class="w-8 h-8 rounded-full" alt="Bot">
          <div class="bg-gray-200 px-4 py-3 rounded-2xl max-w-sm shadow-md text-gray-900 prose prose-sm">${marked.parse(data.response)}</div>
        </div>`;
      chatBox.insertAdjacentHTML("beforeend", botReplyHTML);
      chatBox.scrollTop = chatBox.scrollHeight;

    } catch (err) {
      chatBox.removeChild(thinkingEl);
      console.error("Error:", err);

      const errorHTML = `
        <div class="flex items-start gap-3">
          <img src="https://cdn2.iconfinder.com/data/icons/robot-29/100/doctor-robot-robot-medical-ai-doctor-nurse-stethoscope-256.png" class="w-8 h-8 rounded-full" alt="Bot">
          <div class="bg-red-100 text-red-700 px-4 py-3 rounded-2xl max-w-sm shadow-md">
            Something went wrong. Please try again.
          </div>
        </div>`;
      chatBox.insertAdjacentHTML("beforeend", errorHTML);
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  });

