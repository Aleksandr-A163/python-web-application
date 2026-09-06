(() => {
  const root = document.documentElement;
  const toggle = document.querySelector("#themeToggle");
  const savedTheme = localStorage.getItem("phonebook-theme");

  if (savedTheme === "dark") root.dataset.theme = "dark";

  toggle?.addEventListener("click", () => {
    const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = nextTheme;
    localStorage.setItem("phonebook-theme", nextTheme);
  });
})();
