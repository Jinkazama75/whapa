document.addEventListener("DOMContentLoaded", () => {
  const statusEl = document.getElementById("status");
  const tokenPreviewEl = document.getElementById("tokenPreview");
  const btnCopy = document.getElementById("btnCopy");
  let foundToken = "";

  const cookieApi = (typeof browser !== "undefined" && browser.cookies) ? browser.cookies : chrome.cookies;

  function checkCookie(url) {
    return new Promise((resolve) => {
      try {
        const res = cookieApi.get({ url: url, name: "oauth_token" }, (cookie) => {
          resolve(cookie ? cookie.value : null);
        });
        if (res && typeof res.then === "function") {
          res.then((c) => resolve(c ? c.value : null)).catch(() => resolve(null));
        }
      } catch (e) {
        resolve(null);
      }
    });
  }

  async function retrieveToken() {
    // Prova prima accounts.google.com, poi google.com
    let val = await checkCookie("https://accounts.google.com");
    if (!val) {
      val = await checkCookie("https://google.com");
    }

    if (val && val.trim().length > 0) {
      foundToken = val.trim();
      statusEl.textContent = "✅ Token trovato con successo!";
      statusEl.style.color = "#25D366";
      tokenPreviewEl.textContent = foundToken;
      tokenPreviewEl.style.display = "block";
      btnCopy.disabled = false;
      btnCopy.textContent = "📋 Copia Token";
    } else {
      statusEl.textContent = "⚠️ Token non trovato. Assicurati di aver aperto la pagina accounts.google.com/EmbeddedSetup ed effettuato l'accesso.";
      statusEl.style.color = "#FFA726";
      tokenPreviewEl.style.display = "none";
      btnCopy.disabled = true;
      btnCopy.textContent = "In attesa di login...";
    }
  }

  btnCopy.addEventListener("click", () => {
    if (!foundToken) return;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(foundToken).then(() => {
        onCopied();
      }).catch(() => {
        fallbackCopy(foundToken);
      });
    } else {
      fallbackCopy(foundToken);
    }
  });

  function fallbackCopy(text) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
      onCopied();
    } catch (e) {
      alert("Impossibile copiare: copia manualmente il testo visibile.");
    }
    document.body.removeChild(ta);
  }

  function onCopied() {
    btnCopy.textContent = "✅ Copiato negli Appunti!";
    btnCopy.style.background = "#1EBE5D";
    setTimeout(() => {
      btnCopy.textContent = "📋 Copia Token";
      btnCopy.style.background = "#25D366";
    }, 2000);
  }

  retrieveToken();
});
