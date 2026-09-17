const API_URL = "/api/requests";

const main = document.querySelector(".main");
const listElements = Array.from(main.children);

document.addEventListener("DOMContentLoaded", start);

async function start() {
  main.addEventListener("click", handleClick);
  const filterForm = document.getElementById("filter-form");
  filterForm.addEventListener("input", handleFilterChange);
  filterForm.addEventListener("submit", handleFilterChange);
  filterForm.addEventListener("reset", handleFilterReset);

  try {
    await renderStudents();
  } catch (error) {
    alert(error.message);
  }
}

async function handleFilterChange(event) {
  event.preventDefault();

  try {
    await renderStudents();
  } catch (error) {
    alert(error.message);
  }
}

async function handleFilterReset(event) {
  event.preventDefault();

  const filterForm = document.getElementById("filter-form");
  filterForm.reset();

  try {
    await renderStudents();
  } catch (error) {
    alert(error.message);
  }
}

async function renderStudents() {
  const body = document.getElementById("students-table-body");
  const students = await getStudents();

  body.innerHTML = "";

  if (students.length === 0) {
    body.innerHTML = '<tr><td colspan="8">Студентов пока нет</td></tr>';
    return;
  }

  for (const student of students) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${escapeHtml(student.fullName)}</td>
      <td>${escapeHtml(student.group)}</td>
      <td>${escapeHtml(student.isuId)}</td>
      <td>№${escapeHtml(student.dormNumber)}</td>
      <td>${escapeHtml(student.room)}</td>
      <td><button type="button" class="button button--small" data-action="details" data-id="${student.id}">Подробнее</button></td>
      <td><button type="button" class="button button--small" data-action="edit" data-id="${student.id}">Редактировать</button></td>
      <td><button type="button" class="button button--small button--danger" data-action="delete" data-id="${student.id}">Удалить</button></td>
    `;
    body.appendChild(row);
  }
}

async function handleClick(event) {
  const element = event.target.closest("button");
  if (!element) return;

  const action = element.dataset.action;

  switch (action) {
    case "add":
      await showForm();
      break;

    case "edit":
      await showForm(Number(element.dataset.id));
      break;

    case "details":
      await showDetails(Number(element.dataset.id));
      break;

    case "delete":
      await removeStudent(Number(element.dataset.id));
      break;

    case "back":
      showList();
      await renderStudents();
      break;
  }
}

async function showForm(id) {
  const view = await loadTemplate("student-form.html");
  const form = view.querySelector("#student-form");

  if (id) {
    const student = await getStudentById(id);
    if (!student) return;

    view.querySelector("#form-title").textContent = "Редактировать студента";
    view.querySelector("#student-id").value = student.id;
    view.querySelector("#fullName").value = student.fullName;
    view.querySelector("#group").value = student.group;
    view.querySelector("#isuId").value = student.isuId;
    view.querySelector("#dormNumber").value = student.dormNumber;
    view.querySelector("#room").value = student.room;
    view.querySelector("#checkInDate").value = student.checkInDate;
    view.querySelector("#isForeigner").checked = student.isForeigner;
    view.querySelector("#notes").value = student.notes || "";
    view.querySelector("#student-preview").innerHTML = studentTableHtml(student);
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const student = {
      fullName: view.querySelector("#fullName").value.trim(),
      group: view.querySelector("#group").value.trim(),
      isuId: view.querySelector("#isuId").value.trim(),
      dormNumber: Number(view.querySelector("#dormNumber").value),
      room: Number(view.querySelector("#room").value),
      checkInDate: view.querySelector("#checkInDate").value,
      isForeigner: view.querySelector("#isForeigner").checked,
      notes: view.querySelector("#notes").value.trim(),
    };

    try {
      if (id) {
        await updateStudent(id, student);
      } else {
        await addStudent(student);
      }
    } catch (error) {
      view.querySelector("#form-errors").textContent = error.message;
      return;
    }

    showList();
    await renderStudents();
  });
}

async function showDetails(id) {
  const student = await getStudentById(id);
  if (!student) return;

  const view = await loadTemplate("student-details.html");
  const details = view.querySelector("#student-details");

  details.innerHTML = studentTableHtml(student);
}

async function removeStudent(id) {
  const student = await getStudentById(id);
  if (!student) return;

  if (confirm(`Удалить студента ${student.fullName}?`)) {
    try {
      await deleteStudent(id);
    } catch (error) {
      alert(error.message);
      return;
    }

    await renderStudents();
  }
}

async function getStudents() {
  const params = new URLSearchParams();

  const fullName = document.getElementById("filter-fullName").value.trim();
  const group = document.getElementById("filter-group").value.trim();
  const isuId = document.getElementById("filter-isuId").value.trim();
  const dormitory = document.getElementById("filter-dormitory").value;
  const room = document.getElementById("filter-room").value;
  const checkInDate = document.getElementById("filter-checkInDate").value;
  const isForeigner = document.getElementById("filter-isForeigner").checked;

  if (fullName) params.set("fullName", fullName);
  if (group) params.set("group", group);
  if (isuId) params.set("isuId", isuId);
  if (dormitory) params.set("dormitory", dormitory);
  if (room) params.set("room", room);
  if (checkInDate) params.set("checkInDate", checkInDate);
  if (isForeigner) params.set("isForeigner", "true");

  const query = params.toString();
  const response = await fetch(query ? `${API_URL}?${query}` : API_URL);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error);
  }

  return data;
}

async function getStudentById(id) {
  const response = await fetch(`${API_URL}/${id}`);

  if (response.status === 404) return null;

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error);
  }

  return data;
}

async function addStudent(student) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(student),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error);
  }

  return data;
}

async function updateStudent(id, student) {
  const response = await fetch(`${API_URL}/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(student),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error);
  }

  return data;
}

async function deleteStudent(id) {
  const response = await fetch(`${API_URL}/${id}`, { method: "DELETE" });

  if (!response.ok) {
    throw new Error("Не удалось удалить студента");
  }
}

async function loadTemplate(fileName) {
  const response = await fetch(fileName);
  if (!response.ok) {
    throw new Error("Не удалось загрузить шаблон");
  }

  listElements.forEach((element) => {
    element.hidden = true;
  });

  const oldView = document.getElementById("dynamic-view");
  if (oldView) oldView.remove();

  const view = document.createElement("div");
  view.id = "dynamic-view";
  view.innerHTML = await response.text();
  main.appendChild(view);
  return view;
}

function showList() {
  document.getElementById("dynamic-view")?.remove();
  listElements.forEach((element) => {
    element.hidden = false;
  });
}

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = String(value);
  return element.innerHTML;
}

function studentTableHtml(student) {
  return `
    <table>
      <tbody>
        <tr><td>ФИО студента</td><td>${escapeHtml(student.fullName)}</td></tr>
        <tr><td>Группа</td><td>${escapeHtml(student.group)}</td></tr>
        <tr><td>ИСУ ID</td><td>${escapeHtml(student.isuId)}</td></tr>
        <tr><td>Номер общежития</td><td>${escapeHtml(student.dormNumber)}</td></tr>
        <tr><td>Комната</td><td>${escapeHtml(student.room)}</td></tr>
        <tr><td>Срок заселения</td><td>${escapeHtml(student.checkInDate)}</td></tr>
        <tr><td>Иностранец</td><td>${student.isForeigner ? "Да" : "Нет"}</td></tr>
        <tr><td>Заметки</td><td>${escapeHtml(student.notes || "Нет")}</td></tr>
      </tbody>
    </table>
  `;
}
