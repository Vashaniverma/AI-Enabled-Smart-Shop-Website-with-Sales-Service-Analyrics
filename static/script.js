// ========== Navbar Toggle ==========
const toggle = document.querySelector('.nav-toggle');
const links = document.querySelector('.nav-links');

if (toggle && links) {
  toggle.addEventListener('click', () => links.classList.toggle('show'));
}

const chatbotIcon = document.getElementById("chatbot-icon");
const chatbotBody = document.getElementById("chatbot-body");
const sendBtn = document.getElementById("chat-send");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");

// Toggle chat window
chatbotIcon.addEventListener("click", () => {
    if (chatbotBody.style.display === "flex") {
        chatbotBody.style.display = "none";
    } else {
        chatbotBody.style.display = "flex";
    }
});

// Function to add messages
function addMessage(message, sender) {
    const msgDiv = document.createElement("div");
    msgDiv.className = sender === "user" ? "user-msg" : "bot-msg";
    msgDiv.innerText = message;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight; // auto-scroll
}

// Send message
sendBtn.addEventListener("click", () => {
    const userMessage = chatInput.value.trim();
    if (!userMessage) return;

    addMessage(userMessage, "user"); // user message
    chatInput.value = "";

    // Send to backend
    fetch("/get_answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage })
    })
    .then(res => res.json())
    .then(data => {
        addMessage(data.answer, "bot"); // bot reply
    })
    .catch(err => {
        addMessage("Error connecting to server.", "bot");
        console.error(err);
    });
});

// Optional: send message on Enter key
chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendBtn.click();
});

// Optional: send message on Enter key
chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendBtn.click();
});

// ========== Footer Year ==========
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// ========== Products Filters ==========
const search = document.getElementById('search');
const category = document.getElementById('category');
const price = document.getElementById('price');
const grid = document.getElementById('productGrid');

function applyFilters() {
  if (!grid) return;
  const q = (search?.value || '').toLowerCase();
  const cat = category?.value || '';
  const pr = price?.value || '';

  [...grid.querySelectorAll('.product')].forEach(card => {
    const title = card.querySelector('h3').textContent.toLowerCase();
    const text = card.querySelector('p').textContent.toLowerCase();
    const cOk = !cat || card.dataset.category === cat;
    const pOk = !pr || card.dataset.price === pr;
    const qOk = !q || title.includes(q) || text.includes(q);
    card.style.display = cOk && pOk && qOk ? '' : 'none';
  });
}
[search, category, price].forEach(el => el && el.addEventListener('input', applyFilters));

// ========== Fake Form Handlers ==========
const serviceForm = document.getElementById('serviceForm');
if (serviceForm) {
  serviceForm.addEventListener('submit', e => {
    e.preventDefault();
    document.getElementById('serviceMsg').textContent =
      'Thank you! Your request has been received. We will confirm shortly.';
    serviceForm.reset();
  });
}

const contactForm = document.getElementById('contactForm');
if (contactForm) {
  contactForm.addEventListener('submit', e => {
    e.preventDefault();
    document.getElementById('contactMsg').textContent =
      'Message sent. We will get back to you soon!';
    contactForm.reset();
  });
}
