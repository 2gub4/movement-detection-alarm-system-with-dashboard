document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const toggleBtn = document.getElementById("themeToggle");
  const icon = toggleBtn.querySelector("i");

  // ustawienia startowe
  if (localStorage.getItem("theme") === "light") {
    body.classList.remove("dark");
    body.classList.add("light");
    icon.classList.replace("bi-moon", "bi-sun");
  } else {
    body.classList.remove("light");
    body.classList.add("dark");
    icon.classList.replace("bi-sun", "bi-moon");
  }

  // przełącznik
  toggleBtn.addEventListener("click", () => {
    if (body.classList.contains("dark")) {
      body.classList.remove("dark");
      body.classList.add("light");
      localStorage.setItem("theme", "light");
      icon.classList.replace("bi-moon", "bi-sun");
    } else {
      body.classList.remove("light");
      body.classList.add("dark");
      localStorage.setItem("theme", "dark");
      icon.classList.replace("bi-sun", "bi-moon");
    }
  });
});
