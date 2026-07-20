const API_URL = "http://127.0.0.1:8000/scan";

async function scanCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const url = tab.url;

  document.getElementById("url-display").textContent = url;

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url }),
    });

    const data = await response.json();
    displayResult(data);
  } catch (error) {
    document.getElementById("loading").textContent =
      "Could not reach PhishGuard API. Is the server running on localhost:8000?";
  }
}

function displayResult(data) {
  document.getElementById("loading").style.display = "none";
  document.getElementById("result").style.display = "block";

  const scoreBox = document.getElementById("score-box");
  const isRisky = data.verdict === "phishing";

  scoreBox.className = isRisky ? "risky" : "safe";
  document.getElementById("score-number").textContent = data.score;
  document.getElementById("verdict").textContent = data.verdict;

  const reasonsList = document.getElementById("reasons");
  reasonsList.innerHTML = "";
  data.top_reasons.forEach((reason) => {
    const li = document.createElement("li");
    li.textContent = reason;
    reasonsList.appendChild(li);
  });
}

scanCurrentTab();