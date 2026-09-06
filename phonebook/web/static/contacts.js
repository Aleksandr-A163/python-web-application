(() => {
  const list = document.querySelector("#contactList");
  const search = document.querySelector("#contactSearch");
  const count = document.querySelector("#contactCount");
  const refresh = document.querySelector("#refreshContacts");
  if (!list || !search || !count || !refresh) return;

  let contacts = [];

  const initials = (name) => name.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();

  const render = () => {
    const query = search.value.trim().toLocaleLowerCase("ru");
    const visible = contacts.filter((contact) =>
      [contact.name, contact.phone, contact.comment].some((value) =>
        value.toLocaleLowerCase("ru").includes(query)
      )
    );

    count.textContent = `${visible.length} из ${contacts.length}`;
    list.replaceChildren();

    if (!visible.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = contacts.length ? "Ничего не найдено" : "В справочнике пока нет контактов";
      list.append(empty);
      return;
    }

    visible.forEach((contact, index) => {
      const row = document.createElement("article");
      row.className = "contact-row";

      const avatar = document.createElement("div");
      avatar.className = `avatar ${["avatar-blue", "avatar-violet", "avatar-green"][index % 3]}`;
      avatar.textContent = initials(contact.name);

      const identity = document.createElement("div");
      identity.className = "contact-name";
      const name = document.createElement("strong");
      name.textContent = contact.name;
      const id = document.createElement("small");
      id.textContent = `Контакт #${contact.id}`;
      identity.append(name, id);

      const phone = document.createElement("div");
      phone.className = "contact-phone";
      phone.textContent = contact.phone;

      const comment = document.createElement("div");
      comment.className = "contact-comment";
      comment.textContent = contact.comment || "Без комментария";

      row.append(avatar, identity, phone, comment);
      list.append(row);
    });
  };

  const load = async () => {
    refresh.disabled = true;
    count.textContent = "Загрузка…";
    try {
      const response = await fetch("/api/contacts/");
      if (!response.ok) throw new Error("API request failed");
      contacts = await response.json();
      render();
    } catch {
      list.innerHTML = '<div class="empty-state text-danger">Не удалось загрузить контакты</div>';
      count.textContent = "Ошибка";
    } finally {
      refresh.disabled = false;
    }
  };

  search.addEventListener("input", render);
  refresh.addEventListener("click", load);
  load();
})();
